# Three teaching stages in a fixed order
# does not skip ahead or go backwards, cemented learning for the student

STAGE_ORDER = ["diagnostic", "question_loop", "completion", "transfer_check"]


def create_session_state(problem_text, answer, target_concept):
    # build a fresh tutoring session with memory
    # only called once at the beginning stage of the conversation
    return {
        "stage": "diagnostic",
        "problem": {
            "text": problem_text,
            "locked_answer": answer,
            "target_concept": target_concept,
        },

        # reserved feature
        "plan": {
            "gap_identified": None,
            "misconceptions": [],
            "funnel_steps": [],
        },
        "current_step_index": 0,
        "current_rung": 5,

        # how many times the student has gotten the current stage question wrong
        "wrong_answer_count": 0,

        # how many times the student has demanded the answer
        "impatience_strikes": 0,

        # how many times a student has completed a walkthrough that was unaccepted
        "completion_attempts": 0,

        # true once session is finished and reach last stage
        # without this completion will loop
        "session_complete": False,

        # holds transfer problem once generated
        "transfer_problem": {
            "text": None,
            "locked_answer": None,
        },

        # attempted is true on gradable answers
        # passed is whether answer was correct
        "transfer_check": {
            "attempted": False,
            "passed": None,
        },
        # a running record of every turn
        "log": [],
    }


def update_state(state, turn, first_turn):
    # updates the state dictionary based on the structured fields the model just returned
    # tracks the students struggle, and only mark wrong answers to gradable questions
    if not first_turn and turn.gradable:
        if turn.answer_correct:

            # reset the wrong answer count
            state["wrong_answer_count"] = 0
        else:
            # count wrong answer
            state["wrong_answer_count"] += 1

    if not first_turn and turn.impatience_demand:
        state["impatience_strikes"] += 1

    if not first_turn and state["stage"] == "completion":
        if turn.stage_complete:
            state["completion_attempts"] = 0
        else:
            state["completion_attempts"] += 1

    # updates attempted or passed by last given answer
    if not first_turn and state["stage"] == "transfer_check" and turn.gradable:
        state["transfer_check"]["attempted"] = True
        state["transfer_check"]["passed"] = turn.answer_correct

    # stops final asking loop
    if not first_turn and turn.stage_complete and state["stage"] == STAGE_ORDER[-1]:
        state["session_complete"] = True

    # advance to next stage when model signals this one is complete
    if not first_turn and turn.stage_complete:
        current_index = STAGE_ORDER.index(state["stage"])
        if current_index < len(STAGE_ORDER) - 1:
            state["stage"] = STAGE_ORDER[current_index + 1]

            # fresh stage
            state["wrong_answer_count"] = 0
    # logging
    state["log"].append({
        "reply_text": turn.reply_text,
        "gradable": turn.gradable,
        "answer_correct": None if first_turn else turn.answer_correct,
        "impatience_demand": turn.impatience_demand,
    })

    return state


