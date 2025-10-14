from decorators.limiter import limiter
from fastapi import FastAPI, Request, Security
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI()

DEFAULT_LIMIT = "30/minute"


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
