import os
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

from tutor_prompt import SYSTEM_PROMPT
from tutor_response import TutorTurn
from session_state import create_session_state, update_state, build_instruction
from problem_solver import solve_problem
from session_history import save_session, load_all_sessions

app = Flask(__name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# chat interface
# Flask convention
@app.route("/")
def home():
    return render_template("index.html")


# single session storage for local use
session = {
    "state": None,
    "messages": None,
    "first_turn": True,

}

# student submits a new problem - entry point
@app.route("/api/start", methods=["POST"])
def start_session():
    data = request.get_json()
    problem_text = data.get("problem_text", "").strip()

    # solution is solved before tutoring
    solution = solve_problem(client, problem_text)

    # reject unsolvable problems or problems outside the three types
    if not solution.solvable:
        return jsonify({
            "ok": False,
            "error": "I can only help with single linear equations, systems of two linear equations, "
                     "or basic quadratic right now."
        })
    # build state dict
    # verified answer + target concept
    state = create_session_state(
        problem_text=problem_text,
        answer=solution.locked_answer,
        target_concept=solution.target_concept,
    )

    # conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": f"I need help solving {problem_text}"})

    session["state"] = state
    session["messages"] = messages
    session["first_turn"] = True

    # tutor's opening question
    tutor_reply, session["state"] = _get_tutor_reply(state, messages, first_turn=True)
    session["first_turn"] = False

    return jsonify({"ok": True, "reply": tutor_reply})


@app.route("/api/message", methods=["POST"])
def continue_session():
    # tutoring loop
    data = request.get_json()
    user_message = data.get("message", "").strip()

    state = session["state"]
    messages = session["messages"]

    messages.append({"role": "user", "content": user_message})

    # stage = UI elements indicator
    tutor_reply, state = _get_tutor_reply(state, messages, first_turn=False)
    session["state"] = state
    return jsonify({"ok": True, "reply": tutor_reply, "stage": state["stage"]})


# New Problem: saving previous conversation before clearing
@app.route("/api/reset", methods=["POST"])
def reset_session():
    save_session(session["state"], session["messages"])

    session["state"] = None
    session["messages"] = None
    session["first_turn"] = True
    return jsonify({"ok": True})


# saved conversations: Past Problems
@app.route("/api/history", methods=["GET"])
def get_history():
    sessions = load_all_sessions()
    return jsonify({"ok": True, "sessions": sessions})


# tutoring model for opening question and messages exchanged
# current stage is changed into instructions
def _get_tutor_reply(state, messages, first_turn):
    instruction = build_instruction(state)

    # temporary list added for one clear instruction returned
    call_messages = messages if instruction is None else messages + [
        {"role": "system", "content": instruction}
    ]

    completion = client.chat.completions.parse(
        model="gpt-5-mini",
        messages=call_messages,
        response_format=TutorTurn,
    )

    # permanent conversation history
    turn = completion.choices[0].message.parsed
    state = update_state(state, turn, first_turn)
    messages.append({"role": "assistant", "content": turn.reply_text})

    return turn.reply_text, state


# error handling for testing
if __name__ == "__main__":
    app.run(debug=True, port=5000)
