from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

T = TypeVar("T", bound=SQLModel)
T2 = TypeVar("T2", bound=BaseModel)


# 단순히 boilerplate 줄이기용 함수
async def get_data_from_db(
    session: AsyncSession,
    model: Type[T],
    schema: Type[T2],
    query: Optional[select] = None,
) -> list[T2]:
    """Get list of items from database and convert to schema"""
    if query is None:
        query = select(model)

    items = (await session.exec(query)).all()

    # BaseModel의 default config는 extra='ignore'이므로 model_dump()의 결과에
    # schema에 없는 필드가 있어도 무시하고 생성됨
    return [schema.model_validate(item.model_dump()) for item in items]
