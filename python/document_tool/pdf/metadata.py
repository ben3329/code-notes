from collections import deque
from datetime import datetime

import pytz
from pypdf import PdfReader, PdfWriter

libre_queue: deque[str] = deque()


def write_metadata(pdf_path: str) -> None:
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.add_metadata(
        {
            "/Subject": "Subject here",
            "/Author": "Author here",
            "/Creator": "Creator here. Usually the software name used to create the document",
            "/CreationDate": datetime.now(pytz.timezone("Asia/Seoul")).strftime(
                "D:%Y%m%d%H%M%S"
            ),
        }
    )

    with open(pdf_path, "wb") as f:
        writer.write(f)
