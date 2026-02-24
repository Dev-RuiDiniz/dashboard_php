from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import and_, case, extract, func, literal, or_, select

from app.models import (
    DeliveryWithdrawal,
    Family,
    FoodBasket,
    FoodBasketStatus,
    SystemSettings,
    VulnerabilityLevel,
)


class EligibilityReason(StrEnum):
    DOC_PENDING = "DOC_PENDING"
    LOW_VULNERABILITY = "LOW_VULNERABILITY"
    RECENT_DELIVERY = "RECENT_DELIVERY"
    MONTH_LIMIT_REACHED = "MONTH_LIMIT_REACHED"


VULNERABILITY_ORDER: dict[VulnerabilityLevel, int] = {
    VulnerabilityLevel.NONE: 0,
    VulnerabilityLevel.LOW: 1,
    VulnerabilityLevel.MEDIUM: 2,
    VulnerabilityLevel.HIGH: 3,
    VulnerabilityLevel.EXTREME: 4,
}


@dataclass
class FamilyEligibilityResult:
    family_id: int
    eligible: bool
    reasons: list[EligibilityReason]


def _settings_defaults() -> SystemSettings:
    return SystemSettings(
        id=1,
        delivery_month_limit=1,
        min_months_since_last_delivery=2,
        min_vulnerability_level=2,
        require_documentation_complete=True,
    )


def get_system_settings(db) -> SystemSettings:
    settings = db.execute(select(SystemSettings).limit(1)).scalar_one_or_none()
    if settings:
        return settings

    settings = _settings_defaults()
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


DOC_COMPLETE_TOKENS = ("OK", "COMPLETE", "COMPLETO", "COMPLETA", "REGULAR")


def _is_documentation_complete(status: str | None) -> bool:
    normalized = (status or "").strip().upper()
    return any(token in normalized for token in DOC_COMPLETE_TOKENS)


def _latest_delivery_sources_subquery():
    withdrawal_month_index = (
        extract("year", DeliveryWithdrawal.confirmed_at) * 12
        + extract("month", DeliveryWithdrawal.confirmed_at)
    )
    withdrawal_last = (
        select(
            DeliveryWithdrawal.family_id.label("family_id"),
            func.max(DeliveryWithdrawal.confirmed_at).label("latest_withdrawal_at"),
            func.max(withdrawal_month_index).label("latest_withdrawal_month_index"),
        )
        .group_by(DeliveryWithdrawal.family_id)
        .subquery()
    )

    basket_month_index = FoodBasket.reference_year * 12 + FoodBasket.reference_month
    basket_last = (
        select(
            FoodBasket.family_id.label("family_id"),
            func.max(
                func.date(
                    func.printf(
                        "%04d-%02d-01",
                        FoodBasket.reference_year,
                        FoodBasket.reference_month,
                    )
                )
            ).label("latest_basket_date"),
            func.max(basket_month_index).label("latest_basket_month_index"),
        )
        .where(FoodBasket.status == FoodBasketStatus.DELIVERED)
        .group_by(FoodBasket.family_id)
        .subquery()
    )

    return withdrawal_last, basket_last


def _last_delivery_month_index_expr(withdrawal_last, basket_last):
    return case(
        (
            and_(
                withdrawal_last.c.latest_withdrawal_month_index.is_not(None),
                or_(
                    basket_last.c.latest_basket_month_index.is_(None),
                    withdrawal_last.c.latest_withdrawal_month_index
                    >= basket_last.c.latest_basket_month_index,
                ),
            ),
            withdrawal_last.c.latest_withdrawal_month_index,
        ),
        else_=basket_last.c.latest_basket_month_index,
    )


def _months_since_expr(last_delivery_month_index_expr):
    current_index = date.today().year * 12 + date.today().month
    return case(
        (
            last_delivery_month_index_expr.is_(None),
            literal(current_index),
        ),
        else_=literal(current_index) - last_delivery_month_index_expr,
    )


def _month_deliveries_count_subquery():
    today = date.today()

    withdrawals_count = (
        select(
            DeliveryWithdrawal.family_id.label("family_id"),
            func.count(DeliveryWithdrawal.id).label("withdrawals_count"),
        )
        .where(
            extract("year", DeliveryWithdrawal.confirmed_at) == today.year,
            extract("month", DeliveryWithdrawal.confirmed_at) == today.month,
        )
        .group_by(DeliveryWithdrawal.family_id)
        .subquery()
    )

    baskets_count = (
        select(
            FoodBasket.family_id.label("family_id"),
            func.count(FoodBasket.id).label("baskets_count"),
        )
        .where(
            FoodBasket.status == FoodBasketStatus.DELIVERED,
            FoodBasket.reference_year == today.year,
            FoodBasket.reference_month == today.month,
        )
        .group_by(FoodBasket.family_id)
        .subquery()
    )

    return withdrawals_count, baskets_count


