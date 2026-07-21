import os
from openai import OpenAI
from tutor_prompt import SYSTEM_PROMPT

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

print("Tutor test session. Type 'quit' to stop. \n")

messages.append({"role": "user", "content": "I need help solving 5x + 3y = 36 and x - y = 4"})

while True:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
    )

    reply = response.choices[0].message.content
    print(f"Tutor: {reply}\n")

    messages.append({"role": "assistant", "content": reply})

    user_input = input("You: ")
    if user_input.strip().lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})