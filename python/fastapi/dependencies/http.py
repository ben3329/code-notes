from collections.abc import AsyncGenerator

import httpx


async def get_async_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    client = httpx.AsyncClient(
        http2=False,
        timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    try:
        yield client
    finally:
        await client.aclose()
