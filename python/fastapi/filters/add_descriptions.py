from datetime import date
from typing import Optional

from fastapi import Query
from fastapi_filter.contrib.sqlalchemy import Filter
from sqlmodel import Field, SQLModel


class SomeDB(SQLModel, table=True):
    id: int = Field(primary_key=True)
    string_column: str
    int_column: int
    bool_column: bool
    date_column: date


class SomeFilter(Filter):
    string_column: Optional[str] = Query(
        Query(
            None,
            type="string",
            description="Filter by exact match of string column",
            examples=["somevalue"],
        )
    )
    int_column: Optional[int] = Query(
        Query(
            None,
            type="integer",
            description="Filter by exact match of int column",
            examples=[123456],
        )
    )
    bool_column: Optional[bool] = Query(
        Query(
            None,
            type="boolean",
            description="Filter by exact match of boolean column",
            examples=[True],
        )
    )
    date_column: Optional[date] = Query(
        Query(
            None,
            type="date",
            description="Filter by exact match of date column",
            examples=["2024-07-01"],
        )
    )

    class Constants(Filter.Constants):
        model = SomeDB
