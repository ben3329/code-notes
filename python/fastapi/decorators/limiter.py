import hashlib
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from fastapi import Request
from slowapi import Limiter


def user_id_key_func(request: Request) -> str:
    """Rate-limit key function deriving from request state set by auth."""
    key = f"{request.state.user_id}_{request.method}_{request.url.path}"
    cache_key = hashlib.md5(key.encode()).hexdigest()
    return cache_key


F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def dummy_decorator_factory(*_d_args: Any, **_d_kwargs: Any) -> Callable[[F], F]:
    """No-op limiter for WEB runtime, preserving async function signature."""

    def dummy_decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
            return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return dummy_decorator


limiter = Limiter(
    key_func=user_id_key_func,
    storage_uri="SOME_URL",
)

USE_DUMMY_LIMITER = False  # Set to False to enable real rate limiting

if USE_DUMMY_LIMITER:
    limiter.limit = dummy_decorator_factory  # type: ignore[assignment]
