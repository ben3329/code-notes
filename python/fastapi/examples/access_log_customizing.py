import http
import logging
import time
from contextlib import asynccontextmanager
from copy import copy
from typing import AsyncIterator

import click
from fastapi import FastAPI, Request
from uvicorn.logging import ColourizedFormatter


def _mute_default_access_log():
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.handlers.clear()
    uvicorn_logger.propagate = False
    uvicorn_logger.disabled = True


_mute_default_access_log()


class CustomAccessFormatter(ColourizedFormatter):
    status_code_colours = {
        1: lambda code: click.style(str(code), fg="bright_white"),
        2: lambda code: click.style(str(code), fg="green"),
        3: lambda code: click.style(str(code), fg="yellow"),
        4: lambda code: click.style(str(code), fg="red"),
        5: lambda code: click.style(str(code), fg="bright_red"),
    }

    def get_status_code(self, status_code: int) -> str:
        try:
            status_phrase = http.HTTPStatus(status_code).phrase
        except ValueError:
            status_phrase = ""
        status_and_phrase = f"{status_code} {status_phrase}"
        if self.use_colors:

            def default(code: int) -> str:
                return status_and_phrase

            func = self.status_code_colours.get(status_code // 100, default)
            return func(status_and_phrase)
        return status_and_phrase

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        (
            client_addr,
            method,
            full_path,
            http_version,
            status_code,
            step,
            process_time,
        ) = recordcopy.args
        status_code = (
            self.get_status_code(int(status_code)) if status_code is not None else "- -"
        )
        request_line = f"{method} {full_path} HTTP/{http_version}"
        if self.use_colors:
            request_line = click.style(request_line, bold=True)
        recordcopy.__dict__.update(
            {
                "client_addr": client_addr,
                "request_line": request_line,
                "status_code": status_code,
                "step": step,
                "process_time": (
                    round(process_time, 3) if process_time is not None else "-"
                ),
            }
        )
        return super().formatMessage(recordcopy)


def _configure_app_access_log():
    logger = logging.getLogger("app.access")
    handler = logging.StreamHandler()
    handler.setFormatter(
        CustomAccessFormatter(
            '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s -- %(step)s (%(process_time)s s)'
        )
    )
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


_configure_app_access_log()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Initialize cache with Redis/Valkey if available; fallback to in-memory on failure
    try:
        _mute_default_access_log()
        yield
    finally:
        # Close Redis connection if we opened one
        pass


app = FastAPI(
    lifespan=lifespan,
)

logger = logging.getLogger("app.access")
ignore_logging_paths = ["/healthcheck"]


@app.middleware("http")
async def custom_access_log(request: Request, call_next):
    forwarded_for = request.headers.get("x-forwarded-for")
    client_host = request.client.host if request.client else "-"
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else client_host
    http_version = request.scope.get("http_version", "1.1")
    path = request.url.path
    if request.url.query:
        path = f"{path}?{request.url.query}"
    if request.url.path not in ignore_logging_paths:
        logger.info(
            '%s - "%s %s HTTP/%s" %s -- %s (%s s)',
            client_ip,
            request.method,
            path,
            http_version,
            None,
            "START",
            None,
        )

    start = time.time()
    response = await call_next(request)
    end = time.time()

    if request.url.path not in ignore_logging_paths:
        logger.info(
            '%s - "%s %s HTTP/%s" %s -- %s (%s s)',
            client_ip,
            request.method,
            path,
            http_version,
            response.status_code,
            "END",
            (end - start),
        )
    return response
