"""create families and dependents tables

Revision ID: 0003_family_dependent
Revises: 0002_auth_rbac
Create Date: 2025-02-12 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_family_dependent"
down_revision: Union[str, None] = "0002_auth_rbac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


vulnerability_enum = sa.Enum(
    "Sem vulnerabilidade",
    "Baixa",
    "Média",
    "Alta",
    "Extrema",
    name="vulnerabilityenum",
)


def upgrade() -> None:
    vulnerability_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "families",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("responsible_name", sa.String(length=120), nullable=False),
        sa.Column("responsible_cpf", sa.String(length=11), nullable=False, unique=True),
        sa.Column("responsible_rg", sa.String(length=30), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("cep", sa.String(length=12), nullable=True),
        sa.Column("street", sa.String(length=120), nullable=True),
        sa.Column("number", sa.String(length=20), nullable=True),
        sa.Column("complement", sa.String(length=80), nullable=True),
        sa.Column("neighborhood", sa.String(length=80), nullable=True),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("socioeconomic_profile", sa.Text(), nullable=True),
        sa.Column("documentation_status", sa.Text(), nullable=True),
        sa.Column("vulnerability", vulnerability_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "dependents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("family_id", sa.Integer(), sa.ForeignKey("families.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("cpf", sa.String(length=11), nullable=True, unique=True),
        sa.Column("relationship", sa.String(length=80), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("income", sa.Float(), nullable=True),
        sa.Column("benefits", sa.Text(), nullable=True),
    )
    op.create_index("ix_families_responsible_name", "families", ["responsible_name"])
    op.create_index("ix_families_neighborhood", "families", ["neighborhood"])
    op.create_index("ix_families_vulnerability", "families", ["vulnerability"])
    op.create_index("ix_dependents_family_id", "dependents", ["family_id"])


def downgrade() -> None:
    op.drop_index("ix_dependents_family_id", table_name="dependents")
    op.drop_index("ix_families_vulnerability", table_name="families")
    op.drop_index("ix_families_neighborhood", table_name="families")
    op.drop_index("ix_families_responsible_name", table_name="families")
    op.drop_table("dependents")
    op.drop_table("families")
    vulnerability_enum.drop(op.get_bind(), checkfirst=True)
