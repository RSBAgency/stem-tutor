import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

response = client.chat.completions.create(
        model= "gpt-5-mini",
        messages=[
            {"role": "user", "content": "Say hello in one sentence"}
        ],
    )

print(response.choices[0].message.content)