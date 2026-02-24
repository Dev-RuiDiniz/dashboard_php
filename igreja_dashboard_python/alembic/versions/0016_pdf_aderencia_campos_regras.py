"""add fields required for client adherence audit

Revision ID: 0016_pdf_aderencia_campos_regras
Revises: 0015_monthly_closure_official_report_fields
Create Date: 2026-02-20 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0016_pdf_aderencia_campos_regras"
down_revision: Union[str, None] = "0015_monthly_closure_official_report_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


equipment_type_enum = sa.Enum(
    "Bengala",
    "Cadeira de rodas",
    "Andador",
    "Muleta",
    "Cama",
    "Outros",
    name="equipmenttype",
)

equipment_condition_enum = sa.Enum(
    "Novo",
    "Bom",
    "Precisa reparo",
    name="equipmentcondition",
)

family_benefit_status_enum = sa.Enum(
    "Apta",
    "Já beneficiada",
    "Atenção",
    name="familybenefitstatus",
)

document_status_enum = sa.Enum("Sim", "Não", "Parcial", name="documentstatus")
street_time_enum = sa.Enum(
    "Menos de 3 meses",
    "3 a 12 meses",
    "1 a 5 anos",
    "+5 anos",
    name="streettime",
)
spiritual_decision_enum = sa.Enum(
    "Reconciliação",
    "Conversão",
    "Interesse",
    "Apoio social",
    name="spiritualdecision",
)
referral_target_enum = sa.Enum(
    "CRAS",
    "CAPS",
    "UBS",
    "Documentos",
    "Trabalho",
    "Outro",
    name="referraltarget",
)


def upgrade() -> None:
    bind = op.get_bind()
    equipment_type_enum.create(bind, checkfirst=True)
    equipment_condition_enum.create(bind, checkfirst=True)
    family_benefit_status_enum.create(bind, checkfirst=True)
    document_status_enum.create(bind, checkfirst=True)
    street_time_enum.create(bind, checkfirst=True)
    spiritual_decision_enum.create(bind, checkfirst=True)
    referral_target_enum.create(bind, checkfirst=True)

    op.create_table(
        "family_workers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("family_id", sa.Integer(), sa.ForeignKey("families.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("monthly_income", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_index("ix_family_workers_family_id", "family_workers", ["family_id"])

    op.add_column("families", sa.Column("partner_name", sa.String(length=120), nullable=True))
    op.add_column("families", sa.Column("partner_cpf", sa.String(length=11), nullable=True))
    op.add_column("families", sa.Column("marital_status", sa.String(length=40), nullable=True))
    op.add_column("families", sa.Column("education_level", sa.String(length=60), nullable=True))
    op.add_column("families", sa.Column("housing_type", sa.String(length=60), nullable=True))
    op.add_column("families", sa.Column("chronic_diseases", sa.Text(), nullable=True))
    op.add_column("families", sa.Column("social_benefits", sa.Text(), nullable=True))
    op.add_column("families", sa.Column("church_attendance", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("families", sa.Column("needs_visit_alert", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("families", sa.Column("adults_count", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("families", sa.Column("workers_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("families", sa.Column("total_income", sa.Float(), nullable=False, server_default="0"))
    op.add_column("families", sa.Column("birth_certificate_present", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("families", sa.Column("birth_certificate_missing_count", sa.Integer(), nullable=False, server_default="0"))

    op.add_column("food_baskets", sa.Column("delivery_date", sa.Date(), nullable=False, server_default=sa.func.current_date()))
    op.add_column("food_baskets", sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("food_baskets", sa.Column("frequency_months", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("food_baskets", sa.Column("last_withdrawal_at", sa.Date(), nullable=True))
    op.add_column("food_baskets", sa.Column("last_withdrawal_responsible", sa.String(length=120), nullable=True))
    op.add_column("food_baskets", sa.Column("family_status", family_benefit_status_enum, nullable=False, server_default="Apta"))

    op.add_column("equipment", sa.Column("equipment_type", equipment_type_enum, nullable=False, server_default="Outros"))
    op.add_column("equipment", sa.Column("condition_status", equipment_condition_enum, nullable=False, server_default="Bom"))
    op.add_column("equipment", sa.Column("notes", sa.Text(), nullable=True))

    op.add_column("loans", sa.Column("return_condition", equipment_condition_enum, nullable=True))
    if bind.dialect.name == "sqlite":
        op.execute("UPDATE loans SET due_date = COALESCE(due_date, date(loan_date, ' +30 day'))")
    else:
        op.execute("UPDATE loans SET due_date = COALESCE(due_date, loan_date + INTERVAL '30 days')")

    op.add_column("street_people", sa.Column("documents_status", document_status_enum, nullable=False, server_default="Parcial"))
    op.add_column("street_people", sa.Column("street_time", street_time_enum, nullable=True))
    op.add_column("street_people", sa.Column("immediate_needs", sa.Text(), nullable=True))
    op.add_column("street_people", sa.Column("wants_prayer", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("street_people", sa.Column("accepts_visit", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("street_people", sa.Column("spiritual_decision", spiritual_decision_enum, nullable=True))
    op.add_column("street_people", sa.Column("consent_signature_name", sa.String(length=120), nullable=True))

    op.add_column("referrals", sa.Column("target", referral_target_enum, nullable=False, server_default="Outro"))


def downgrade() -> None:
    op.drop_column("referrals", "target")

    op.drop_column("street_people", "consent_signature_name")
    op.drop_column("street_people", "spiritual_decision")
    op.drop_column("street_people", "accepts_visit")
    op.drop_column("street_people", "wants_prayer")
    op.drop_column("street_people", "immediate_needs")
    op.drop_column("street_people", "street_time")
    op.drop_column("street_people", "documents_status")

    op.drop_column("loans", "return_condition")
    op.drop_column("equipment", "notes")
    op.drop_column("equipment", "condition_status")
    op.drop_column("equipment", "equipment_type")

    op.drop_column("food_baskets", "family_status")
    op.drop_column("food_baskets", "last_withdrawal_responsible")
    op.drop_column("food_baskets", "last_withdrawal_at")
    op.drop_column("food_baskets", "frequency_months")
    op.drop_column("food_baskets", "quantity")
    op.drop_column("food_baskets", "delivery_date")

    op.drop_column("families", "birth_certificate_missing_count")
    op.drop_column("families", "birth_certificate_present")
    op.drop_column("families", "total_income")
    op.drop_column("families", "workers_count")
    op.drop_column("families", "adults_count")
    op.drop_column("families", "needs_visit_alert")
    op.drop_column("families", "church_attendance")
    op.drop_column("families", "social_benefits")
    op.drop_column("families", "chronic_diseases")
    op.drop_column("families", "housing_type")
    op.drop_column("families", "education_level")
    op.drop_column("families", "marital_status")
    op.drop_column("families", "partner_cpf")
    op.drop_column("families", "partner_name")

    op.drop_index("ix_family_workers_family_id", table_name="family_workers")
    op.drop_table("family_workers")

    bind = op.get_bind()
    referral_target_enum.drop(bind, checkfirst=True)
    spiritual_decision_enum.drop(bind, checkfirst=True)
    street_time_enum.drop(bind, checkfirst=True)
    document_status_enum.drop(bind, checkfirst=True)
    family_benefit_status_enum.drop(bind, checkfirst=True)
    equipment_condition_enum.drop(bind, checkfirst=True)
    equipment_type_enum.drop(bind, checkfirst=True)
