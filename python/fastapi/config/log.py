import logging


# AWS ECS Log에서 healthcheck 로그를 필터링하기 위한 필터
class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True
        lower = message.lower()
        # Filter common access log patterns for healthcheck endpoints
        return not ("/healthcheck" in lower and ("get" in lower or "head" in lower))


uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addFilter(HealthCheckFilter())
