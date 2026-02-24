"""create delivery events module

Revision ID: 0009_delivery_events
Revises: 0008_postgres_schemas
Create Date: 2026-02-18 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_delivery_events"
down_revision: Union[str, None] = "0008_postgres_schemas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


delivery_event_status_enum = sa.Enum("OPEN", "CLOSED", name="deliveryeventstatus")
delivery_invite_status_enum = sa.Enum("INVITED", "WITHDRAWN", "NO_SHOW", name="deliveryinvitestatus")


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _schema() -> str | None:
    return "domain" if _is_postgres() else None


def _fk(table: str) -> str:
    if _is_postgres():
        if table == "users":
            return "auth.users.id"
        return f"domain.{table}.id"
    return f"{table}.id"


def upgrade() -> None:
    schema = _schema()
    delivery_event_status_enum.create(op.get_bind(), checkfirst=True)
    delivery_invite_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "delivery_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("status", delivery_event_status_enum, nullable=False, server_default="OPEN"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_delivery_events_date_status", "delivery_events", ["event_date", "status"], schema=schema)
    op.create_index("ix_delivery_events_created_by", "delivery_events", ["created_by_user_id"], schema=schema)

    op.create_table(
        "delivery_invites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey(_fk("delivery_events")), nullable=False),
        sa.Column("family_id", sa.Integer(), sa.ForeignKey(_fk("families")), nullable=False),
        sa.Column("withdrawal_code", sa.String(length=6), nullable=False),
        sa.Column("invited_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("status", delivery_invite_status_enum, nullable=False, server_default="INVITED"),
        sa.UniqueConstraint("event_id", "family_id", name="uq_delivery_invites_event_family"),
        schema=schema,
    )
    op.create_index("ix_delivery_invites_event_status", "delivery_invites", ["event_id", "status"], schema=schema)
    op.create_index(
        "ix_delivery_invites_event_code",
        "delivery_invites",
        ["event_id", "withdrawal_code"],
        unique=True,
        schema=schema,
    )
    op.create_index("ix_delivery_invites_family_id", "delivery_invites", ["family_id"], schema=schema)

    op.create_table(
        "delivery_withdrawals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey(_fk("delivery_events")), nullable=False),
        sa.Column("family_id", sa.Integer(), sa.ForeignKey(_fk("families")), nullable=False),
        sa.Column("confirmed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("signature_name", sa.String(length=120), nullable=False),
        sa.Column("signature_accepted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("event_id", "family_id", name="uq_delivery_withdrawals_event_family"),
        schema=schema,
    )
    op.create_index(
        "ix_delivery_withdrawals_event_family",
        "delivery_withdrawals",
        ["event_id", "family_id"],
        schema=schema,
    )
    op.create_index(
        "ix_delivery_withdrawals_confirmed_by",
        "delivery_withdrawals",
        ["confirmed_by_user_id"],
        schema=schema,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index(
        "ix_audit_logs_entity_created",
        "audit_logs",
        ["entity", "entity_id", "created_at"],
        schema=schema,
    )
    op.create_index(
        "ix_audit_logs_user_created",
        "audit_logs",
        ["user_id", "created_at"],
        schema=schema,
    )


def downgrade() -> None:
    schema = _schema()

    op.drop_index("ix_audit_logs_user_created", table_name="audit_logs", schema=schema)
    op.drop_index("ix_audit_logs_entity_created", table_name="audit_logs", schema=schema)
    op.drop_table("audit_logs", schema=schema)

    op.drop_index("ix_delivery_withdrawals_confirmed_by", table_name="delivery_withdrawals", schema=schema)
    op.drop_index("ix_delivery_withdrawals_event_family", table_name="delivery_withdrawals", schema=schema)
    op.drop_table("delivery_withdrawals", schema=schema)

    op.drop_index("ix_delivery_invites_family_id", table_name="delivery_invites", schema=schema)
    op.drop_index("ix_delivery_invites_event_code", table_name="delivery_invites", schema=schema)
    op.drop_index("ix_delivery_invites_event_status", table_name="delivery_invites", schema=schema)
    op.drop_table("delivery_invites", schema=schema)

    op.drop_index("ix_delivery_events_created_by", table_name="delivery_events", schema=schema)
    op.drop_index("ix_delivery_events_date_status", table_name="delivery_events", schema=schema)
    op.drop_table("delivery_events", schema=schema)

    delivery_invite_status_enum.drop(op.get_bind(), checkfirst=True)
    delivery_event_status_enum.drop(op.get_bind(), checkfirst=True)
