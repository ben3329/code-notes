import hashlib
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from fastapi import FastAPI, Request, Security
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI()

redis_url = "redis://localhost:6379"
USE_DUMMY_LIMITER = False  # Set to False to enable real rate limiting
DEFAULT_LIMIT = "30/minute"


def user_id_key_func(request: Request) -> str:
    """Rate-limit key function deriving from request state set by auth."""
    key = f"{request.state.user_id}_{request.method}_{request.url.path}"
    cache_key = hashlib.md5(key.encode()).hexdigest()  # nosec S3241
    return cache_key


limiter = Limiter(
    key_func=user_id_key_func,
    storage_uri=redis_url,
)

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def dummy_decorator_factory(*_d_args: Any, **_d_kwargs: Any) -> Callable[[F], F]:
    """No-op limiter for WEB runtime, preserving async function signature."""

    def dummy_decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
            return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return dummy_decorator


if USE_DUMMY_LIMITER:
    limiter.limit = dummy_decorator_factory  # type: ignore[assignment]

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def auth_check(request: Request) -> str:
    request.state.user_id = "anonymous"  # for user_id_key_func
    return request.state.user_id


@app.get("/test")
@limiter.limit(DEFAULT_LIMIT)
async def test(
    request: Request,  # Must be first parameter for slowapi
    user=Security(auth_check),
):
    return {"message": "Hello World"}
