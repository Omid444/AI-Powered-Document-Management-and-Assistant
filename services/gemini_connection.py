import os, json
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from typing import Optional, Dict
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY").strip())

class DocumentSummary(BaseModel):
    title: str
    summary: str
    tags: Optional[Dict[str, str]] = None
    is_payment: Optional[float] = None
    is_tax_related: Optional[bool] = None
    due_date: Optional[str] = None   # ISO YYYY-MM-DD
    doc_date: Optional[str] = None   # ISO YYYY-MM-DD

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "tags": {"type": "string"},
        "is_payment": {"type": "number"},
        "is_tax_related": {"type": "boolean"},
        "due_date": {"type": "string", "format": "date"},
        "doc_date": {"type": "string", "format": "date"}
    },
    "required": ["title", "summary"]
}




def file_upload_llm_gemini(user_message, meta_data) -> DocumentSummary:
    system_text = (
        "You are a helpful assistant. Answer in less than 500 words. "
        "First, if needed, explain the text in three or more lines. "
        "This is a document that belongs to the user; summarize it to be simpler and more understandable. "
        f"Use the provided document and {RESPONSE_SCHEMA} format to return response in jason format  "
        "Focus more on important metadata like due date or payment amount if exist in document "
        "Always write in the second-person point of view. "

    )

    config = types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=1000,
        response_schema=RESPONSE_SCHEMA,   # ✅ JSON Schema (not Pydantic class)
        system_instruction=system_text,    # simple string is fine
    )

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_message,             # simple string is fine
        config=config,
    )
    # print("FULL RESPONSE: .  ..   ...   ...   ...  ....  ....  .... .... ...")
    # import pprint
    # pprint.pprint(resp.to_dict())
    print("resp", resp)
    # Manually parse JSON → Pydantic
    raw_json = resp.text  # model returns JSON text because of response_mime_type
    if not raw_json:
        raise ValueError("Gemini did not return any text")
    try:
        return DocumentSummary.model_validate_json(raw_json)
    except ValidationError:
        # if model returned slight deviations, try a lenient path
        data = json.loads(raw_json)
        return DocumentSummary.model_validate(data)


def ask_ai_gemini(user_message: str) -> str:
    config = types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=300,
        system_instruction="You are a helpful assistant.",
    )
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_message,
        config=config,
    )
    return resp.text

# MODEL_NAME = "gemini-2.5-flash"
# user_message = "Dear Omid Davoudi,"
# "We hope this message finds you well. This notice serves as a formal payment request for your active"
# "insurance policy (Policy No. SL-45239876-X). To ensure uninterrupted coverage, please complete the"
# "payment of $245.00 by the due date indicated below. Your timely action will ensure continuous"
# "protection under our comprehensive insurance plan."
# "Failure to make the payment by the specified due date may result in a temporary suspension of your"
# "policy benefits. We highly recommend you complete your payment as soon as possible to avoid any"
# "disruption. If you have already settled this invoice, please disregard this notice. For any inquiries"
# "Invoice Number INV-890123"
# "Policy Number SL-45239876-X"
# "Issue Date 2025-08-07"
# "Due Date 2025-08-17"
# "Amount Due $245.00"
# "Payment Method Bank Transfer / Credit Card / Online Portal"
#
# # 4. Generate content
# try:
#     system_text = (
#         "You are a helpful assistant. Answer in less than 500 words. "
#         "First, if needed, explain the text in three or more lines. "
#         "This is a document that belongs to the user; summarize it to be simpler and more understandable. "
#         f"Use the provided document metadata: {"meta_data"} to give a detailed reply. "
#         "Focus more on important metadata like due date or payment amount. "
#         "Always write in the second-person point of view. "
#         "Return the result strictly in the defined JSON structure."
#     )
#
#     config = types.GenerateContentConfig(
#         temperature=0.2,
#         max_output_tokens=1000,
#         response_schema=RESPONSE_SCHEMA,  # ✅ JSON Schema (not Pydantic class)
#         system_instruction=system_text,  # simple string is fine
#     )
#
#     resp = client.models.generate_content(
#         model="gemini-2.5-flash",
#         contents=user_message,  # simple string is fine
#         config=config,
#     )
#     print(resp)
#     print(resp.text)
# except Exception as e:
#     print(f"\nError generating content: {e}")
#     print("Check your model name (e.g., 'gemini-2.5-flash') and API key validity.")
