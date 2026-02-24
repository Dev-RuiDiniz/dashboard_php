"""create social visits domain

Revision ID: 0007_social_visits
Revises: 0006_street_domain
Create Date: 2025-02-13 00:00:03.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_social_visits"
down_revision: Union[str, None] = "0006_street_domain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


visit_request_status_enum = sa.Enum(
    "Pendente",
    "Concluída",
    "Cancelada",
    name="visitrequeststatus",
)

visit_execution_result_enum = sa.Enum(
    "Concluída",
    "Parcial",
    "Não concluída",
    name="visitexecutionresult",
)


def upgrade() -> None:
    visit_request_status_enum.create(op.get_bind(), checkfirst=True)
    visit_execution_result_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "visit_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("family_id", sa.Integer(), sa.ForeignKey("families.id"), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("status", visit_request_status_enum, nullable=False, server_default="Pendente"),
        sa.Column("request_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_visit_requests_family_status", "visit_requests", ["family_id", "status"])
    op.create_index("ix_visit_requests_scheduled_date", "visit_requests", ["scheduled_date"])

    op.create_table(
        "visit_executions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("visit_request_id", sa.Integer(), sa.ForeignKey("visit_requests.id"), nullable=False),
        sa.Column("executed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("executed_at", sa.Date(), nullable=False),
        sa.Column("result", visit_execution_result_enum, nullable=False, server_default="Concluída"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("visit_request_id", name="uq_visit_execution_request"),
    )


def downgrade() -> None:
    op.drop_table("visit_executions")
    op.drop_index("ix_visit_requests_scheduled_date", table_name="visit_requests")
    op.drop_index("ix_visit_requests_family_status", table_name="visit_requests")
    op.drop_table("visit_requests")

    visit_execution_result_enum.drop(op.get_bind(), checkfirst=True)
    visit_request_status_enum.drop(op.get_bind(), checkfirst=True)
