"""move tables to postgres schemas

Revision ID: 0008_postgres_schemas
Revises: 0007_social_visits
Create Date: 2026-02-09 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "0008_postgres_schemas"
down_revision: Union[str, None] = "0007_social_visits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DOMAIN_TABLES = (
    "families",
    "dependents",
    "equipment",
    "loans",
    "food_baskets",
    "street_people",
    "street_services",
    "referrals",
    "visit_requests",
    "visit_executions",
)

AUTH_TABLES = (
    "users",
    "roles",
    "user_roles",
)


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return

    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.execute("CREATE SCHEMA IF NOT EXISTS domain")

    for table_name in AUTH_TABLES:
        op.execute(f"ALTER TABLE IF EXISTS public.{table_name} SET SCHEMA auth")

    for table_name in DOMAIN_TABLES:
        op.execute(f"ALTER TABLE IF EXISTS public.{table_name} SET SCHEMA domain")

    op.execute("ALTER TABLE IF EXISTS public.alembic_version SET SCHEMA auth")


def downgrade() -> None:
    if not _is_postgres():
        return

    for table_name in DOMAIN_TABLES:
        op.execute(f"ALTER TABLE IF EXISTS domain.{table_name} SET SCHEMA public")

    for table_name in AUTH_TABLES:
        op.execute(f"ALTER TABLE IF EXISTS auth.{table_name} SET SCHEMA public")

    op.execute("ALTER TABLE IF EXISTS auth.alembic_version SET SCHEMA public")
