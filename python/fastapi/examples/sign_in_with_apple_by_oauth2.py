import time
from typing import Literal

import httpx
from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import Base64Str, BaseModel
from pydantic_settings import BaseSettings


class AppleConfig(BaseSettings):
    team_id: str
    service_client_id: str
    app_client_id: str
    key_id: str
    private_key_base64: Base64Str


config = AppleConfig()

APPLE_PUBLIC_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
APPLE_ISSUER = "https://appleid.apple.com"
FRONT_END_URL = "http://localhost:3000/"  # your frontend url


class AppleDecodedToken(BaseModel):
    model_config = {"extra": "ignore"}
    sub: str
    email: str | None


class PublicKeyNotFoundError(Exception):
    pass


class TokenDecodeError(Exception):
    pass


class TokenGenerationError(Exception):
    pass


def _generate_client_secret():
    """Apple client_secret (JWT) 생성"""
    headers = {"kid": config.key_id, "alg": "ES256"}
    payload = {
        "iss": config.team_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 180,  # 6개월 유효
        "aud": APPLE_ISSUER,
        "sub": config.service_client_id,
    }
    return jwt.encode(
        payload, config.private_key_base64, algorithm="ES256", headers=headers
    )


async def _get_apple_public_keys() -> list[dict]:
    """Apple 공개키 가져오기"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(APPLE_PUBLIC_KEYS_URL)
        resp.raise_for_status()
        key_list = resp.json()["keys"]
        return key_list


async def verify_apple_id_token(
    id_token: str, mode: Literal["web", "app"] = "web"
) -> AppleDecodedToken:
    # 1. 토큰 header에서 kid, alg 추출
    header = jwt.get_unverified_header(id_token)
    public_keys = await _get_apple_public_keys()

    # 2. kid 일치하는 공개키 찾기
    public_key = next((k for k in public_keys if k["kid"] == header["kid"]), None)
    if public_key is None:
        raise PublicKeyNotFoundError("No matching public key found")

    try:
        # 3. jwt 검증
        payload = jwt.decode(
            id_token,
            public_key,
            algorithms=[header["alg"]],
            audience=(
                config.service_client_id if mode == "web" else config.app_client_id
            ),
            issuer=APPLE_ISSUER,
        )
        id_token = AppleDecodedToken.model_validate(payload)
        return id_token
    except ExpiredSignatureError as e:
        raise e
    except JWTError as e:
        raise e
    except Exception as e:
        raise TokenDecodeError("Failed to decode token") from e


async def get_id_token(code: str, redirect_url: str) -> str:
    client_secret = _generate_client_secret()
    data = {
        "client_id": config.app_client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": str(redirect_url),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(APPLE_TOKEN_URL, data=data)
        token_resp = resp.json()
        if "error" in token_resp:
            raise TokenGenerationError("Failed to generate token")

    id_token = token_resp.get("id_token")
    return id_token


router = APIRouter()


@router.post("/sign_in_with_apple")
async def sign_in_with_apple(
    request: Request,
    code: str = Form(...),
    id_token: str = Form(None),
    state: str = Form(None),
) -> RedirectResponse:

    # 1) validate id_token
    if not id_token:
        id_token = await get_id_token(code, request.url)
    decoded_token = await verify_apple_id_token(id_token)

    # 2) Find Account in DB
    if decoded_token.email:
        account = None
    else:
        account = None

    # 3) Mint jwt tokens
    access_token = ""

    # 5) Redirect to your frontend
    redirect_url = f"{FRONT_END_URL}/login?access_token={access_token}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


class SignInWithAppleIn(BaseModel):
    id_token: str


class SignInResultOut(BaseModel):
    access_token: str
    refresh_token: str


@router.post("/sign_in_with_apple/app")
async def sign_in_with_apple_for_app(
    sign_in_with_apple_in: SignInWithAppleIn,
) -> SignInResultOut:
    # 1) validate id_token
    decoded_token = await verify_apple_id_token(
        sign_in_with_apple_in.id_token, mode="app"
    )

    # 2) Find Account in DB
    if decoded_token.email:
        account = None
    else:
        pass

    # 4) Mint jwt tokens
    access_token = ""
    refresh_token = ""

    return SignInResultOut(
        access_token=access_token,
        refresh_token=refresh_token,
    )
