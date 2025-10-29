from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from scalar_fastapi import get_scalar_api_reference
from sqlmodel import Field

DISABLE_API_DOCS = False  # Set to True to disable OpenAPI docs

app = FastAPI(
    title="My API",
    redoc_url="/redoc" if not DISABLE_API_DOCS else None,
    openapi_url="/openapi.json" if not DISABLE_API_DOCS else None,
    version="1.0.0",
    description="Description in HTML format.",
    openapi_tags=[
        {"name": "SomeTag", "description": "SomeTag description"},
    ],
    contact={
        "name": "MyCompany Support",
    },
    license_info={
        "name": "Proprietary",
    },
)


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
        hide_client_button=True,
        hidden_clients=[
            "libcurl",
            "webrequest",
            "restmethod",
        ],
    )


class HelloOut(BaseModel):
    message: str = Field(..., description="A friendly greeting message")


@app.get(
    "/hello",
    tags=["SomeTag"],
    summary="Hello Endpoint",
    description="An endpoint that returns a friendly greeting.",
    responses={
        status.HTTP_418_IM_A_TEAPOT: {
            "description": "I'm a teapot",
        }
    },
)
async def hello(
    error: bool = Query(
        False, description="Trigger teapot error", examples=[True, False]
    )
) -> HelloOut:
    if error:  # Example condition to raise the teapot error
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT, detail="I'm a teapot"
        )
    return HelloOut(message="Hello, World!")
