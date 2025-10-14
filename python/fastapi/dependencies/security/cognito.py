from dataclasses import Field
from typing import Callable, Optional, TypeVar

import boto3
from fastapi import Request
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPBearer
from fastapi_cognito import CognitoAuth, CognitoSettings, CognitoToken
from pycognito import Cognito
from pydantic_settings import BaseSettings, SettingsConfigDict

T = TypeVar("T")


class AWSCognitoConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    access_key_id: str
    secret_access_key: str
    region: str
    cognito_user_pool_id: str
    cognito_client_id: str


class CustomCognitoToken(CognitoToken):
    sub: Optional[str] = None
    groups: Optional[list[str]] = Field(None, alias="cognito:groups")


class CognitoAccessBearer(HTTPBearer):
    def __init__(
        self,
        callback: Callable[[Cognito, CustomCognitoToken], T],
        config: Optional[AWSCognitoConfig] = None,
    ):
        super().__init__()
        if config is None:
            config = AWSCognitoConfig()
        self.config = config
        self.boto3_session = boto3.Session(
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
        )
        self.cognito_auth = CognitoAuth(
            settings=CognitoSettings(
                check_expiration=True,
                jwt_header_name="Authorization",
                jwt_header_prefix="Bearer",
                userpools={
                    "default": {
                        "region": config.region,
                        "userpool_id": config.cognito_user_pool_id,
                        "app_client_id": config.cognito_client_id,
                    }
                },
            ),
            custom_model=CustomCognitoToken,
        )
        self.callback = callback

    async def __call__(self, request: Request) -> T:
        cognito_token: CustomCognitoToken = await self.cognito_auth.auth_required(
            request
        )
        cognito = Cognito(
            user_pool_id=self.config.cognito_user_pool_id,
            client_id=self.config.cognito_client_id,
            access_token=request.headers["Authorization"].split(" ")[1],
            session=self.boto3_session,
        )
        return await run_in_threadpool(self.callback, cognito, cognito_token)


def cognito_auth_callback(
    cognito: Cognito, token: CustomCognitoToken
) -> CustomCognitoToken:
    return token


cognito_access_bearer = CognitoAccessBearer(cognito_auth_callback)
