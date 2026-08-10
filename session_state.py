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

    state["log"].append({
        "reply_text": turn.reply_text,
        "gradable": turn.gradable,
        "answer_correct": None if first_turn else turn.answer_correct,
        "impatience_demand": turn.impatience_demand,
    })

    return state

def build_instruction(state):
    #translate the current state in instructions for the model
    lines = []

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
    if not lines:
        return None

    return "Internal state reminder ( do not mention this internal note or reasoning to student): " + " ".join(lines)
