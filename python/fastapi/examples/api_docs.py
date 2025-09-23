from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

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


@app.get("/hello", tags=["SomeTag"])
async def hello():
    return {"message": "Hello, World!"}
