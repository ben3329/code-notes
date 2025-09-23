from default_app.api.v1.endpoints import test
from fastapi import APIRouter

v1_router = APIRouter()
v1_router.include_router(test.router, prefix="/test", tags=["test"])
