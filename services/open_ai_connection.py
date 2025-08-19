import os
from openai import OpenAI
from dotenv import load_dotenv
import json
load_dotenv()
apikey = os.getenv("OPENAI_KEY")
print(apikey)
client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

def file_upload_llm(user_message, meta_data=""):
    response = client.chat.completions.create(
        model="gpt-4o-mini",  #  gpt-4-vision-preview
        messages=[
            {
                "role": "system",
                "content": f"You are a helpful assistant. at first explains in three or more lines (if needed) about this text."
                " It is a document belongs to me, summarize this text for me to make it more simple and understandable"
                f"use the metadata of document which is provided here:{meta_data} to provide detailed reply."
                f"focus on important details of metadata more, something like due date or payment amount"
                f"and remember always write it in second person format"
                f"also return a JSON object with the following fields:\n"
                    "- title: A short title based on the text, String format\n"
                    "- summary: A three-line or more explanation in second person format. Use provided metadata to improve accuracy. String Format\n"
                    "- tags: dictionary of metadata. dictionary format"       
                    "- is_payment: If  payment specified in document, write payment in float format(e.g. 120.0), otherwise null\n"
                    "_ is_tax_related: If document is tax related True (boolean format) otherwise null\n"
                    "- due_date: If the deadline date is specified in document for payment write date in date format in ISO format (YYYY-MM-DD), otherwise null\n"       
                    "- doc_date: If the document's date of publishing is there in document write date in date format in ISO format (YYYY-MM-DD), otherwise null"
            },
            {"role": "user", "content": user_message}
        ],
        max_tokens=300,
        response_format={"type": "json_object"}
    )

    print(response.choices[0].message.content)
    raw_text = response.choices[0].message.content
    data = json.loads(raw_text)
    print(data)
    return data


def ask_ai(user_message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",  #  gpt-4-vision-preview
        messages=[
            {
                "role": "system",
                "content": f"You are a helpful assistant"
            },
            {"role": "user", "content": user_message}
        ],
        max_tokens=300
    )

    response_data = response.choices[0].message.content
    return response_data
