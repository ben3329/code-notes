from functools import wraps
from inspect import signature
from typing import Callable
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Field, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


class RoleEnum(str):
    ADMIN = "admin"
    USER = "user"


class User(SQLModel, table=True):
    id: UUID | None = Field(default=None, primary_key=True)
    username: str
    role: RoleEnum


ROLE_HIERARCHY: dict[RoleEnum, list[RoleEnum]] = {
    RoleEnum.ADMIN: [RoleEnum.USER],
    RoleEnum.USER: [],
}


def has_role_or_above(checking_role: RoleEnum, required_role: RoleEnum) -> bool:
    if checking_role == required_role:
        return True
    for sub_role in ROLE_HIERARCHY[checking_role]:
        if has_role_or_above(sub_role, required_role):
            return True
    return False


def role_required(role: RoleEnum) -> Callable:
    """
    Decorator to check if the user has the required role.
    """

    def decorator(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            bound = signature(func).bind_partial(*args, **kwargs)
            user_id: UUID | None = bound.arguments.get("user")
            session: AsyncSession | None = bound.arguments.get("session")
            if user_id is None or session is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing dependencies for role verification",
                )
            db_user = await session.get(User, UUID(user_id))
            if not db_user or not has_role_or_above(db_user.role, role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden"
                )
            return await func(*args, **kwargs)

        return wrapped

    return decorator
