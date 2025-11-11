import json
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel, ValidationError


class AuditLog(BaseModel):
    datetime_utc: datetime
    pass


LOG_GROUP_NAME = "log-group-name"


class AWSSettings:
    access_key_id: str
    secret_access_key: str
    region: str


config = AWSSettings()


class CloudWatch:
    _DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z"
    _MIN_DATETIME = datetime.min.replace(tzinfo=timezone.utc)
    _AWS_MAX_LIMIT = 1000

    def __init__(self):
        self._log_group = LOG_GROUP_NAME
        self._client = boto3.client(
            "logs",
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
        )

    @staticmethod
    def _to_epoch_millis(value: datetime | None) -> int | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return int(value.timestamp() * 1000)

    def _parse_datetime(self, value: str) -> datetime | None:
        try:
            parsed = datetime.strptime(value, self._DATETIME_FORMAT)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                return None
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)

    def _event_to_audit_log(
        self,
        message: str,
        timestamp_ms: int | None,
    ) -> AuditLog | None:
        if not message:
            return None
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return None

        datetime_value = payload.get("datetime_utc")
        parsed_datetime = (
            self._parse_datetime(datetime_value)
            if isinstance(datetime_value, str)
            else None
        )
        if parsed_datetime is None and timestamp_ms is not None:
            parsed_datetime = datetime.fromtimestamp(
                timestamp_ms / 1000, tz=timezone.utc
            )
        if parsed_datetime is None:
            return None
        payload["datetime_utc"] = parsed_datetime

        try:
            return AuditLog(**payload)
        except ValidationError:
            return None

    def fetch_audit_logs(
        self,
        limit: int,
        start_time: datetime | None,
        end_time: datetime | None,
        next_token: str | None,
    ) -> tuple[list[AuditLog], str | None]:
        collected_logs: list[AuditLog] = []
        token = next_token

        start_ms = self._to_epoch_millis(start_time)
        end_ms = self._to_epoch_millis(end_time)

        while len(collected_logs) < limit:
            request_limit = min(self._AWS_MAX_LIMIT, limit - len(collected_logs))
            params: dict[str, Any] = {
                "logGroupName": self._log_group,
                "limit": request_limit,
            }
            if start_ms is not None:
                params["startTime"] = start_ms
            if end_ms is not None:
                params["endTime"] = end_ms
            if token:
                params["nextToken"] = token

            try:
                result = self._client.filter_log_events(**params)
            except (BotoCoreError, ClientError) as exc:
                raise RuntimeError(
                    "Failed to fetch audit logs from CloudWatch"
                ) from exc

            for event in result.get("events", []):
                log = self._event_to_audit_log(
                    event.get("message", ""),
                    event.get("timestamp"),
                )
                if log:
                    collected_logs.append(log)
                    if len(collected_logs) >= limit:
                        break

            token = result.get("nextToken")
            if not token:
                break

        collected_logs.sort(
            key=lambda log: log.datetime_utc or self._MIN_DATETIME,
            reverse=True,
        )

        return collected_logs, token
