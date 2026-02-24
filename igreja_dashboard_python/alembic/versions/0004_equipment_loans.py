"""create equipment and loans tables

Revision ID: 0004_equipment_loans
Revises: 0003_family_dependent
Create Date: 2025-02-12 00:00:01.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_equipment_loans"
down_revision: Union[str, None] = "0003_family_dependent"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


equipment_status_enum = sa.Enum(
    "Disponível",
    "Emprestado",
    "Indisponível",
    name="equipmentstatus",
)

loan_status_enum = sa.Enum(
    "Ativo",
    "Devolvido",
    name="loanstatus",
)


def upgrade() -> None:
    equipment_status_enum.create(op.get_bind(), checkfirst=True)
    loan_status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=20), nullable=False, unique=True),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("status", equipment_status_enum, nullable=False, server_default="Disponível"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "loans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("equipment_id", sa.Integer(), sa.ForeignKey("equipment.id"), nullable=False),
        sa.Column("family_id", sa.Integer(), sa.ForeignKey("families.id"), nullable=False),
        sa.Column("loan_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", loan_status_enum, nullable=False, server_default="Ativo"),
        sa.Column("returned_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_equipment_code", "equipment", ["code"])
    op.create_index("ix_loans_family_id", "loans", ["family_id"])
    op.create_index("ix_loans_equipment_id", "loans", ["equipment_id"])
    op.create_index("ix_loans_status", "loans", ["status"])


def downgrade() -> None:
    op.drop_index("ix_loans_status", table_name="loans")
    op.drop_index("ix_loans_equipment_id", table_name="loans")
    op.drop_index("ix_loans_family_id", table_name="loans")
    op.drop_index("ix_equipment_code", table_name="equipment")
    op.drop_table("loans")
    op.drop_table("equipment")
    loan_status_enum.drop(op.get_bind(), checkfirst=True)
    equipment_status_enum.drop(op.get_bind(), checkfirst=True)
