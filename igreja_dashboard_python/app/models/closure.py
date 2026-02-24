from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, CheckConstraint, DateTime, Enum as SqlEnum, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.schemas import DOMAIN_SCHEMA, schema_kwargs


class MonthlyClosureStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class MonthlyClosure(Base):
    __tablename__ = "monthly_closures"
    __table_args__ = (
        UniqueConstraint("month", "year", name="uq_monthly_closures_month_year"),
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_monthly_closures_month_range"),
        CheckConstraint(
            "official_pdf_sha256 IS NULL OR length(official_pdf_sha256) = 64",
            name="ck_monthly_closures_official_sha256_len",
        ),
        CheckConstraint(
            "official_pdf_sha256 IS NULL OR official_pdf_path IS NOT NULL",
            name="ck_monthly_closures_official_pdf_path_required",
        ),
        schema_kwargs(DOMAIN_SCHEMA),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    closed_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    summary_snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pdf_report_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    official_pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    official_pdf_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    official_snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    official_signed_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    official_signed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[MonthlyClosureStatus] = mapped_column(
        SqlEnum(
            MonthlyClosureStatus,
            name="monthlyclosurestatus",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
        ),
        nullable=False,
        default=MonthlyClosureStatus.OPEN,
        server_default="OPEN",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )


Index("ix_monthly_closures_year_month", MonthlyClosure.year, MonthlyClosure.month)
Index("ix_monthly_closures_status", MonthlyClosure.status)
