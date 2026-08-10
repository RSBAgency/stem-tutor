import os
from openai import OpenAI
from tutor_prompt import SYSTEM_PROMPT
from tutor_response import TutorTurn
from session_state import create_session_state, update_state, build_instruction
from problem_solver import solve_problem

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

print("Tutor test session. Type 'quit' to stop. \n")

problem_text = input("What algebra problem do you need help with? ")

solution = solve_problem(client, problem_text)

if not solution.solvable:
    print("\nSorry, I can only help with single linear equations, systems of "
          "two linear equations, or basic quadratics right now. Please try a "
          "different problem.")
    exit()


print(f"\n[debug] Locked answer: {solution.locked_answer} "
      f"(concept: {solution.target_concept})\n")

state = create_session_state(
    problem_text=problem_text,
    answer=solution.locked_answer,
    target_concept=solution.target_concept,
)

messages = [{"role": "system", "content": SYSTEM_PROMPT}]
messages.append({"role": "user", "content": f"I need help solving {problem_text}"})

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
    print(f"[state] stage={state['stage']} wrong_answer_count={state['wrong_answer_count']} "
          f"impatience_strikes={state['impatience_strikes']} (gradable={turn.gradable}, "
          f"answer_correct={turn.answer_correct}, stage_complete={turn.stage_complete})\n")

    messages.append({"role": "assistant", "content": turn.reply_text})

    user_input = input("You: ")
    if user_input.strip().lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})