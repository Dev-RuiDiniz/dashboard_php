"""add lgpd consent and audit payloads

Revision ID: 0011_lgpd_consent_audit_enhancements
Revises: 0010_children_module
Create Date: 2026-02-18 00:00:02.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011_lgpd_consent_audit_enhancements"
down_revision: Union[str, None] = "0010_children_module"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _schema() -> str | None:
    return "domain" if _is_postgres() else None


def upgrade() -> None:
    schema = _schema()

    op.add_column("families", sa.Column("consent_term_version", sa.String(length=40), nullable=True), schema=schema)
    op.add_column("families", sa.Column("consent_accepted_at", sa.DateTime(), nullable=True), schema=schema)
    op.add_column("families", sa.Column("consent_accepted_by_user_id", sa.Integer(), nullable=True), schema=schema)
    op.add_column(
        "families",
        sa.Column("consent_accepted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        schema=schema,
    )

    op.add_column("street_people", sa.Column("consent_term_version", sa.String(length=40), nullable=True), schema=schema)
    op.add_column("street_people", sa.Column("consent_accepted_at", sa.DateTime(), nullable=True), schema=schema)
    op.add_column("street_people", sa.Column("consent_accepted_by_user_id", sa.Integer(), nullable=True), schema=schema)
    op.add_column(
        "street_people",
        sa.Column("consent_accepted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        schema=schema,
    )

    op.add_column("visit_requests", sa.Column("consent_term_version", sa.String(length=40), nullable=True), schema=schema)
    op.add_column("visit_requests", sa.Column("consent_accepted_at", sa.DateTime(), nullable=True), schema=schema)
    op.add_column("visit_requests", sa.Column("consent_accepted_by_user_id", sa.Integer(), nullable=True), schema=schema)
    op.add_column(
        "visit_requests",
        sa.Column("consent_accepted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        schema=schema,
    )

    op.create_table(
        "consent_terms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version", sa.String(length=40), nullable=False, unique=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_consent_terms_active", "consent_terms", ["active"], schema=schema)

    op.add_column("audit_logs", sa.Column("before_json", sa.JSON(), nullable=True), schema=schema)
    op.add_column("audit_logs", sa.Column("after_json", sa.JSON(), nullable=True), schema=schema)
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity"], schema=schema)
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"], schema=schema)
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], schema=schema)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], schema=schema)


def downgrade() -> None:
    schema = _schema()

    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs", schema=schema)
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs", schema=schema)
    op.drop_index("ix_audit_logs_entity_id", table_name="audit_logs", schema=schema)
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs", schema=schema)
    op.drop_column("audit_logs", "after_json", schema=schema)
    op.drop_column("audit_logs", "before_json", schema=schema)

    op.drop_index("ix_consent_terms_active", table_name="consent_terms", schema=schema)
    op.drop_table("consent_terms", schema=schema)

    for table in ("visit_requests", "street_people", "families"):
        op.drop_column(table, "consent_accepted", schema=schema)
        op.drop_column(table, "consent_accepted_by_user_id", schema=schema)
        op.drop_column(table, "consent_accepted_at", schema=schema)
        op.drop_column(table, "consent_term_version", schema=schema)
