from copy import deepcopy

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        summary=app.summary,
        description=app.description,
        terms_of_service=app.terms_of_service,
        contact=app.contact,
        license_info=app.license_info,
        routes=app.routes,
        webhooks=app.webhooks.routes,
        tags=app.openapi_tags,
        servers=app.servers,
        separate_input_output_schemas=app.separate_input_output_schemas,
    )

    # 스키마 오버라이딩
    # swagger dart code generator를 위해 ref 제거
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if request_body := method.get("requestBody"):
                if content := request_body.get("content"):
                    if multipart_form_data := content.get("multipart/form-data"):
                        if schema := multipart_form_data.get("schema"):
                            if ref := schema.get("$ref"):
                                component = deepcopy(
                                    openapi_schema["components"]["schemas"][
                                        ref.split("/")[-1]
                                    ]
                                )
                                component.pop("title")
                                multipart_form_data["schema"] = component
                                schema.pop("$ref")
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
