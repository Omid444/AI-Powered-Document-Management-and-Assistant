import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
apikey = os.getenv("OPENAI_KEY")
print(apikey)
client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

def ask_ai(user_message, meta_data=""):
    response = client.chat.completions.create(
        model="gpt-4o-mini",  #  gpt-4-vision-preview
        messages=[
            {
                "role": "developer",
                "content": f"You are a helpful assistant. at first explains in two or fewer lines about this text."
                " It is a document belongs to me, summarize this text for me to make it more simple and understandable"
                f"use the metadata of document which is provided here:{meta_data} to provide detailed reply. "
                f"focus on important details of metadata more, something like due date or payment amount"
                f"and remember always write it in second person format"
            },
            {"role": "user", "content": user_message}
        ],
        max_tokens=300,
    )

    print(response.choices[0].message.content)
    return response.choices[0].message.content


