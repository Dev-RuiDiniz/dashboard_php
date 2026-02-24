"""add system settings for eligibility engine

Revision ID: 0013_system_settings_eligibility
Revises: 0012_security_password_reset_lockout
Create Date: 2026-02-18 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.schemas import DOMAIN_SCHEMA, table_key


revision: str = "0013_system_settings_eligibility"
down_revision: Union[str, None] = "0012_security_password_reset_lockout"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("delivery_month_limit", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "min_months_since_last_delivery",
            sa.Integer(),
            nullable=False,
            server_default="2",
        ),
        sa.Column("min_vulnerability_level", sa.Integer(), nullable=False, server_default="2"),
        sa.Column(
            "require_documentation_complete",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=DOMAIN_SCHEMA,
    )

    system_settings_table = table_key(DOMAIN_SCHEMA, "system_settings")
    op.execute(
        sa.text(
            f"""
            INSERT INTO {system_settings_table}
            (id, delivery_month_limit, min_months_since_last_delivery, min_vulnerability_level, require_documentation_complete)
            VALUES (1, 1, 2, 2, :require_docs)
            """
        ).bindparams(require_docs=True)
    )


def downgrade() -> None:
    op.drop_table("system_settings", schema=DOMAIN_SCHEMA)
