"""create street people domain

Revision ID: 0006_street_domain
Revises: 0005_food_baskets
Create Date: 2025-02-13 00:00:02.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_street_domain"
down_revision: Union[str, None] = "0005_food_baskets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


referral_status_enum = sa.Enum(
    "Encaminhado",
    "Em acompanhamento",
    "Concluído",
    "Interrompido",
    name="referralstatus",
)


def upgrade() -> None:
    referral_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "street_people",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("cpf", sa.String(length=11), nullable=True),
        sa.Column("rg", sa.String(length=30), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("approximate_age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("reference_location", sa.String(length=140), nullable=False),
        sa.Column("benefit_notes", sa.Text(), nullable=True),
        sa.Column("general_notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("cpf"),
    )
    op.create_index("ix_street_people_reference_location", "street_people", ["reference_location"])

    op.create_table(
        "street_services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("street_people.id"), nullable=False),
        sa.Column("service_type", sa.String(length=80), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("responsible_name", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_street_services_person_date", "street_services", ["person_id", "service_date"])
    op.create_index("ix_street_services_type", "street_services", ["service_type"])

    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("street_people.id"), nullable=False),
        sa.Column("recovery_home", sa.String(length=160), nullable=False),
        sa.Column("referral_date", sa.Date(), nullable=False),
        sa.Column("status", referral_status_enum, nullable=False, server_default="Encaminhado"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_referrals_person_status", "referrals", ["person_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_referrals_person_status", table_name="referrals")
    op.drop_table("referrals")

    op.drop_index("ix_street_services_type", table_name="street_services")
    op.drop_index("ix_street_services_person_date", table_name="street_services")
    op.drop_table("street_services")

    op.drop_index("ix_street_people_reference_location", table_name="street_people")
    op.drop_table("street_people")

    referral_status_enum.drop(op.get_bind(), checkfirst=True)
