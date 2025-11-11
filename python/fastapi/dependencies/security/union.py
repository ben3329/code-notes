"""설정에 따라 인증 종속성을 선택 필요 시 사용"""

from enum import Enum

from dependencies.security.api_key import check_api_key
from dependencies.security.cognito import cognito_access_bearer


class AuthTypeEnum(Enum):
    COGNITO = "cognito"
    API_KEY = "api_key"


def get_auth():
    auth_type = AuthTypeEnum.API_KEY
    if auth_type == AuthTypeEnum.COGNITO:
        return cognito_access_bearer
    elif auth_type == AuthTypeEnum.API_KEY:
        return check_api_key


current_auth = get_auth()
