from __future__ import annotations

from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy import select

from app.models import MonthlyClosure, MonthlyClosureStatus


LOCKED_MONTH_MESSAGE = "Mês fechado: alterações retroativas estão bloqueadas."


def _coerce_month_year(target_date: date | datetime | None, month: int | None, year: int | None) -> tuple[int, int]:
    if target_date is not None:
        return target_date.month, target_date.year
    if month is None or year is None:
        raise ValueError("É necessário informar data ou mês/ano para validação de fechamento.")
    return month, year


def is_month_closed(db, month: int, year: int) -> bool:
    closure = db.execute(
        select(MonthlyClosure).where(
            MonthlyClosure.month == month,
            MonthlyClosure.year == year,
            MonthlyClosure.status == MonthlyClosureStatus.CLOSED,
        )
    ).scalar_one_or_none()
    return closure is not None


def require_month_open(
    db,
    *,
    target_date: date | datetime | None = None,
    month: int | None = None,
    year: int | None = None,
) -> None:
    target_month, target_year = _coerce_month_year(target_date, month, year)
    if is_month_closed(db, target_month, target_year):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=LOCKED_MONTH_MESSAGE)
