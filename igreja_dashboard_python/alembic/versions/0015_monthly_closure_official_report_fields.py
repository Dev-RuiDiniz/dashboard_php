"""add official monthly report fields to closures

Revision ID: 0015_monthly_closure_official_report_fields
Revises: 0014_monthly_closures
Create Date: 2026-02-18 00:00:01.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.schemas import AUTH_SCHEMA, DOMAIN_SCHEMA, table_key


revision: str = "0015_monthly_closure_official_report_fields"
down_revision: Union[str, None] = "0014_monthly_closures"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("monthly_closures", schema=DOMAIN_SCHEMA) as batch_op:
        batch_op.add_column(sa.Column("official_pdf_path", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("official_pdf_sha256", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("official_snapshot_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("official_signed_by_user_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("official_signed_at", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            "fk_monthly_closures_official_signed_by_user_id",
            table_key(AUTH_SCHEMA, "users"),
            ["official_signed_by_user_id"],
            ["id"],
        )
        batch_op.create_check_constraint(
            "ck_monthly_closures_official_sha256_len",
            "official_pdf_sha256 IS NULL OR length(official_pdf_sha256) = 64",
        )
        batch_op.create_check_constraint(
            "ck_monthly_closures_official_pdf_path_required",
            "official_pdf_sha256 IS NULL OR official_pdf_path IS NOT NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("monthly_closures", schema=DOMAIN_SCHEMA) as batch_op:
        batch_op.drop_constraint("ck_monthly_closures_official_pdf_path_required", type_="check")
        batch_op.drop_constraint("ck_monthly_closures_official_sha256_len", type_="check")
        batch_op.drop_constraint("fk_monthly_closures_official_signed_by_user_id", type_="foreignkey")
        batch_op.drop_column("official_signed_at")
        batch_op.drop_column("official_signed_by_user_id")
        batch_op.drop_column("official_snapshot_json")
        batch_op.drop_column("official_pdf_sha256")
        batch_op.drop_column("official_pdf_path")
