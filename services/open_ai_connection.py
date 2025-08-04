import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_ai(user_message):
    response = client.chat.completions.create(
        model="gpt-4o",  #  gpt-4-vision-preview
        messages=[
            {"role": "system", "content": user_message}
        ],
        max_tokens=300,
    )

    print(response.choices[0].message.content)
    return response.choices[0].message.content


