# app/services/google_oauth_code.py
import httpx
from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel, Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings


class GoogleConfig(BaseSettings):
    client_id: str
    client_secret: str


config = GoogleConfig()
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
FRONT_END_URL = "http://localhost:3000/"  # your frontend url


class GoogleTokenResponse(BaseModel):
    access_token: str
    expires_in: int
    id_token: str | None = None
    refresh_token: str | None = None
    scope: str | None = None
    token_type: str


class GoogleDecodedToken(BaseModel):
    iss: str
    aud: str
    sub: str
    email: str
    email_verified: bool = Field(default=True)
    name: str | None = None
    picture: HttpUrl | None = None
    hd: str | None = None  # workspace domain
    iat: int
    exp: int

    @field_validator("iss")
    @classmethod
    def _iss_ok(cls, v: str):
        if v not in GOOGLE_ISSUERS:
            raise ValueError("wrong issuer")
        return v


class GoogleTokenExchangeError(Exception):
    pass


async def exchange_code_for_tokens(code: str, redirect_uri: str) -> GoogleTokenResponse:
    data = {
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
        payload = resp.json()
        if resp.status_code != 200 or "error" in payload:
            raise GoogleTokenExchangeError(str(payload))
        return GoogleTokenResponse(**payload)


def verify_google_id_token(id_token_str: str) -> GoogleDecodedToken:
    """
    Verify Google ID token using google-auth (handles keys, exp, aud).
    Returns decoded claims dict on success.
    """
    try:
        info: dict = google_id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            config.client_id,  # audience
        )
        if info.get("iss") not in GOOGLE_ISSUERS:
            raise ValueError("Wrong issuer")
        if info.get("email_verified") is False:
            raise ValueError("Email not verified")

        return GoogleDecodedToken.model_validate(info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


router = APIRouter()


@router.post("/sign_in_with_google")
async def sign_in_with_google_code(
    request: Request,
    code: str = Form(...),
    state: str = Form(None),
    scope: str = Form(None),
    authuser: str = Form(None),
    hd: str = Form(None),
    prompt: str = Form(None),
) -> RedirectResponse:
    # 1) Exchange authorization code for tokens
    try:
        tokens = await exchange_code_for_tokens(
            code, str(request.url._url.split("?")[0])
        )
    except GoogleTokenExchangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google token exchange failed: {e}",
        )

    if not tokens.id_token:
        raise HTTPException(status_code=400, detail="No id_token in Google response")

    # 2) Verify Google ID token (iss/aud/exp, etc.)
    try:
        gtok = verify_google_id_token(tokens.id_token)

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google ID token: {e}")

    # 3) Find account in DB
    account = None

    # 4) Mint jwt tokens
    access_token = ""

    # 5) Redirect to your frontend
    redirect_url = f"{FRONT_END_URL}/login?access_token={access_token}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