def build_instruction(state):

    # translate the current state into instructions for the model, instead or rereading the conversation in whole
    # current stage instead of empty
    lines = [f"Current stage: {state['stage']}."]
    # inject the verified answer directly every turn
    # testing fix, avoid AI changing the answer in the middle of a conversation
    lines.append(
        f"The problem is: {state['problem']['text']}. The verified correct "
        f"answer is: {state['problem']['locked_answer']}. Use this exact "
        f"answer to judge whether the student's response are correct - do "
        f"not re-drive the answer yourself."
    )

    # self check behavior instruction in diagnostic stage
    if state["stage"] == "diagnostic":
        lines.append(
            "You are still in the diagnostic stage. Ask about the "
            "student's prior knowledge of this topic, do not yet ask "
            "them to solve any part of the actual problem. Once you have "
            "a good sense of what they know, set stage_complete to true "
            "and your NEXT reply should ask the first real question"
        )

    elif state["stage"] == "question_loop":
        # testing fix, a more specified version broke after the system was tested on quadratics
        # generalized wording is better suited for the question loop instead of structured return shapes
        lines.append(
            "You are in the question loop. Only set stage_complete to true "
            "once the student has found and you have confirmed the COMPLETE "
            "final answer to the problem, every value the problem asks for "
            "(for example: both x and y in a system, or all roots of a quadratic, "
            "or the single value in a linear equation), not after a single correct "
            "sub step. If any part of the full answer is still missing or unconfirmed "
            "stage_complete MUST be false, even if this individual answer was correct. "
        )

    elif state["stage"] == "completion":
        # testing fix, the AI would say the problem was complete when the student did not solve the problem
        # student must produce full reasoning for themselves
        # testing fix: completion tiers added for partial completion - registering progress

        if state["session_complete"]:
            lines.append(
                "The student has already fully completed this problem, "
                "including a correct walkthrough. Do NOT ask them to "
                "walk through the solution again or re-check it. "
                "Respond naturally to whatever they say now or offer a new problem, "
                "answer a question, or simply acknowledge them. "
            )
        else:
            attempts = state["completion_attempts"]

            if attempts == 0:  # first attempt walkthrough
                lines.append(
                    "You are in the completion stage. Your job is to ask "
                    "the STUDENT to walk through the entire solution path themselves,"
                    "from the first step to the final answer, in their own words. "
                    "Do not summarize it for them and call that completion, you must "
                    "ask them to do it. Only set stage_complete to true once "
                    "the student has actually produced a full walkthrough covering "
                    "every step, not just confirmed the final numbers."
                )
            elif attempts == 1:  # narrow missing information
                lines.append(
                    "The student has already attempted a full walkthrough once "
                    "and it was missing something. Do NOT repeat the entire "
                    "multi-part request again. Acknowledge specifically what they "
                    "already got right then ask ONLY about the one specific piece that "
                    "that is still missing or wrong. Name that piece directly. If your "
                    "reply repeats the full checklist again instead of narrowing to the "
                    "one missing piece, you have failed this instruction."
                )
            else:  # recognize effort
                lines.append(
                    "The student has now made multiple walkthrough attempts. If their"
                    " explanation covers the correct operation and reaches the correct"
                    "final answer, accept it as sufficient and set stage_complete to true, "
                    "even if a minor detail, like a formal name of property, was missing or"
                    "imperfect. Do NOT ask for a full walkthrough again. If your reply requests "
                    "an entire multipart explanation again instead of either accepting it "
                    "or naming just one remaining gap, you have failed this instruction. "
                    "If the student still has not attempted the core reasoning at all "
                    "briefly state the missing piece yourself, confirm they understand, "
                    "and set stage_complete to true."

                )
    # transfer check stage
    # separate from question loop and checks a new generated problem
    elif state["stage"] == "transfer_check":
        if state["session_complete"]:
            lines.append(
                "This session has finished, including the transfer check or skipped "
                "because transfer problem could not be verified. Do NOT ask another "
                "question or request more work. Respond naturally and acknowledge the "
                "student, offer a new problem, or wrap up the conversation."

            )
        else:
            tp = state["transfer_problem"]
            # reset to 0 wrong answers
            wc = state["wrong_answer_count"]

            lines.append(
                f"TRANSFER CHECK: for this stage ONLY, the active problem the "
                f"student should solve is: {tp['text']}. Its verified answer is: "
                f"{tp['locked_answer']}. Use THIS answer, not the original "
                f"problem's answer mentioned above, to judge correctness here. "
                f"If your reply_text judges the student against the original "
                f"problem's answer instead of this one, you have failed this instruction."

            )

            if wc == 0:
                lines.append(
                    "Present this transfer problem to the student and ask them "
                    "to solve it with MINIMAL guidance, do not walk them through "
                    "the full ladder of questions like in the main question loop. "
                    "If they solve it correctly, briefly affirm and set stage_complete "
                    "to true. If they decline or say they are done instead of attempting "
                    "it, accep that gracefully and set stage_complete to true. Do not "
                    "pressure the student to attempt it."
                )
            elif wc == 1:
                lines.append(
                    "The student already got this transfer problem wrong once. Give them "
                    "ONE hint pointing at the underlying concept, not the answer or specific "
                    "steps, and let them try once more. This is their FINAL attempt: after "
                    "their next answer set stage_complete to true regardless of whether it was "
                    "correct, do not ask again for a third time. If your reply asks for another "
                    "attempt after this FINAL one, you have failed this instruction."
                )
            else:
                lines.append(
                    "The student has now gotten this transfer problem wrong two or more times "
                    "including after already receiving a hint. Your reply_text for this turn "
                    "MUST NOT ask them to try again. Acknowledge their effort, briefly state "
                    "the correct answer, and you MUST set stage_complete to true on this "
                    "turn. NO exceptions. If stage_complete is not true, or if your repl_text "
                    "asks for another attempt, you have failed this instruction."
                )

    # descent rule only applies to main question loop
    if state["stage"] != "transfer_check":
        wc = state["wrong_answer_count"]
        # descent rule
        # change of tactic and restructuring of question for better student understanding
        # testing fix, the AI usually defaulted to giving a more obvious hint within the same question
        if wc == 1:
            lines.append(
                "The student has gotten the current step wrong once already. "
                "If their next answer is wrong again, this will be their 2nd "
                "wrong attempt: you must acknowledge you're changing approach "
                "and ask a NEW, differently structured question, not the same "
                "question with a bigger hint. "
            )
        elif wc >= 2:
            lines.append(
                "The student has gotten the current step wrong two or more "
                "times already. Your reply_text for this turn MUST be direct "
                "teaching, not a question: explain the current single step in "
                "full, state the operation and the result. Then confirm "
                "understanding, then move to the NEXT step. Do not end your "
                "reply_text with a question asking the student to solve this "
                "same step again, if your reply asks the student to solve or "
                "fill in this step themselves, you have failed this instruction "
                "and must rewrite it as direct teaching instead"
            )

    strikes = state["impatience_strikes"]
    # impatience strikes, 3 strikes
    if strikes == 1:
        lines.append(
            "The student has already demanded the final answer once. If "
            "they demand it again, you must explicitly acknowledge this is "
            "a repeated request before holding firm. "
        )
    elif strikes >= 2:
        lines.append(
            "The student has demanded the final answer two or more times "
            "already. If they demand it again, do NOT refuse again "
            "directly teach the current single step instead, then hand the "
            "next question back to them. "
        )

    # return none if the current stage line and answer line exist
    # avoid extra instructions being added
    if len(lines) == 1:
        return None

    return "Internal state reminder ( do not mention this internal note or reasoning to student): " + " ".join(lines)
