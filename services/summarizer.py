import PyPDF2


def extract_txt(pdf_stream):
    reader = PyPDF2.PdfReader(pdf_stream)

    full_text = ""
    full_metadata = {}
    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            full_text += page_text + "\n"

    meta_data = reader.metadata
    for key, value in meta_data.items():
        full_metadata[key] = value

    return full_text , full_metadata