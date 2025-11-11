from sqlalchemy.orm import selectinload
from sqlmodel import case, delete, func, literal, or_, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from .table import SomeTable

default = (
    select(SomeTable)
    .where(SomeTable.index_column == "default")
    .group_by(SomeTable.id)
    .order_by(
        SomeTable.created_at.desc(),
    )
    .limit(1)
)

select_in_load = (
    select(SomeTable)
    .options(selectinload(SomeTable.useforeign_list))
    .where(SomeTable.index_column == "default")
)

where_in = select(SomeTable).where(
    SomeTable.id.in_([1, 2, 3]),
)

where_is = select(SomeTable).where(
    SomeTable.text_column.is_(None),
)

or_query = select(SomeTable).where(
    or_(SomeTable.int_column > 10, SomeTable.bool_column == True)
)

case_query = select(
    SomeTable,
    case(
        (SomeTable.bool_column == True, "It's True"),
        else_="It's False",
    ).label("bool_description"),
)

union = select(literal("AAA").label("label"), SomeTable.id).union_all(
    select(literal("BBB"), SomeTable.id)
)


delete_query = delete(SomeTable).where(SomeTable.id == default.id)

update_query = (
    update(SomeTable)
    .where(SomeTable.id == default.id)
    .values(text_column="updated text")
)

cte = default.cte("default_cte")
subquery = default.subquery()
count_query = select(func.count()).select_from(cte)
page = 1
limit = 10
paginated_query = (
    select(cte.c.id)
    .select_from(cte)
    .order_by(cte.c.update_date.desc(), cte.c.id)
    .offset((page - 1) * limit)
    .limit(limit)
)


async def get_query_result(session: AsyncSession):
    first = (await session.exec(default)).first()
    one_or_none = (
        await session.exec(select(SomeTable).where(SomeTable.id == 1))
    ).one_or_none()  # 2개 이상일 때 에러
    all_results = (await session.exec(select(SomeTable))).all()
    get = await session.get(SomeTable, 1)
    get_with_options = await session.get(
        SomeTable,
        1,
        options=[selectinload(SomeTable.useforeign_list)],
    )
