import os
import sys

from fastapi import FastAPI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from default_app.api.routers import router

app = FastAPI(
    title="기본 디렉토리 구조 예시",
)

app.include_router(router)
