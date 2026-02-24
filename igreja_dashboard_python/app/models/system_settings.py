from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.schemas import DOMAIN_SCHEMA, schema_kwargs


class SystemSettings(Base):
    __tablename__ = "system_settings"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    delivery_month_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    min_months_since_last_delivery: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
        server_default="2",
    )
    min_vulnerability_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
        server_default="2",
    )
    require_documentation_complete: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )
    updated_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.utcnow,
    )
