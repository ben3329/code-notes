from datetime import timedelta
from zoneinfo import ZoneInfo

from fastapi import Header, Request, Security
from fastapi_jwt import JwtAccessBearer, JwtAuthorizationCredentials, JwtRefreshBearer

jwt_access_bearer = JwtAccessBearer(
    secret_key="mysecretkey",
    auto_error=True,
    access_expires_delta=timedelta(hours=12),
    refresh_expires_delta=timedelta(days=30),
)

jwt_refresh_bearer = JwtRefreshBearer.from_other(other=jwt_access_bearer)


def access_security(
    jwt: JwtAuthorizationCredentials = Security(jwt_access_bearer),
    timezone: ZoneInfo = Header("Asia/Seoul", alias="X-Client-Timezone"),
    request: Request = None,
):
    print(timezone)
