"""
fastapi-pagination으로 구현하기 어려운 경우 사용
* 데이터 조회 후 추가 작업이 필요한 경우
"""

from math import ceil
from typing import Optional

from dependencies.db import get_async_session
from fastapi import APIRouter, Depends, Query, Request
from fastapi_filter import FilterDepends
from filters.add_descriptions import SomeDB, SomeFilter
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from python.pydantic.pagenator import PaginatedOut

router = APIRouter()


@router.get("")
async def get_paginated_data(
    request: Request,
    limit: Optional[int] = Query(50, ge=1, le=100, type="integer"),
    page: Optional[int] = Query(1, ge=1, type="integer"),
    filters: SomeFilter = FilterDepends(SomeFilter),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedOut[SomeDB]:
    query = select(SomeDB)
    filtered_query = filters.filter(query)
    count_query = select(func.count()).select_from(filtered_query)
    total = (await session.exec(count_query)).one()

    paginated_query = filtered_query.offset((page - 1) * limit).limit(limit)
    items = (await session.exec(paginated_query)).all()

    return PaginatedOut(
        total=total,
        page=page,
        pages=ceil(total / limit),
        items=items,
    )
