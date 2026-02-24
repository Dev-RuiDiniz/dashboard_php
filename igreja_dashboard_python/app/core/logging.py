from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any

from app.core.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        utc_tz = getattr(datetime, "UTC", None)
        if utc_tz is None:
            utc_tz = timezone.utc  # noqa: UP017 (compatibilidade com Python 3.10)
        payload: dict[str, Any] = {
            "timestamp": datetime.now(utc_tz).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        if hasattr(record, "method"):
            payload["method"] = record.method
        if hasattr(record, "path"):
            payload["path"] = record.path
        if hasattr(record, "status_code"):
            payload["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            payload["duration_ms"] = record.duration_ms
        if hasattr(record, "client_ip"):
            payload["client_ip"] = record.client_ip
        if hasattr(record, "user_id"):
            payload["user_id"] = record.user_id
        if hasattr(record, "app_env"):
            payload["app_env"] = record.app_env
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    if settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    root_logger.addHandler(handler)
