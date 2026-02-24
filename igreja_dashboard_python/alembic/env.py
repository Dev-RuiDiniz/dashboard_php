from __future__ import annotations

import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, inspect, pool
from sqlalchemy.engine import make_url

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402
from app.db.auth_base import AuthBase  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.schemas import AUTH_SCHEMA  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = os.getenv("DATABASE_URL") or settings.database_url
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = [Base.metadata, AuthBase.metadata]


def _compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):  # type: ignore[no-untyped-def]
    if context.dialect.name == "sqlite":
        return False
    return None


def _compare_server_default(context, inspected_column, metadata_column, inspected_default, metadata_default, rendered_metadata_default):  # type: ignore[no-untyped-def]
    if context.dialect.name == "sqlite":
        return False
    return None


def _configure_context_kwargs(
    version_table_schema: str | None = None,
    render_as_batch: bool = False,
    include_schemas: bool = False,
) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "target_metadata": target_metadata,
        "include_schemas": include_schemas,
        "compare_type": _compare_type,
        "compare_server_default": _compare_server_default,
        "render_as_batch": render_as_batch,
    }
    if version_table_schema:
        kwargs["version_table_schema"] = version_table_schema
    return kwargs


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    dialect_name = make_url(url).get_backend_name()
    context.configure(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_configure_context_kwargs(
            render_as_batch=dialect_name == "sqlite",
            include_schemas=dialect_name == "postgresql",
        ),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        inspector = inspect(connection)
        version_schema = None
        render_as_batch = connection.dialect.name == "sqlite"
        include_schemas = connection.dialect.name == "postgresql"
        if include_schemas:
            has_auth_schema = AUTH_SCHEMA in inspector.get_schema_names()
            public_has_version = inspector.has_table("alembic_version", schema="public")
            auth_has_version = inspector.has_table("alembic_version", schema=AUTH_SCHEMA)
            if auth_has_version or (has_auth_schema and not public_has_version):
                version_schema = AUTH_SCHEMA

        context.configure(
            connection=connection,
            **_configure_context_kwargs(
                version_schema,
                render_as_batch=render_as_batch,
                include_schemas=include_schemas,
            ),
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
