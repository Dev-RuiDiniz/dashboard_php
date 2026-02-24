from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.schemas import DOMAIN_SCHEMA, schema_kwargs


class ConsentTerm(Base):
    __tablename__ = "consent_terms"
    __table_args__ = schema_kwargs(DOMAIN_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())


Index("ix_consent_terms_active", ConsentTerm.active)
