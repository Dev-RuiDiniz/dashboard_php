from __future__ import annotations

from datetime import date

from sqlalchemy import case, extract, func, select
from sqlalchemy.orm import selectinload

from app.models import (
    Child,
    Family,
    FoodBasket,
    FoodBasketStatus,
    Loan,
    LoanStatus,
    Referral,
    StreetPerson,
    VisitRequest,
    VisitRequestStatus,
    VulnerabilityLevel,
)

VULNERABILITY_ALERT_LEVELS = {VulnerabilityLevel.HIGH, VulnerabilityLevel.EXTREME}


def families_report(db, only_active: bool = False) -> list[Family]:
    stmt = select(Family).order_by(Family.responsible_name)
    if only_active:
        stmt = stmt.where(Family.is_active.is_(True))
    return db.execute(stmt).scalars().all()


def baskets_report(db, year: int | None = None, month: int | None = None) -> list[FoodBasket]:
    stmt = (
        select(FoodBasket)
        .options(selectinload(FoodBasket.family))
        .order_by(FoodBasket.reference_year.desc(), FoodBasket.reference_month.desc())
    )
    if year is not None:
        stmt = stmt.where(FoodBasket.reference_year == year)
    if month is not None:
        stmt = stmt.where(FoodBasket.reference_month == month)
    return db.execute(stmt).scalars().all()


def equipment_report(db) -> list[Loan]:
    stmt = (
        select(Loan)
        .options(selectinload(Loan.family), selectinload(Loan.equipment))
        .order_by(Loan.loan_date.desc())
    )
    return db.execute(stmt).scalars().all()


def children_report(db) -> list[Child]:
    stmt = select(Child).options(selectinload(Child.family)).order_by(Child.name.asc())
    return db.execute(stmt).scalars().all()


def referrals_report(db) -> list[Referral]:
    stmt = (
        select(Referral)
        .options(selectinload(Referral.person))
        .order_by(Referral.referral_date.desc())
    )
    return db.execute(stmt).scalars().all()


def alerts_report(db, months_threshold: int = 3) -> list[dict[str, str | int]]:
    families = db.execute(select(Family).order_by(Family.responsible_name)).scalars().all()
    alerts: list[dict[str, str | int]] = []
    current_index = date.today().year * 12 + date.today().month

    for family in families:
        latest_basket = db.execute(
            select(FoodBasket)
            .where(
                FoodBasket.family_id == family.id, FoodBasket.status == FoodBasketStatus.DELIVERED
            )
            .order_by(FoodBasket.reference_year.desc(), FoodBasket.reference_month.desc())
            .limit(1)
        ).scalar_one_or_none()

        if latest_basket:
            latest_index = latest_basket.reference_year * 12 + latest_basket.reference_month
            months_without = current_index - latest_index
            if months_without >= months_threshold:
                alerts.append(
                    {
                        "family": family.responsible_name,
                        "type": "Sem cesta recente",
                        "duration": months_without,
                    }
                )

        overdue_loans = (
            db.execute(
                select(Loan).where(
                    Loan.family_id == family.id,
                    Loan.status == LoanStatus.ACTIVE,
                    Loan.due_date.is_not(None),
                    Loan.due_date < date.today(),
                )
            )
            .scalars()
            .all()
        )
        for loan in overdue_loans:
            duration = (date.today() - loan.due_date).days
            alerts.append(
                {
                    "family": family.responsible_name,
                    "type": "Equipamento em atraso",
                    "duration": duration,
                }
            )

        overdue_visits = (
            db.execute(
                select(VisitRequest).where(
                    VisitRequest.family_id == family.id,
                    VisitRequest.status == VisitRequestStatus.PENDING,
                    VisitRequest.scheduled_date < date.today(),
                )
            )
            .scalars()
            .all()
        )
        for visit in overdue_visits:
            duration = (date.today() - visit.scheduled_date).days
            alerts.append(
                {
                    "family": family.responsible_name,
                    "type": "Visita social em atraso",
                    "duration": duration,
                }
            )

    return alerts


def street_people_report(db) -> list[dict[str, str | int]]:
    people = (
        db.execute(select(StreetPerson).order_by(StreetPerson.created_at.desc())).scalars().all()
    )
    rows: list[dict[str, str | int]] = []
    for person in people:
        last_referral = (
            person.referrals[0].status.value if person.referrals else "Sem encaminhamento"
        )
        rows.append(
            {
                "name": person.full_name or "Não informado",
                "reference_location": person.reference_location,
                "service_count": len(person.services),
                "last_referral_status": last_referral,
            }
        )
    return rows


def visits_report(db, year: int | None = None, month: int | None = None) -> list[VisitRequest]:
    stmt = (
        select(VisitRequest)
        .options(selectinload(VisitRequest.family))
        .order_by(VisitRequest.scheduled_date.desc())
    )
    if year is not None:
        stmt = stmt.where(extract("year", VisitRequest.scheduled_date) == year)
    if month is not None:
        stmt = stmt.where(extract("month", VisitRequest.scheduled_date) == month)
    return db.execute(stmt).scalars().all()


def neighborhood_report(db, year: int | None = None, month: int | None = None) -> list[dict[str, int | str]]:
    delivered_this_period = case(
        (
            FoodBasket.status == FoodBasketStatus.DELIVERED,
            1,
        ),
        else_=0,
    )
    if year is not None:
        delivered_this_period = case(
            (
                (FoodBasket.status == FoodBasketStatus.DELIVERED)
                & (FoodBasket.reference_year == year)
                & ((FoodBasket.reference_month == month) if month is not None else True),
                1,
            ),
            else_=0,
        )

    normalized_neighborhood = func.upper(func.trim(Family.neighborhood))

    stmt = (
        select(
            normalized_neighborhood.label("neighborhood_normalized"),
            func.count(func.distinct(Family.id)).label("families_total"),
            func.sum(delivered_this_period).label("baskets_total"),
            func.count(
                func.distinct(
                    case(
                        (Family.vulnerability.in_(tuple(VULNERABILITY_ALERT_LEVELS)), Family.id),
                        else_=None,
                    )
                )
            ).label("alerts_total"),
        )
        .outerjoin(FoodBasket, FoodBasket.family_id == Family.id)
        .where(
            Family.is_active.is_(True),
            Family.neighborhood.is_not(None),
            func.trim(Family.neighborhood) != "",
        )
        .group_by(normalized_neighborhood)
        .order_by(func.count(func.distinct(Family.id)).desc(), normalized_neighborhood.asc())
    )
    rows = db.execute(stmt).all()
    return [
        {
            "neighborhood": str(row.neighborhood_normalized or "").title(),
            "neighborhood_normalized": str(row.neighborhood_normalized or ""),
            "families_total": int(row.families_total or 0),
            "baskets_total": int(row.baskets_total or 0),
            "alerts_total": int(row.alerts_total or 0),
        }
        for row in rows
    ]
