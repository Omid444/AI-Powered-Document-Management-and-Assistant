import PyPDF2
from io import BytesIO

def extract_text_and_metadata(file_bytes: bytes):
    # Create a BytesIO object from the byte string to be compatible with PyPDF2
    pdf_stream = BytesIO(file_bytes)
    reader = PyPDF2.PdfReader(pdf_stream)

    full_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"

    meta_data = reader.metadata
    full_metadata = {key: value for key, value in meta_data.items()}

    return full_text, full_metadata

