from typing import Any

from fastapi import Depends
from fastapi.exceptions import RequestValidationError
from fastapi_filter.base.filter import BaseFilterModel, _list_to_str_fields
from pydantic import ValidationError, create_model


def FilterDepends(
    Filter: type[BaseFilterModel], *, by_alias: bool = False, use_cache: bool = True
) -> Any:
    """
    from fastapi_filter import FilterDepends 사용 시 Optional을 반드시 사용해야 하는데, 이걸 사용할 경우 Optional 사용 안해도 됨.
    Optional 사용 시 openapi 문서에서 anyof로 인식 됨.
    "parameters": [
        {
            "name": "some",
            "in": "query",
            "required": false,
            "schema": {
                "anyOf": [
                    {
                        "type": "string"
                    },
                    {
                        "type": "null"
                    }
                ],
                "description": "Some filter",
                "title": "Some"
            },
            "description": "Some filter"
        },
    ]
    GET Parameter에서 anyOf에 null 사용 시 일부 코드 생성기에서 오류가 발생함.
    Optional을 사용 안 할 경우 아래와 같이 생성 됨.
    "parameters": [
        {
            "name": "some",
            "in": "query",
            "required": false,
            "schema": {
                "type": "string"
                "description": "Some filter",
                "title": "Some"
            },
            "description": "Some filter"
        },
    ]
    """
    fields = _list_to_str_fields(Filter)
    GeneratedFilter: type[BaseFilterModel] = create_model(
        Filter.__class__.__name__, **fields
    )

    class FilterWrapper(GeneratedFilter):  # type: ignore[misc,valid-type]
        def __new__(cls, *args, **kwargs):
            try:
                kwargs = {
                    kwargs_key: kwargs_value
                    for kwargs_key, kwargs_value in kwargs.items()
                    if kwargs_value is not None
                }
                instance = GeneratedFilter(*args, **kwargs)
                data = instance.model_dump(
                    exclude_unset=True, exclude_defaults=True, by_alias=by_alias
                )
                if original_filter := getattr(
                    Filter.Constants, "original_filter", None
                ):
                    prefix = f"{Filter.Constants.prefix}__"
                    stripped = {k.removeprefix(prefix): v for k, v in data.items()}
                    return original_filter(**stripped)
                return Filter(**data)
            except ValidationError as e:
                raise RequestValidationError(e.errors()) from e

    return Depends(FilterWrapper)
