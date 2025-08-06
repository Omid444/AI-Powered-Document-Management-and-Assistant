import PyPDF2


def extract_txt(pdf_stream):
    reader = PyPDF2.PdfReader(pdf_stream)

    full_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"
    return full_text