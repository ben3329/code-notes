from pypdf import PdfReader, PdfWriter

WATERMARK_PATH = "some/path/to/watermark.pdf"


def add_watermark(pdf_path: str) -> None:

    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    watermark = PdfReader(WATERMARK_PATH).pages[0]

    for page in reader.pages:
        page.merge_page(watermark)
        writer.add_page(page)

    with open(pdf_path, "wb") as f:
        writer.write(f)
