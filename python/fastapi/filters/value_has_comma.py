from typing import Optional

from fastapi import Query
from fastapi_filter.contrib.sqlalchemy import Filter
from sqlmodel import Field, SQLModel


class SomeDB(SQLModel, table=True):
    id: int = Field(primary_key=True)
    comma_included_column: str


def _escape_comma(values: Optional[list[str]]) -> Optional[list[str]]:
    if values is None:
        return
    return [value.replace("%2C", ",") for value in values]


class SomeFilter(Filter):
    comma_included_column: Optional[str] = None
    comma_included_column__in: Optional[list[str]] = Query(
        Query(
            None,
            description="Comma separated values. Escape comma with %2C if the value contains comma",
        )
    )

    def filter(self, query):
        self.comma_included_column__in = _escape_comma(self.comma_included_column__in)
        return super().filter(query)

    class Constants(Filter.Constants):
        model = SomeDB