def compute_family_eligibility(db, family_id: int, settings: SystemSettings) -> FamilyEligibilityResult:
    family = db.get(Family, family_id)
    if not family or not family.is_active:
        return FamilyEligibilityResult(family_id=family_id, eligible=False, reasons=[])

    reasons: list[EligibilityReason] = []

    vulnerability_value = VULNERABILITY_ORDER.get(family.vulnerability, 0)
    if vulnerability_value < settings.min_vulnerability_level:
        reasons.append(EligibilityReason.LOW_VULNERABILITY)

    if settings.require_documentation_complete and not _is_documentation_complete(
        family.documentation_status
    ):
        reasons.append(EligibilityReason.DOC_PENDING)

    withdrawal_last, basket_last = _latest_delivery_sources_subquery()
    last_delivery_month_index_expr = _last_delivery_month_index_expr(withdrawal_last, basket_last)
    months_since_expr = _months_since_expr(last_delivery_month_index_expr)

    row = db.execute(
        select(months_since_expr.label("months_since"))
        .select_from(Family)
        .outerjoin(withdrawal_last, withdrawal_last.c.family_id == Family.id)
        .outerjoin(basket_last, basket_last.c.family_id == Family.id)
        .where(Family.id == family_id)
    ).one()
    if int(row.months_since or 0) < settings.min_months_since_last_delivery:
        reasons.append(EligibilityReason.RECENT_DELIVERY)

    if settings.delivery_month_limit > 0:
        withdrawals_count, baskets_count = _month_deliveries_count_subquery()
        delivery_count_row = db.execute(
            select(
                (
                    func.coalesce(withdrawals_count.c.withdrawals_count, 0)
                    + func.coalesce(baskets_count.c.baskets_count, 0)
                ).label("month_deliveries")
            )
            .select_from(Family)
            .outerjoin(withdrawals_count, withdrawals_count.c.family_id == Family.id)
            .outerjoin(baskets_count, baskets_count.c.family_id == Family.id)
            .where(Family.id == family_id)
        ).one()

        if int(delivery_count_row.month_deliveries or 0) >= settings.delivery_month_limit:
            reasons.append(EligibilityReason.MONTH_LIMIT_REACHED)

    return FamilyEligibilityResult(family_id=family_id, eligible=not reasons, reasons=reasons)


def _coalesce_latest_delivery_date(latest_withdrawal_at, latest_basket_date):
    basket_date_obj: date | None = None
    if latest_basket_date:
        if isinstance(latest_basket_date, str):
            basket_date_obj = datetime.fromisoformat(latest_basket_date).date()
        elif isinstance(latest_basket_date, datetime):
            basket_date_obj = latest_basket_date.date()
        elif isinstance(latest_basket_date, date):
            basket_date_obj = latest_basket_date

    withdrawal_date_obj: date | None = None
    if latest_withdrawal_at:
        if isinstance(latest_withdrawal_at, str):
            withdrawal_date_obj = datetime.fromisoformat(latest_withdrawal_at).date()
        elif isinstance(latest_withdrawal_at, datetime):
            withdrawal_date_obj = latest_withdrawal_at.date()
        elif isinstance(latest_withdrawal_at, date):
            withdrawal_date_obj = latest_withdrawal_at

    if withdrawal_date_obj and (not basket_date_obj or withdrawal_date_obj >= basket_date_obj):
        return withdrawal_date_obj
    return basket_date_obj


def list_eligible_families(db, settings: SystemSettings, limit: int = 20, neighborhood: str | None = None):
    withdrawal_last, basket_last = _latest_delivery_sources_subquery()
    last_delivery_month_index_expr = _last_delivery_month_index_expr(withdrawal_last, basket_last)
    months_since_expr = _months_since_expr(last_delivery_month_index_expr)
    withdrawals_count, baskets_count = _month_deliveries_count_subquery()

    vulnerability_rank = case(
        *[(Family.vulnerability == level, rank) for level, rank in VULNERABILITY_ORDER.items()],
        else_=0,
    )

    stmt = (
        select(
            Family,
            withdrawal_last.c.latest_withdrawal_at,
            basket_last.c.latest_basket_date,
            (
                func.coalesce(withdrawals_count.c.withdrawals_count, 0)
                + func.coalesce(baskets_count.c.baskets_count, 0)
            ).label("month_deliveries"),
            months_since_expr.label("months_since_last_delivery"),
        )
        .outerjoin(withdrawal_last, withdrawal_last.c.family_id == Family.id)
        .outerjoin(basket_last, basket_last.c.family_id == Family.id)
        .outerjoin(withdrawals_count, withdrawals_count.c.family_id == Family.id)
        .outerjoin(baskets_count, baskets_count.c.family_id == Family.id)
        .where(
            Family.is_active.is_(True),
            vulnerability_rank >= settings.min_vulnerability_level,
            months_since_expr >= settings.min_months_since_last_delivery,
        )
        .order_by(vulnerability_rank.desc(), Family.responsible_name.asc())
        .limit(max(1, min(limit, 100)))
    )

    if neighborhood:
        stmt = stmt.where(func.upper(func.trim(Family.neighborhood)) == neighborhood.strip().upper())

    if settings.require_documentation_complete:
        normalized_doc_status = func.upper(func.trim(func.coalesce(Family.documentation_status, "")))
        stmt = stmt.where(
            or_(*[normalized_doc_status.like(f"%{token}%") for token in DOC_COMPLETE_TOKENS])
        )

    if settings.delivery_month_limit > 0:
        stmt = stmt.where(
            (
                func.coalesce(withdrawals_count.c.withdrawals_count, 0)
                + func.coalesce(baskets_count.c.baskets_count, 0)
            )
            < settings.delivery_month_limit
        )

    rows = db.execute(stmt).all()
    return [
        {
            "family": row.Family,
            "last_delivery_date": _coalesce_latest_delivery_date(
                row.latest_withdrawal_at, row.latest_basket_date
            ),
            "month_deliveries": int(row.month_deliveries or 0),
            "months_since_last_delivery": int(row.months_since_last_delivery or 0),
            "doc_pending": not _is_documentation_complete(row.Family.documentation_status),
        }
        for row in rows
    ]
