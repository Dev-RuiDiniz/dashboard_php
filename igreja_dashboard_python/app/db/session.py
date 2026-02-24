from __future__ import annotations

import logging
import os
from threading import Lock

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger("app.db")

_engine = None
_engine_url: str | None = None
_session_factory = None
_engine_error: Exception | None = None
_engine_lock = Lock()


def _resolve_database_url() -> str:
    raw_url = (os.getenv("DATABASE_URL") or settings.database_url or "").strip()
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://") and "+" not in raw_url.split("://", 1)[0]:
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


def validate_database_configuration(app_env: str | None = None) -> tuple[bool, str | None]:
    environment = (app_env or settings.app_env).strip().lower()
    database_url = _resolve_database_url()

    if environment == "production" and not database_url:
        return False, "DATABASE_URL precisa estar definido em produção."

    if environment == "production" and database_url.startswith("sqlite"):
        return False, "Produção requer PostgreSQL; SQLite não é suportado."

    if environment == "production" and database_url and not database_url.startswith("postgresql"):
        return False, "Produção requer DATABASE_URL com dialeto postgresql."

    return True, None


def _build_engine(database_url: str):
    is_sqlite = database_url.startswith("sqlite")
    is_postgres = database_url.startswith("postgresql")

    kwargs: dict[str, object] = {"future": True}
    if is_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
    elif is_postgres:
        # Em serverless evitamos manter conexões abertas entre invocações.
        kwargs["poolclass"] = NullPool
        kwargs["pool_pre_ping"] = True

    return create_engine(database_url, **kwargs)


def _ensure_engine() -> None:
    global _engine, _engine_url, _session_factory, _engine_error

    database_url = _resolve_database_url()
    if not database_url:
        _engine = None
        _engine_url = None
        _session_factory = None
        _engine_error = RuntimeError("DATABASE_URL não configurada.")
        return

    if _engine is not None and _engine_url == database_url and _session_factory is not None:
        return

    with _engine_lock:
        if _engine is not None and _engine_url == database_url and _session_factory is not None:
            return
        try:
            engine = _build_engine(database_url)
        except Exception as exc:  # noqa: BLE001
            _engine = None
            _engine_url = database_url
            _session_factory = None
            _engine_error = exc
            logger.exception(
                "Falha ao inicializar SQLAlchemy engine",
                extra={"database_url": database_url},
            )
            return

        _engine = engine
        _engine_url = database_url
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
            expire_on_commit=False,
        )
        _engine_error = None


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
    except Exception:
        # Ignore non-SQLite engines.
        pass
    finally:
        cursor.close()


def get_database_url() -> str:
    return _resolve_database_url()


def database_ready() -> bool:
    is_valid, _ = validate_database_configuration()
    if not is_valid:
        return False
    _ensure_engine()
    return _session_factory is not None


def get_engine_error() -> Exception | None:
    _ensure_engine()
    return _engine_error


def get_engine():
    _ensure_engine()
    return _engine


def get_session_factory():
    is_valid, error_message = validate_database_configuration()
    if not is_valid:
        raise RuntimeError(error_message or "Configuração inválida de banco para o ambiente.")

    _ensure_engine()
    if _session_factory is None:
        root_cause = _engine_error or RuntimeError("Engine indisponível")
        raise RuntimeError(
            "Conexão com banco indisponível ou configuração inválida."
        ) from root_cause
    return _session_factory


def SessionLocal():
    return get_session_factory()()


def AuthSessionLocal():
    return get_session_factory()()


auth_engine = get_engine
engine = get_engine
