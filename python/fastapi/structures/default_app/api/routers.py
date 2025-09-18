from default_app.api.v1.routers import v1_router
from fastapi import APIRouter

router = APIRouter()

router.include_router(v1_router, prefix="/v1")
