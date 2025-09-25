from uuid import UUID, uuid4

from dependencies.db import get_sync_session
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlmodel import Field, Session, SQLModel, select


class APIKey(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    key: str = Field(index=True, unique=True)
    user_id: UUID = Field(foreign_key="user.id")


api_key_header = APIKeyHeader(name="x-api-key", scheme_name="API Key", auto_error=True)


def check_api_key(
    api_key: str = Security(api_key_header),
    session: Session = Depends(get_sync_session),
) -> UUID:
    api_key_obj = session.exec(
        select(APIKey).where(APIKey.key == api_key)
    ).one_or_none()
    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return api_key_obj.user_id
