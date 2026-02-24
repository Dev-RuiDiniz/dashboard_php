from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.schemas import DOMAIN_SCHEMA, schema_kwargs, table_key


def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class VulnerabilityLevel(str, Enum):
    NONE = "Sem vulnerabilidade"
    LOW = "Baixa"
    MEDIUM = "Média"
    HIGH = "Alta"
    EXTREME = "Extrema"


class FamilyBenefitStatus(str, Enum):
    ELIGIBLE = "Apta"
    ALREADY_BENEFITED = "Já beneficiada"
    ATTENTION = "Atenção"


class Family(Base):
    __tablename__ = "families"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    responsible_name: Mapped[str] = mapped_column(String(120), nullable=False)
    responsible_cpf: Mapped[str] = mapped_column(String(11), unique=True, nullable=False)
    responsible_rg: Mapped[str | None] = mapped_column(String(30))
    partner_name: Mapped[str | None] = mapped_column(String(120))
    partner_cpf: Mapped[str | None] = mapped_column(String(11))
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    marital_status: Mapped[str | None] = mapped_column(String(40))
    education_level: Mapped[str | None] = mapped_column(String(60))
    housing_type: Mapped[str | None] = mapped_column(String(60))
    chronic_diseases: Mapped[str | None] = mapped_column(Text)
    social_benefits: Mapped[str | None] = mapped_column(Text)
    church_attendance: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    needs_visit_alert: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    adults_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    workers_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_income: Mapped[float] = mapped_column(Float, nullable=False, default=0, server_default="0")
    birth_certificate_present: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    birth_certificate_missing_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    cep: Mapped[str | None] = mapped_column(String(12))
    street: Mapped[str | None] = mapped_column(String(120))
    number: Mapped[str | None] = mapped_column(String(20))
    complement: Mapped[str | None] = mapped_column(String(80))
    neighborhood: Mapped[str | None] = mapped_column(String(80))
    city: Mapped[str | None] = mapped_column(String(80))
    state: Mapped[str | None] = mapped_column(String(2))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    socioeconomic_profile: Mapped[str | None] = mapped_column(Text)
    documentation_status: Mapped[str | None] = mapped_column(Text)
    vulnerability: Mapped[VulnerabilityLevel] = mapped_column(
        SqlEnum(
            VulnerabilityLevel,
            name="vulnerabilityenum",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    consent_term_version: Mapped[str | None] = mapped_column(String(40))
    consent_accepted_at: Mapped[datetime | None] = mapped_column(DateTime)
    consent_accepted_by_user_id: Mapped[int | None] = mapped_column(Integer)
    consent_accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )

    dependents: Mapped[list[Dependent]] = relationship(
        "Dependent", back_populates="family", cascade="all, delete-orphan"
    )
    workers: Mapped[list[FamilyWorker]] = relationship(
        "FamilyWorker",
        back_populates="family",
        cascade="all, delete-orphan",
        order_by="FamilyWorker.id",
    )
    children: Mapped[list[Child]] = relationship(
        "Child", back_populates="family", cascade="all, delete-orphan"
    )
    loans: Mapped[list[Loan]] = relationship(
        "Loan",
        back_populates="family",
        cascade="all, delete-orphan",
        order_by="desc(Loan.loan_date)",
    )
    food_baskets: Mapped[list[FoodBasket]] = relationship(
        "FoodBasket",
        back_populates="family",
        cascade="all, delete-orphan",
        order_by="desc(FoodBasket.reference_year), desc(FoodBasket.reference_month)",
    )
    visit_requests: Mapped[list[VisitRequest]] = relationship(
        "VisitRequest",
        back_populates="family",
        cascade="all, delete-orphan",
        order_by="desc(VisitRequest.scheduled_date), desc(VisitRequest.created_at)",
    )


class Dependent(Base):
    __tablename__ = "dependents"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey(table_key(DOMAIN_SCHEMA, "families.id")), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    cpf: Mapped[str | None] = mapped_column(String(11), unique=True)
    relationship_type: Mapped[str] = mapped_column("relationship", String(80), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    income: Mapped[float | None] = mapped_column(Float)
    benefits: Mapped[str | None] = mapped_column(Text)

    family: Mapped[Family] = relationship("Family", back_populates="dependents")


class FamilyWorker(Base):
    __tablename__ = "family_workers"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey(table_key(DOMAIN_SCHEMA, "families.id"), ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    monthly_income: Mapped[float] = mapped_column(Float, nullable=False, default=0, server_default="0")

    family: Mapped[Family] = relationship("Family", back_populates="workers")


class ChildSex(str, Enum):
    M = "M"
    F = "F"
    O = "O"  # noqa: E741
    NI = "NI"


class Child(Base):
    __tablename__ = "children"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey(table_key(DOMAIN_SCHEMA, "families.id"), ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    sex: Mapped[ChildSex] = mapped_column(
        SqlEnum(
            ChildSex,
            name="childsex",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=ChildSex.NI,
        server_default="NI",
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )

    family: Mapped[Family] = relationship("Family", back_populates="children")


class FoodBasketStatus(str, Enum):
    DELIVERED = "Entregue"
    PENDING = "Pendente"
    CANCELED = "Cancelada"


class FoodBasket(Base):
    __tablename__ = "food_baskets"
    __table_args__ = (
        UniqueConstraint(
            "family_id", "reference_year", "reference_month", name="uq_food_basket_family_month"
        ),
        schema_kwargs(DOMAIN_SCHEMA),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey(table_key(DOMAIN_SCHEMA, "families.id")), nullable=False
    )
    reference_year: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_month: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[FoodBasketStatus] = mapped_column(
        SqlEnum(
            FoodBasketStatus,
            name="foodbasketstatus",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=FoodBasketStatus.DELIVERED,
        server_default="Entregue",
    )
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    frequency_months: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    last_withdrawal_at: Mapped[date | None] = mapped_column(Date)
    last_withdrawal_responsible: Mapped[str | None] = mapped_column(String(120))
    family_status: Mapped[FamilyBenefitStatus] = mapped_column(
        SqlEnum(
            FamilyBenefitStatus,
            name="familybenefitstatus",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=FamilyBenefitStatus.ELIGIBLE,
        server_default="Apta",
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )

    family: Mapped[Family] = relationship("Family", back_populates="food_baskets")


class VisitRequestStatus(str, Enum):
    PENDING = "Pendente"
    COMPLETED = "Concluída"
    CANCELED = "Cancelada"


class VisitExecutionResult(str, Enum):
    COMPLETED = "Concluída"
    PARTIAL = "Parcial"
    NOT_COMPLETED = "Não concluída"


class VisitRequest(Base):
    __tablename__ = "visit_requests"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey(table_key(DOMAIN_SCHEMA, "families.id")), nullable=False
    )
    requested_by_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[VisitRequestStatus] = mapped_column(
        SqlEnum(
            VisitRequestStatus,
            name="visitrequeststatus",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=VisitRequestStatus.PENDING,
        server_default="Pendente",
    )
    request_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    consent_term_version: Mapped[str | None] = mapped_column(String(40))
    consent_accepted_at: Mapped[datetime | None] = mapped_column(DateTime)
    consent_accepted_by_user_id: Mapped[int | None] = mapped_column(Integer)
    consent_accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )

    family: Mapped[Family] = relationship("Family", back_populates="visit_requests")
    execution: Mapped[VisitExecution | None] = relationship(
        "VisitExecution", back_populates="request", uselist=False, cascade="all, delete-orphan"
    )


class VisitExecution(Base):
    __tablename__ = "visit_executions"
    __table_args__ = (
        UniqueConstraint("visit_request_id", name="uq_visit_execution_request"),
        schema_kwargs(DOMAIN_SCHEMA),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    visit_request_id: Mapped[int] = mapped_column(
        ForeignKey(table_key(DOMAIN_SCHEMA, "visit_requests.id")), nullable=False
    )
    executed_by_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    executed_at: Mapped[date] = mapped_column(Date, nullable=False)
    result: Mapped[VisitExecutionResult] = mapped_column(
        SqlEnum(
            VisitExecutionResult,
            name="visitexecutionresult",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=VisitExecutionResult.COMPLETED,
        server_default="Concluída",
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )

    request: Mapped[VisitRequest] = relationship("VisitRequest", back_populates="execution")


Index("ix_families_responsible_name", Family.responsible_name)
Index("ix_families_neighborhood", Family.neighborhood)
Index("ix_families_vulnerability", Family.vulnerability)
Index("ix_dependents_family_id", Dependent.family_id)
Index("ix_family_workers_family_id", FamilyWorker.family_id)
Index("ix_children_family_id", Child.family_id)
Index("ix_children_birth_date", Child.birth_date)
Index("ix_food_baskets_family_id", FoodBasket.family_id)
Index("ix_food_baskets_reference_period", FoodBasket.reference_year, FoodBasket.reference_month)
Index("ix_food_baskets_status", FoodBasket.status)
Index("ix_visit_requests_family_status", VisitRequest.family_id, VisitRequest.status)
Index("ix_visit_requests_scheduled_date", VisitRequest.scheduled_date)

from app.models.equipment import Loan  # noqa: E402  # isort: skip
