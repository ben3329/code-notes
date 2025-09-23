import os
import time
from enum import Enum
from typing import Optional

import boto3
from fastapi import FastAPI, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# custom middleware example


class AWSParameterStoreConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    aws_maintenance_parameter_name: str
    is_devel: bool = True


class MaintenanceStatusEnum(Enum):
    OK = "ok"
    MAINTENANCE = "maintenance"


class CheckMaintenanceMiddleware(BaseHTTPMiddleware):
    _CHECK_INTERVAL = 300

    def __init__(
        self,
        app,
        aws_config: Optional[AWSParameterStoreConfig] = None,
        ignore_url_paths: list[str] = [],
    ):
        if aws_config is None:
            aws_config = AWSParameterStoreConfig()
        self.aws_config = aws_config
        self.ignore_url_paths = ignore_url_paths
        self._last_check_time: float = 0
        self._status: MaintenanceStatusEnum = MaintenanceStatusEnum.OK
        self._end_time: int
        super().__init__(app)

    def check_maintenance_status(
        self, config: AWSParameterStoreConfig
    ) -> tuple[MaintenanceStatusEnum, int]:
        ssm = boto3.client(
            "ssm",
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.aws_region,
        )
        if config.is_devel:
            name = os.path.join("/develop", config.aws_maintenance_parameter_name)
        else:
            name = os.path.join("/production", config.aws_maintenance_parameter_name)
        response = ssm.get_parameter(Name=name)
        status, end_time = response["Parameter"]["Value"].split(",")
        return MaintenanceStatusEnum(status), int(end_time)

    async def dispatch(self, request: Request, call_next):
        if request.url.path not in self.ignore_url_paths:
            now = time.time()
            if now - self._last_check_time > self._CHECK_INTERVAL:
                try:
                    self._status, self._end_time = await run_in_threadpool(
                        self.check_maintenance_status, self.aws_config
                    )
                except:
                    self._status = MaintenanceStatusEnum.OK
                self._last_check_time = now
            if self._status == MaintenanceStatusEnum.MAINTENANCE:
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={"status": self._status.value, "end_time": self._end_time},
                )
        response = await call_next(request)
        return response


app.add_middleware(
    CheckMaintenanceMiddleware,
    AWSParameterStoreConfig(),
    ignore_url_paths=["/healthcheck", "/docs", "/openapi.json", "/scalar", "/redoc"],
)
