from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any

from app.models import AuditLog

SENSITIVE_KEYS = {"password", "hashed_password", "token", "access_token", "refresh_token"}


def _mask_cpf(value: str) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if len(digits) != 11:
        return value
    return f"***.***.***-{digits[-2:]}"


def _serialize_scalar(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def sanitize_payload(payload: Any) -> Any:
    if payload is None:
        return None
    if is_dataclass(payload):
        payload = asdict(payload)
    if hasattr(payload, "__dict__") and not isinstance(payload, dict):
        payload = {
            key: val
            for key, val in vars(payload).items()
            if not key.startswith("_")
        }
    if isinstance(payload, dict):
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            lowered = key.lower()
            if lowered in SENSITIVE_KEYS or "senha" in lowered:
                continue
            if "cpf" in lowered and isinstance(value, str):
                sanitized[key] = _mask_cpf(value)
                continue
            sanitized[key] = sanitize_payload(value)
        return sanitized
    if isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]
    if isinstance(payload, tuple):
        return [sanitize_payload(item) for item in payload]
    return _serialize_scalar(payload)


def log_action(
    db_session,
    user_id: int,
    action: str,
    entity: str,
    entity_id: int,
    before: Any = None,
    after: Any = None,
) -> None:
    db_session.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            before_json=sanitize_payload(before),
            after_json=sanitize_payload(after),
        )
    )
