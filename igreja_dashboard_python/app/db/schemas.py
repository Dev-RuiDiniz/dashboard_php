from __future__ import annotations

from app.core.config import settings

USE_SCHEMAS = not settings.database_url.startswith("sqlite")

AUTH_SCHEMA = "auth" if USE_SCHEMAS else None
DOMAIN_SCHEMA = "domain" if USE_SCHEMAS else None


def table_key(schema: str | None, table: str) -> str:
    return f"{schema}.{table}" if schema else table


def schema_kwargs(schema: str | None) -> dict[str, str]:
    return {"schema": schema} if schema else {}
