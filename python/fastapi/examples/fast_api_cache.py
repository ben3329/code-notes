import hashlib
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from sqlmodel.ext.asyncio.session import AsyncSession

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

redis_url = "redis://localhost:6379"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    backend = None
    redis = None
    # Initialize cache with Redis/Valkey if available; fallback to in-memory on failure
    try:
        redis = aioredis.from_url(
            redis_url,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        # Proactively verify connectivity to avoid runtime surprises
        await redis.ping()
        backend = RedisBackend(redis=redis)
    except Exception as e:
        print(
            "Warning: Redis cache unavailable, falling back to in-memory cache",
            e,
        )
    if backend is None:
        backend = InMemoryBackend()

    FastAPICache.init(
        backend,
        prefix="fastapi-cache",
    )
    try:
        yield
    finally:
        # Close Redis connection if we opened one
        if redis is not None:
            try:
                await redis.close()
            except Exception:
                pass


app = FastAPI(lifespan=lifespan)

CACHE_EXPIRATION = 60 * 5  # seconds


@app.get("/test")
@cache(expire=CACHE_EXPIRATION)
async def get_authentication_result_list():
    return {"message": "Hello World"}


# Example usage of custom key builder to exclude session objects from cache key
def key_builder_without_session(
    func,
    namespace,
    *,
    request,
    response,
    args,
    kwargs,
) -> str:
    new_args = tuple(arg for arg in args if not isinstance(arg, AsyncSession))
    new_kwargs = {k: v for k, v in kwargs.items() if not isinstance(v, AsyncSession)}
    cache_key = hashlib.md5(  # noqa: S324
        f"{func.__module__}:{func.__name__}:{new_args}:{new_kwargs}".encode()
    ).hexdigest()
    return f"{namespace}:{cache_key}"


def get_session() -> AsyncSession:
    """Dummy function to illustrate dependency injection of session."""
    pass


@app.get("/with_key_builder")
@cache(expire=60, key_builder=key_builder_without_session)
async def with_key_builder(session: AsyncSession = Depends(get_session)):
    return {"message": "Hello World"}
