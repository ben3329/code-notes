from datetime import datetime, timezone

from pydantic import BaseModel, field_validator


class BaseModelWithDatetime(BaseModel):
    model_config = {
        "json_encoders": {datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S %Z")}
    }

    @field_validator("*", mode="before")
    def set_utc_timezone(cls, value):
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.astimezone(timezone.utc)
        return value
