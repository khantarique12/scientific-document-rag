import pymupdf


def create_pdf_bytes(text="Scientific document"):
    document = pymupdf.open()

    page = document.new_page()
    page.insert_text((72, 72), text)

    pdf_bytes = document.tobytes()
    document.close()

    return pdf_bytes
