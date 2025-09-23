import os
import time
from collections import deque

# libreoffice는 동시 변환에 문제가 있어 순차적으로 처리하기 위해 큐 사용
libre_queue: deque[str] = deque()


def docx_to_pdf(docx_path: str) -> str:
    global libre_queue
    libre_queue.append(docx_path)
    while libre_queue[0] != docx_path:
        time.sleep(1)
    outdir = os.path.dirname(docx_path)
    os.system(
        f"libreoffice --headless --convert-to pdf --outdir {outdir} '{docx_path}'"
    )
    libre_queue.popleft()
    return docx_path.rsplit(".", 1)[0] + ".pdf"
