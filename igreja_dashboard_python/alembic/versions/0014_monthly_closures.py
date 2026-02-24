"""add monthly closures table

Revision ID: 0014_monthly_closures
Revises: 0013_system_settings_eligibility
Create Date: 2026-02-18 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.schemas import AUTH_SCHEMA, DOMAIN_SCHEMA, table_key


revision: str = "0014_monthly_closures"
down_revision: Union[str, None] = "0013_system_settings_eligibility"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monthly_closures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("closed_by_user_id", sa.Integer(), sa.ForeignKey(table_key(AUTH_SCHEMA, "users.id")), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("summary_snapshot_json", sa.JSON(), nullable=True),
        sa.Column("pdf_report_path", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="OPEN"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("month BETWEEN 1 AND 12", name="ck_monthly_closures_month_range"),
        sa.UniqueConstraint("month", "year", name="uq_monthly_closures_month_year"),
        schema=DOMAIN_SCHEMA,
    )
    op.create_index(
        "ix_monthly_closures_year_month",
        table_name="monthly_closures",
        columns=["year", "month"],
        schema=DOMAIN_SCHEMA,
    )
    op.create_index(
        "ix_monthly_closures_status",
        table_name="monthly_closures",
        columns=["status"],
        schema=DOMAIN_SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_monthly_closures_status", table_name="monthly_closures", schema=DOMAIN_SCHEMA)
    op.drop_index("ix_monthly_closures_year_month", table_name="monthly_closures", schema=DOMAIN_SCHEMA)
    op.drop_table("monthly_closures", schema=DOMAIN_SCHEMA)
