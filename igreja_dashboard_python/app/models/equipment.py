from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SqlEnum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.schemas import DOMAIN_SCHEMA, schema_kwargs, table_key




def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]

class EquipmentStatus(str, Enum):
    AVAILABLE = "Disponível"
    LOANED = "Emprestado"
    MAINTENANCE = "Manutenção"


class EquipmentType(str, Enum):
    CANE = "Bengala"
    WHEELCHAIR = "Cadeira de rodas"
    WALKER = "Andador"
    CRUTCH = "Muleta"
    BED = "Cama"
    OTHER = "Outros"


class EquipmentCondition(str, Enum):
    NEW = "Novo"
    GOOD = "Bom"
    NEEDS_REPAIR = "Precisa reparo"


class LoanStatus(str, Enum):
    ACTIVE = "Ativo"
    RETURNED = "Devolvido"


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    equipment_type: Mapped[EquipmentType] = mapped_column(
        SqlEnum(
            EquipmentType,
            name="equipmenttype",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=EquipmentType.OTHER,
        server_default="Outros",
    )
    condition_status: Mapped[EquipmentCondition] = mapped_column(
        SqlEnum(
            EquipmentCondition,
            name="equipmentcondition",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=EquipmentCondition.GOOD,
        server_default="Bom",
    )
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[EquipmentStatus] = mapped_column(
        SqlEnum(
            EquipmentStatus,
            name="equipmentstatus",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=EquipmentStatus.AVAILABLE,
        server_default="Disponível",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    loans: Mapped[list[Loan]] = relationship(
        "Loan",
        back_populates="equipment",
        cascade="all, delete-orphan",
        order_by="desc(Loan.loan_date)",
    )


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey(table_key(DOMAIN_SCHEMA, "equipment.id")), nullable=False)
    family_id: Mapped[int] = mapped_column(ForeignKey(table_key(DOMAIN_SCHEMA, "families.id")), nullable=False)
    loan_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[LoanStatus] = mapped_column(
        SqlEnum(
            LoanStatus,
            name="loanstatus",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=LoanStatus.ACTIVE,
        server_default="Ativo",
    )
    returned_at: Mapped[date | None] = mapped_column(Date)
    return_condition: Mapped[EquipmentCondition | None] = mapped_column(
        SqlEnum(
            EquipmentCondition,
            name="equipmentcondition",
            values_callable=_enum_values,
            native_enum=False,
        )
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    equipment: Mapped[Equipment] = relationship("Equipment", back_populates="loans")
    family: Mapped[Family] = relationship("Family", back_populates="loans")


from app.models.family import Family  # noqa: E402  # isort: skip


Index("ix_equipment_code", Equipment.code)
Index("ix_loans_family_id", Loan.family_id)
Index("ix_loans_equipment_id", Loan.equipment_id)
Index("ix_loans_status", Loan.status)
