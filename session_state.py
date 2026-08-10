
STAGE_ORDER = ["diagnostic","question_loop","consolidation"]

def create_session_state(problem_text, answer, target_concept):
    #build a fresh tutoring sesssion with memory
    return {
        "stage": "diagnostic",
        "problem": {
            "text": problem_text,
            "locked_answer": answer,
            "target_concept": target_concept,
        },
        "plan": {
            "gap_identified": None,
            "misconceptions": [],
            "funnel_steps": [],
        },
        "current_step_index": 0,
        "current_rung": 5,
        "wrong_answer_count": 0,
        "impatience_strikes": 0,
        "transfer_check": {
            "attempted": False,
            "passed": None,
        },
        "log": [],
    }
def update_state(state, turn, first_turn):
    #updates the state dictionary based on the structured fields the model just returned
    if not first_turn and turn.gradable:
        if turn.answer_correct:
            state["wrong_answer_count"] = 0
        else:
            state["wrong_answer_count"] += 1

    if not first_turn and turn.impatience_demand:
            state["impatience_strikes"] += 1

    #advance to next stage when model signals this one is complete
    if not first_turn and turn.stage_complete:
        current_index = STAGE_ORDER.index(state["stage"])
        if current_index < len(STAGE_ORDER) - 1:
            state["stage"] = STAGE_ORDER[current_index + 1]

            #fresh stage
            state["wrong_answer_count"] = 0

    state["log"].append({
        "reply_text": turn.reply_text,
        "gradable": turn.gradable,
        "answer_correct": None if first_turn else turn.answer_correct,
        "impatience_demand": turn.impatience_demand,
    })

    return state

def build_instruction(state):
    #translate the current state in instructions for the model
    #current stage instead of empty
    lines = [f"Current stage: {state['stage']}."]

    #behavior instruction in diagnostic stage
    if state["stage"] == "diagnostic":
        lines.append(
            "You are still in the diagnostic stage. Ask about the "
            "student's prior knowledge of this topic, do not yet ask "
            "them to solve any part of the actual problem. Once you have "
            "a good sense of what they know, set stage_complete to true "
            "and your NEXT reply should ask the first real question"
        )

    elif state["stage"] == "question_loop":
        lines.append(
            "You are in the question loop. Only set stage_complete to true "
            "once the student has correctly found BOTH x and y and you have "
            "confirmed both values with them, not after a single correct "
            "sub-step. If the full solution, or both values, has not yet been reached "
            "and confirmed, stage_complete MUST be false, even if "
            "this individual answer was correct. "
        )

    wc = state["wrong_answer_count"]
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

    if len(lines) == 1:
        return None

    return "Internal state reminder ( do not mention this internal note or reasoning to student): " + " ".join(lines)
