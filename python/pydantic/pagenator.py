from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class PaginatedOut(BaseModel):
    total: int
    page: int
    pages: int
    items: list[T]  # type: ignore
