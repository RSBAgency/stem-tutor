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
