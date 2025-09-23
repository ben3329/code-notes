# fastapi run fastapi/examples/api_filtering.py
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decorators.marking import marking
from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute

app = FastAPI(
    title="My FastAPI Application",
    openapi_url="/openapi.json",
    version="1.0.0",
)

base_router = APIRouter()


@base_router.get("/hello")
async def hello():
    return {"message": "Hello, World!"}


@base_router.get("/hello2")
@marking
async def hello2():
    return {"message": "Hello, World!"}


for route in base_router.routes:
    if isinstance(route, APIRoute):
        endpoint = route.endpoint
        if getattr(endpoint, "marked", False):
            app.router.routes.append(route)
