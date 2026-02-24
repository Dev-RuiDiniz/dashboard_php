"""add children module and event children flag

Revision ID: 0010_children_module
Revises: 0009_delivery_events
Create Date: 2026-02-18 00:00:01.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_children_module"
down_revision: Union[str, None] = "0009_delivery_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

child_sex_enum = sa.Enum("M", "F", "O", "NI", name="childsex")


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _schema() -> str | None:
    return "domain" if _is_postgres() else None


def _fk(table: str) -> str:
    if _is_postgres():
        return f"domain.{table}.id"
    return f"{table}.id"


def upgrade() -> None:
    schema = _schema()
    child_sex_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "children",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("family_id", sa.Integer(), sa.ForeignKey(_fk("families"), ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("sex", child_sex_enum, nullable=False, server_default="NI"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_children_family_id", "children", ["family_id"], schema=schema)
    op.create_index("ix_children_birth_date", "children", ["birth_date"], schema=schema)

    op.add_column(
        "delivery_events",
        sa.Column("has_children_list", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        schema=schema,
    )


def downgrade() -> None:
    schema = _schema()

    op.drop_column("delivery_events", "has_children_list", schema=schema)

    op.drop_index("ix_children_birth_date", table_name="children", schema=schema)
    op.drop_index("ix_children_family_id", table_name="children", schema=schema)
    op.drop_table("children", schema=schema)

    child_sex_enum.drop(op.get_bind(), checkfirst=True)
