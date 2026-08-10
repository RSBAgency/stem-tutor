import os
from openai import OpenAI
from tutor_prompt import SYSTEM_PROMPT
from tutor_response import TutorTurn
from session_state import create_session_state, update_state, build_instruction

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

state = create_session_state(
    problem_text="5x + 3y = 36 and x - y = 4",
    answer={"x": 6, "y": 2},
    target_concept="solving systems of linear equations by substitution",
)

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

print("Tutor test session. Type 'quit' to stop. \n")

messages.append({"role": "user", "content": "I need help solving 5x + 3y = 36 and x - y = 4"})

first_turn = True

while True:
    instruction = build_instruction(state)
    call_messages = messages if instruction is None else messages + [
        {"role": "system", "content": instruction}
    ]

    completion = client.chat.completions.parse(
        model="gpt-5-mini",
        messages=call_messages,
        response_format=TutorTurn,
    )

    turn = completion.choices[0].message.parsed

    state = update_state(state, turn, first_turn)
    first_turn = False

    print(f"Tutor: {turn.reply_text}\n")
    print(f"[state] stage={state['stage']} wrong_answer_count={state['wrong_answer_count']} impatience_strikes={state['impatience_strikes']} "
          f"(gradable={turn.gradable}, answer_correct={turn.answer_correct}, stage_complete={turn.stage_complete})\n")

    messages.append({"role": "assistant", "content": turn.reply_text})

    user_input = input("You: ")
    if user_input.strip().lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})