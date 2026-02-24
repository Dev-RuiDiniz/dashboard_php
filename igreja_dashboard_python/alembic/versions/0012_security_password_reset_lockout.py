"""add password reset and login protection tables

Revision ID: 0012_security_password_reset_lockout
Revises: 0011_lgpd_consent_audit_enhancements
Create Date: 2026-02-18 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.schemas import AUTH_SCHEMA, table_key


revision: str = "0012_security_password_reset_lockout"
down_revision: Union[str, None] = "0011_lgpd_consent_audit_enhancements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey(table_key(AUTH_SCHEMA, "users.id")), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("request_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        schema=AUTH_SCHEMA,
    )
    op.create_index(
        "ix_password_reset_tokens_user_id",
        "password_reset_tokens",
        ["user_id"],
        unique=False,
        schema=AUTH_SCHEMA,
    )
    op.create_index(
        "ix_password_reset_tokens_expires_at",
        "password_reset_tokens",
        ["expires_at"],
        unique=False,
        schema=AUTH_SCHEMA,
    )

    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey(table_key(AUTH_SCHEMA, "users.id")), nullable=True),
        sa.Column("identity", sa.String(length=120), nullable=False),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("attempted_at", sa.DateTime(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema=AUTH_SCHEMA,
    )
    op.create_index(
        "ix_login_attempts_user_id",
        "login_attempts",
        ["user_id"],
        unique=False,
        schema=AUTH_SCHEMA,
    )
    op.create_index(
        "ix_login_attempts_identity_ip_attempted",
        "login_attempts",
        ["identity", "ip", "attempted_at"],
        unique=False,
        schema=AUTH_SCHEMA,
    )
    op.create_index(
        "ix_login_attempts_attempted_at",
        "login_attempts",
        ["attempted_at"],
        unique=False,
        schema=AUTH_SCHEMA,
    )

    op.create_table(
        "rate_limit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("route", sa.String(length=120), nullable=False),
        sa.Column("ip", sa.String(length=64), nullable=False),
        sa.Column("window_start", sa.DateTime(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        schema=AUTH_SCHEMA,
    )
    op.create_index(
        "ix_rate_limit_events_route_ip_window",
        "rate_limit_events",
        ["route", "ip", "window_start"],
        unique=False,
        schema=AUTH_SCHEMA,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_rate_limit_events_route_ip_window",
        table_name="rate_limit_events",
        schema=AUTH_SCHEMA,
    )
    op.drop_table("rate_limit_events", schema=AUTH_SCHEMA)

    op.drop_index("ix_login_attempts_attempted_at", table_name="login_attempts", schema=AUTH_SCHEMA)
    op.drop_index(
        "ix_login_attempts_identity_ip_attempted",
        table_name="login_attempts",
        schema=AUTH_SCHEMA,
    )
    op.drop_index("ix_login_attempts_user_id", table_name="login_attempts", schema=AUTH_SCHEMA)
    op.drop_table("login_attempts", schema=AUTH_SCHEMA)

    op.drop_index(
        "ix_password_reset_tokens_expires_at",
        table_name="password_reset_tokens",
        schema=AUTH_SCHEMA,
    )
    op.drop_index(
        "ix_password_reset_tokens_user_id",
        table_name="password_reset_tokens",
        schema=AUTH_SCHEMA,
    )
    op.drop_table("password_reset_tokens", schema=AUTH_SCHEMA)
