from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SqlEnum, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.schemas import DOMAIN_SCHEMA, schema_kwargs, table_key




def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class DocumentStatus(str, Enum):
    YES = "Sim"
    NO = "Não"
    PARTIAL = "Parcial"


class StreetTime(str, Enum):
    LT_3M = "Menos de 3 meses"
    M3_12 = "3 a 12 meses"
    Y1_5 = "1 a 5 anos"
    GT_5Y = "+5 anos"


class SpiritualDecision(str, Enum):
    RECONCILIATION = "Reconciliação"
    CONVERSION = "Conversão"
    INTEREST = "Interesse"
    SOCIAL_SUPPORT = "Apoio social"


class ReferralTarget(str, Enum):
    CRAS = "CRAS"
    CAPS = "CAPS"
    UBS = "UBS"
    DOCUMENTS = "Documentos"
    JOB = "Trabalho"
    OTHER = "Outro"


class ReferralStatus(str, Enum):
    REFERRED = "Encaminhado"
    FOLLOW_UP = "Em acompanhamento"
    COMPLETED = "Concluído"
    INTERRUPTED = "Interrompido"


class StreetPerson(Base):
    __tablename__ = "street_people"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(120))
    cpf: Mapped[str | None] = mapped_column(String(11), unique=True)
    rg: Mapped[str | None] = mapped_column(String(30))
    birth_date: Mapped[date | None] = mapped_column(Date)
    approximate_age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(20))
    documents_status: Mapped[DocumentStatus] = mapped_column(
        SqlEnum(
            DocumentStatus,
            name="documentstatus",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=DocumentStatus.PARTIAL,
        server_default="Parcial",
    )
    street_time: Mapped[StreetTime | None] = mapped_column(
        SqlEnum(
            StreetTime,
            name="streettime",
            values_callable=_enum_values,
            native_enum=False,
        )
    )
    immediate_needs: Mapped[str | None] = mapped_column(Text)
    wants_prayer: Mapped[bool] = mapped_column(default=False, nullable=False, server_default=text("0"))
    accepts_visit: Mapped[bool] = mapped_column(default=False, nullable=False, server_default=text("0"))
    spiritual_decision: Mapped[SpiritualDecision | None] = mapped_column(
        SqlEnum(
            SpiritualDecision,
            name="spiritualdecision",
            values_callable=_enum_values,
            native_enum=False,
        )
    )
    reference_location: Mapped[str] = mapped_column(String(140), nullable=False)
    benefit_notes: Mapped[str | None] = mapped_column(Text)
    general_notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    consent_term_version: Mapped[str | None] = mapped_column(String(40))
    consent_accepted_at: Mapped[datetime | None] = mapped_column(DateTime)
    consent_accepted_by_user_id: Mapped[int | None] = mapped_column(Integer)
    consent_accepted: Mapped[bool] = mapped_column(default=False, nullable=False, server_default=text("0"))
    consent_signature_name: Mapped[str | None] = mapped_column(String(120))

    services: Mapped[list[StreetService]] = relationship(
        "StreetService",
        back_populates="person",
        cascade="all, delete-orphan",
        order_by="desc(StreetService.service_date)",
    )
    referrals: Mapped[list[Referral]] = relationship(
        "Referral",
        back_populates="person",
        cascade="all, delete-orphan",
        order_by="desc(Referral.referral_date)",
    )


class StreetService(Base):
    __tablename__ = "street_services"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey(table_key(DOMAIN_SCHEMA, "street_people.id")), nullable=False)
    service_type: Mapped[str] = mapped_column(String(80), nullable=False)
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    responsible_name: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    person: Mapped[StreetPerson] = relationship("StreetPerson", back_populates="services")


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey(table_key(DOMAIN_SCHEMA, "street_people.id")), nullable=False)
    recovery_home: Mapped[str] = mapped_column(String(160), nullable=False)
    target: Mapped[ReferralTarget] = mapped_column(
        SqlEnum(
            ReferralTarget,
            name="referraltarget",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=ReferralTarget.OTHER,
        server_default="Outro",
    )
    referral_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ReferralStatus] = mapped_column(
        SqlEnum(
            ReferralStatus,
            name="referralstatus",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=ReferralStatus.REFERRED,
        server_default="Encaminhado",
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    person: Mapped[StreetPerson] = relationship("StreetPerson", back_populates="referrals")


Index("ix_street_people_reference_location", StreetPerson.reference_location)
Index("ix_street_services_person_date", StreetService.person_id, StreetService.service_date)
Index("ix_street_services_type", StreetService.service_type)
Index("ix_referrals_person_status", Referral.person_id, Referral.status)
