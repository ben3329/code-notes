from datetime import timedelta

from fastapi import Depends, Request, Security
from fastapi_jwt import JwtAccessBearer, JwtAuthorizationCredentials, JwtRefreshBearer
from sqlmodel import Session

jwt_access_bearer = JwtAccessBearer(
    secret_key="mysecretkey",
    auto_error=True,
    access_expires_delta=timedelta(hours=12),
    refresh_expires_delta=timedelta(days=30),
)

jwt_refresh_bearer = JwtRefreshBearer.from_other(other=jwt_access_bearer)


def get_session() -> Session:
    pass


def access_security(
    jwt: JwtAuthorizationCredentials = Security(jwt_access_bearer),
    session: Session = Depends(get_session),
    request: Request = None,
):
    pass
    pass
