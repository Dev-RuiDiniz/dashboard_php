from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

from sqlalchemy import extract, func, select

from app.models import (
    Child,
    DeliveryEvent,
    DeliveryInvite,
    DeliveryInviteStatus,
    DeliveryWithdrawal,
    Family,
    FoodBasket,
    FoodBasketStatus,
    Loan,
    LoanStatus,
    Referral,
    StreetService,
    VisitRequest,
    VisitRequestStatus,
)


def _deliveries_totals(db, month: int, year: int) -> tuple[int, set[int], list[str]]:
    withdrawals = db.execute(
        select(DeliveryWithdrawal.family_id)
        .join(DeliveryEvent, DeliveryEvent.id == DeliveryWithdrawal.event_id)
        .where(
            extract("month", DeliveryEvent.event_date) == month,
            extract("year", DeliveryEvent.event_date) == year,
        )
    ).scalars().all()

    if withdrawals:
        return len(withdrawals), set(withdrawals), ["delivery_withdrawals"]

    legacy = db.execute(
        select(FoodBasket.family_id).where(
            FoodBasket.reference_month == month,
            FoodBasket.reference_year == year,
            FoodBasket.status == FoodBasketStatus.DELIVERED,
        )
    ).scalars().all()
    return len(legacy), set(legacy), ["food_baskets_legacy"]


def build_monthly_snapshot(db, month: int, year: int, generated_by_user_id: int | None = None) -> dict:
    deliveries_count, attended_family_ids, delivery_source = _deliveries_totals(db, month, year)

    children_count = 0
    if attended_family_ids:
        children_count = int(
            db.execute(select(func.count(Child.id)).where(Child.family_id.in_(attended_family_ids))).scalar()
            or 0
        )

    referrals = db.execute(
        select(Referral).where(
            extract("month", Referral.referral_date) == month,
            extract("year", Referral.referral_date) == year,
        )
    ).scalars().all()
    referrals_by_type = Counter(item.status.value for item in referrals)

    visits_count = int(
        db.execute(
            select(func.count(VisitRequest.id)).where(
                extract("month", VisitRequest.scheduled_date) == month,
                extract("year", VisitRequest.scheduled_date) == year,
            )
        ).scalar()
        or 0
    )

    equipment_loans_count = int(
        db.execute(
            select(func.count(Loan.id)).where(
                extract("month", Loan.loan_date) == month,
                extract("year", Loan.loan_date) == year,
            )
        ).scalar()
        or 0
    )
    equipment_returns_count = int(
        db.execute(
            select(func.count(Loan.id)).where(
                Loan.status == LoanStatus.RETURNED,
                Loan.returned_at.is_not(None),
                extract("month", Loan.returned_at) == month,
                extract("year", Loan.returned_at) == year,
            )
        ).scalar()
        or 0
    )

    pending_docs_count = int(
        db.execute(
            select(func.count(Family.id)).where(
                Family.is_active.is_(True),
                (Family.documentation_status.is_(None)) | (func.trim(Family.documentation_status) == ""),
            )
        ).scalar()
        or 0
    )
    pending_visits_count = int(
        db.execute(
            select(func.count(VisitRequest.id)).where(
                VisitRequest.status == VisitRequestStatus.PENDING,
                extract("month", VisitRequest.scheduled_date) == month,
                extract("year", VisitRequest.scheduled_date) == year,
            )
        ).scalar()
        or 0
    )

    services_count = int(
        db.execute(
            select(func.count(StreetService.id)).where(
                extract("month", StreetService.service_date) == month,
                extract("year", StreetService.service_date) == year,
            )
        ).scalar()
        or 0
    )

    neighborhood_totals: dict[str, dict[str, int]] = defaultdict(lambda: {"families": 0, "deliveries": 0})
    if attended_family_ids:
        rows = db.execute(select(Family.id, Family.neighborhood).where(Family.id.in_(attended_family_ids))).all()
        for family_id, neighborhood in rows:
            key = (neighborhood or "Não informado").strip() or "Não informado"
            neighborhood_totals[key]["families"] += 1
            if family_id in attended_family_ids:
                neighborhood_totals[key]["deliveries"] += 1

    equipment_status_rows = db.execute(select(Loan.status, func.count(Loan.id)).group_by(Loan.status)).all()
    equipment_status_summary = {str(status.value): int(total) for status, total in equipment_status_rows}

    return {
        "totals": {
            "families_attended": len(attended_family_ids),
            "deliveries_count": deliveries_count,
            "children_count": children_count,
            "referrals_count": {
                "total": len(referrals),
                "by_type": dict(referrals_by_type),
            },
            "visits_count": visits_count,
            "street_services_count": services_count,
            "equipment_loans_count": equipment_loans_count,
            "equipment_returns_count": equipment_returns_count,
            "pending_docs_count": pending_docs_count,
            "pending_visits_count": pending_visits_count,
        },
        "breakdowns": {
            "by_neighborhood": [
                {
                    "neighborhood": neighborhood,
                    "families": values["families"],
                    "deliveries": values["deliveries"],
                }
                for neighborhood, values in sorted(neighborhood_totals.items())
            ],
            "referrals_by_type": dict(referrals_by_type),
            "equipment_status_summary": equipment_status_summary,
        },
        "metadata": {
            "month": month,
            "year": year,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by_user_id": generated_by_user_id,
            "data_sources": sorted(
                {
                    *delivery_source,
                    "children",
                    "referrals",
                    "visit_requests",
                    "street_services",
                    "loans",
                    "families",
                }
            ),
        },
    }
