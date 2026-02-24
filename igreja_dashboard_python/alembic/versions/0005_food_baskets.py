"""create food baskets table

Revision ID: 0005_food_baskets
Revises: 0004_equipment_loans
Create Date: 2025-02-13 00:00:01.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_food_baskets"
down_revision: Union[str, None] = "0004_equipment_loans"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


food_basket_status_enum = sa.Enum(
    "Entregue",
    "Pendente",
    "Cancelada",
    name="foodbasketstatus",
)


def upgrade() -> None:
    food_basket_status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "food_baskets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("family_id", sa.Integer(), sa.ForeignKey("families.id"), nullable=False),
        sa.Column("reference_year", sa.Integer(), nullable=False),
        sa.Column("reference_month", sa.Integer(), nullable=False),
        sa.Column("status", food_basket_status_enum, nullable=False, server_default="Entregue"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("family_id", "reference_year", "reference_month", name="uq_food_basket_family_month"),
    )
    op.create_index("ix_food_baskets_family_id", "food_baskets", ["family_id"])
    op.create_index("ix_food_baskets_reference_period", "food_baskets", ["reference_year", "reference_month"])
    op.create_index("ix_food_baskets_status", "food_baskets", ["status"])


def downgrade() -> None:
    op.drop_index("ix_food_baskets_status", table_name="food_baskets")
    op.drop_index("ix_food_baskets_reference_period", table_name="food_baskets")
    op.drop_index("ix_food_baskets_family_id", table_name="food_baskets")
    op.drop_table("food_baskets")
    food_basket_status_enum.drop(op.get_bind(), checkfirst=True)
