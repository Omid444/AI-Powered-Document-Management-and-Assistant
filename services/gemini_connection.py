# import os, json
# from dotenv import load_dotenv
# from pydantic import BaseModel, ValidationError
# from typing import Optional, Dict, List  # Import List for the new tags type
# # from google import genai
# # from google.genai import types
#
# # Load environment variables from .env file
# load_dotenv()
# # client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY").strip())
#
#
# # 1. Pydantic model for structured output validation
# class DocumentSummary(BaseModel):
#     """Defines the structure for the summarized document metadata."""
#     title: str
#     summary: str
#     # FIX: Changing from Dict[str, str] to List[str] to satisfy strict API schema
#     # requirements (which prohibit 'additionalProperties' and require 'properties' for 'object' types).
#     tags: Optional[List[str]] = None
#     is_payment: Optional[float] = None
#     is_tax_related: Optional[bool] = None
#     due_date: Optional[str] = None  # ISO YYYY-MM-DD
#     doc_date: Optional[str] = None  # ISO YYYY-MM-DD
#
#
# # 2. JSON Schema for Gemini model instruction
# # NOTE: The schema MUST match the structure of the Pydantic model.
# RESPONSE_SCHEMA = {
#     "type": "object",
#     "properties": {
#         "title": {"type": "string", "description": "A concise title for the document."},
#         "summary": {"type": "string", "description": "A simple, second-person summary of the document content."},
#         # FIX APPLIED HERE: Changed type to 'array' (list) of strings, as this
#         # avoids the strict 'object' type requirements imposed by the API SDK.
#         "tags": {
#             "type": "array",
#             "items": {"type": "string"},
#             "description": "A list of relevant tags or keywords. Example: ['Invoice', 'Unpaid', 'Insurance']"
#         },
#         "is_payment": {"type": "number", "description": "The payment amount, if applicable."},
#         "is_tax_related": {"type": "boolean", "description": "True if the document is tax related."},
#         "due_date": {"type": "string", "format": "date", "description": "The due date in YYYY-MM-DD format."},
#         "doc_date": {"type": "string", "format": "date",
#                      "description": "The date the document was issued in YYYY-MM-DD format."}
#     },
#     "required": ["title", "summary"]
# }
#
#
# def file_upload_llm_gemini(user_message, meta_data) -> DocumentSummary:
#     """
#     Analyzes a document text using Gemini and returns structured metadata
#     validated against the DocumentSummary Pydantic model.
#     """
#     print("User Message:", user_message)
#
#     system_text = (
#         "You are a helpful assistant specialized in document processing. "
#         "Your task is to analyze the user's document and return a summary and metadata **strictly in the requested JSON format**. "
#         "Do not include any other text, explanation, or conversational fillers. "
#         "Summarize the document to be simpler and more understandable. "
#         "Focus more on important metadata like due date or payment amount if exist in document. "
#         "For the 'tags' field, generate a JSON array of strings with relevant keywords (e.g., ['Invoice', 'Unpaid', 'Insurance']). "
#     )
#
#     config = types.GenerateContentConfig(
#         temperature=0.2,
#         max_output_tokens=1000,
#         response_mime_type="application/json",
#         response_schema=RESPONSE_SCHEMA,
#         system_instruction=system_text,
#     )
#
#     resp = client.models.generate_content(
#         model="gemini-2.5-flash",
#         contents=user_message,
#         config=config,
#     )
#
#     raw_json = resp.text
#     print("Raw JSON text received:", raw_json)
#
#     if not raw_json:
#         # Check for model block reasons
#         if resp.prompt_feedback and resp.prompt_feedback.block_reason:
#             raise ValueError(
#                 f"Gemini response was blocked: {resp.prompt_feedback.block_reason}. "
#                 f"Safety ratings: {resp.prompt_feedback.safety_ratings}"
#             )
#         raise ValueError("Gemini did not return any JSON text.")
#
#     # Manually parse JSON → Pydantic
#     try:
#         # Attempt to validate and return the Pydantic model
#         return DocumentSummary.model_validate_json(raw_json)
#     except ValidationError as e:
#         print(f"Pydantic Validation Error during parsing: {e}")
#         # Fallback for slight deviations
#         try:
#             data = json.loads(raw_json)
#             return DocumentSummary.model_validate(data)
#         except Exception as json_e:
#             raise ValueError(f"Failed to parse or validate JSON output. Raw text: {raw_json}. Error: {json_e}") from e
#
#
# def ask_ai_gemini(user_message: str) -> str:
#     """A standard function for conversational queries."""
#     config = types.GenerateContentConfig(
#         temperature=0.3,
#         max_output_tokens=300,
#         system_instruction="You are a helpful assistant.",
#     )
#     resp = client.models.generate_content(
#         model="gemini-2.5-flash",
#         contents=user_message,
#         config=config,
#     )
#     return resp.text