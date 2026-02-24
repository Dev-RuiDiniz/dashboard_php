from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum as SqlEnum,
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


class DeliveryEventStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class DeliveryInviteStatus(str, Enum):
    INVITED = "INVITED"
    WITHDRAWN = "WITHDRAWN"
    NO_SHOW = "NO_SHOW"


class DeliveryEvent(Base):
    __tablename__ = "delivery_events"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[DeliveryEventStatus] = mapped_column(
        SqlEnum(
            DeliveryEventStatus,
            name="deliveryeventstatus",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=DeliveryEventStatus.OPEN,
        server_default="OPEN",
    )
    created_by_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    has_children_list: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )

    invites: Mapped[list[DeliveryInvite]] = relationship(
        "DeliveryInvite",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="desc(DeliveryInvite.invited_at)",
    )
    withdrawals: Mapped[list[DeliveryWithdrawal]] = relationship(
        "DeliveryWithdrawal",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="desc(DeliveryWithdrawal.confirmed_at)",
    )


class DeliveryInvite(Base):
    __tablename__ = "delivery_invites"
    __table_args__ = (
        UniqueConstraint("event_id", "family_id", name="uq_delivery_invites_event_family"),
        schema_kwargs(DOMAIN_SCHEMA),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey(table_key(DOMAIN_SCHEMA, "delivery_events.id")),
        nullable=False,
    )
    family_id: Mapped[int] = mapped_column(
        ForeignKey(table_key(DOMAIN_SCHEMA, "families.id")), nullable=False
    )
    withdrawal_code: Mapped[str] = mapped_column(String(6), nullable=False)
    invited_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    status: Mapped[DeliveryInviteStatus] = mapped_column(
        SqlEnum(
            DeliveryInviteStatus,
            name="deliveryinvitestatus",
            values_callable=_enum_values,
            native_enum=False,
        ),
        nullable=False,
        default=DeliveryInviteStatus.INVITED,
        server_default="INVITED",
    )

    event: Mapped[DeliveryEvent] = relationship("DeliveryEvent", back_populates="invites")
    family: Mapped[Family] = relationship("Family")


class DeliveryWithdrawal(Base):
    __tablename__ = "delivery_withdrawals"
    __table_args__ = (
        UniqueConstraint("event_id", "family_id", name="uq_delivery_withdrawals_event_family"),
        schema_kwargs(DOMAIN_SCHEMA),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey(table_key(DOMAIN_SCHEMA, "delivery_events.id")),
        nullable=False,
    )
    family_id: Mapped[int] = mapped_column(
        ForeignKey(table_key(DOMAIN_SCHEMA, "families.id")), nullable=False
    )
    confirmed_by_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    signature_name: Mapped[str] = mapped_column(String(120), nullable=False)
    signature_accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    event: Mapped[DeliveryEvent] = relationship("DeliveryEvent", back_populates="withdrawals")
    family: Mapped[Family] = relationship("Family")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    before_json: Mapped[dict | None] = mapped_column(JSON)
    after_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )


Index("ix_delivery_events_date_status", DeliveryEvent.event_date, DeliveryEvent.status)
Index("ix_delivery_events_created_by", DeliveryEvent.created_by_user_id)
Index("ix_delivery_invites_event_status", DeliveryInvite.event_id, DeliveryInvite.status)
Index(
    "ix_delivery_invites_event_code",
    DeliveryInvite.event_id,
    DeliveryInvite.withdrawal_code,
    unique=True,
)
Index("ix_delivery_invites_family_id", DeliveryInvite.family_id)
Index(
    "ix_delivery_withdrawals_event_family",
    DeliveryWithdrawal.event_id,
    DeliveryWithdrawal.family_id,
)
Index("ix_delivery_withdrawals_confirmed_by", DeliveryWithdrawal.confirmed_by_user_id)
Index("ix_audit_logs_entity", AuditLog.entity)
Index("ix_audit_logs_entity_id", AuditLog.entity_id)
Index("ix_audit_logs_user_id", AuditLog.user_id)
Index("ix_audit_logs_created_at", AuditLog.created_at)
Index("ix_audit_logs_entity_created", AuditLog.entity, AuditLog.entity_id, AuditLog.created_at)
Index("ix_audit_logs_user_created", AuditLog.user_id, AuditLog.created_at)

from app.models.family import Family  # noqa: E402  # isort: skip
