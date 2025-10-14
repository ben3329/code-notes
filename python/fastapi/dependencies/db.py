from typing import AsyncGenerator, Generator

from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from python.sqlmodel.session import DBEngine


def get_sync_session() -> Generator[Session, None, None]:
    db = DBEngine()
    with Session(db.engine) as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    db = DBEngine()
    async with db.AsyncSessionLocal() as conn:
        yield conn
