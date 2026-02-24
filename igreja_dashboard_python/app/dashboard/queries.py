from __future__ import annotations

from datetime import date

from sqlalchemy import case, distinct, func, or_, select

from app.models import (
    Equipment,
    EquipmentStatus,
    Family,
    FoodBasket,
    FoodBasketStatus,
    Loan,
    LoanStatus,
    VisitRequest,
    VisitRequestStatus,
    VulnerabilityLevel,
)

VULNERABILITY_ALERT_LEVELS = {VulnerabilityLevel.HIGH, VulnerabilityLevel.EXTREME}


def _format_cpf(cpf: str | None) -> str:
    digits = "".join(ch for ch in (cpf or "") if ch.isdigit())
    if len(digits) != 11:
        return cpf or "-"
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _format_rg(rg: str | None) -> str:
    cleaned = (rg or "").strip()
    if not cleaned:
        return "-"
    digits = "".join(ch for ch in cleaned if ch.isdigit())
    if len(digits) == 9:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}-{digits[8]}"
    if len(digits) == 8:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}"
    return cleaned


def month_window(reference_date: date | None = None) -> tuple[int, int, int, int]:
    today = reference_date or date.today()
    current_month = today.month
    current_year = today.year
    if current_month == 1:
        return current_month, current_year, 12, current_year - 1
    return current_month, current_year, current_month - 1, current_year


def count_active_families(db) -> int:
    return db.execute(select(func.count(Family.id)).where(Family.is_active.is_(True))).scalar_one()


def count_families_attended_in_month(db, month: int, year: int) -> int:
    stmt = (
        select(func.count(distinct(FoodBasket.family_id)))
        .join(Family, Family.id == FoodBasket.family_id)
        .where(
            Family.is_active.is_(True),
            FoodBasket.reference_month == month,
            FoodBasket.reference_year == year,
            FoodBasket.status == FoodBasketStatus.DELIVERED,
        )
    )
    return db.execute(stmt).scalar_one()


def count_families_without_recent_basket(db, months_threshold: int = 3) -> int:
    month_index = FoodBasket.reference_year * 12 + FoodBasket.reference_month
    latest_basket_subquery = (
        select(
            FoodBasket.family_id.label("family_id"),
            func.max(month_index).label("latest_month_index"),
        )
        .where(FoodBasket.status == FoodBasketStatus.DELIVERED)
        .group_by(FoodBasket.family_id)
        .subquery()
    )

    current_index = date.today().year * 12 + date.today().month
    months_without_expr = case(
        (latest_basket_subquery.c.latest_month_index.is_(None), current_index),
        else_=current_index - latest_basket_subquery.c.latest_month_index,
    )

    stmt = (
        select(func.count(Family.id))
        .outerjoin(latest_basket_subquery, latest_basket_subquery.c.family_id == Family.id)
        .where(Family.is_active.is_(True), months_without_expr >= months_threshold)
    )
    return db.execute(stmt).scalar_one()


def count_families_with_alerts(db, months_threshold: int = 3) -> int:
    month_index = FoodBasket.reference_year * 12 + FoodBasket.reference_month
    latest_basket_subquery = (
        select(
            FoodBasket.family_id.label("family_id"),
            func.max(month_index).label("latest_month_index"),
        )
        .where(FoodBasket.status == FoodBasketStatus.DELIVERED)
        .group_by(FoodBasket.family_id)
        .subquery()
    )

    current_index = date.today().year * 12 + date.today().month
    months_without_expr = case(
        (latest_basket_subquery.c.latest_month_index.is_(None), current_index),
        else_=current_index - latest_basket_subquery.c.latest_month_index,
    )

    stmt = (
        select(func.count(Family.id))
        .outerjoin(latest_basket_subquery, latest_basket_subquery.c.family_id == Family.id)
        .where(
            Family.is_active.is_(True),
            (
                (
                    Family.vulnerability.in_(tuple(VULNERABILITY_ALERT_LEVELS))
                    & (months_without_expr >= 2)
                )
                | (months_without_expr >= months_threshold)
            ),
        )
    )
    return db.execute(stmt).scalar_one()


def count_baskets_by_month(db, month: int, year: int) -> int:
    stmt = select(func.count(FoodBasket.id)).where(
        FoodBasket.reference_month == month,
        FoodBasket.reference_year == year,
        FoodBasket.status == FoodBasketStatus.DELIVERED,
    )
    return db.execute(stmt).scalar_one()


def equipment_overview(db) -> tuple[int, int, int]:
    total = db.execute(select(func.count(Equipment.id))).scalar_one()
    loaned_now = db.execute(
        select(func.count(Equipment.id)).where(Equipment.status == EquipmentStatus.LOANED)
    ).scalar_one()
    overdue_stmt = select(func.count(Loan.id)).where(
        Loan.status == LoanStatus.ACTIVE,
        Loan.due_date.is_not(None),
        Loan.due_date < date.today(),
    )
    overdue = db.execute(overdue_stmt).scalar_one()
    return total, loaned_now, overdue


def count_equipment_in_maintenance(db) -> int:
    stmt = select(func.count(Equipment.id)).where(Equipment.status == EquipmentStatus.UNAVAILABLE)
    return db.execute(stmt).scalar_one()


def alert_distribution(db, months_threshold: int = 3) -> dict[str, int]:
    month_index = FoodBasket.reference_year * 12 + FoodBasket.reference_month
    latest_basket_subquery = (
        select(
            FoodBasket.family_id.label("family_id"),
            func.max(month_index).label("latest_month_index"),
        )
        .where(FoodBasket.status == FoodBasketStatus.DELIVERED)
        .group_by(FoodBasket.family_id)
        .subquery()
    )

    current_index = date.today().year * 12 + date.today().month
    months_without_expr = case(
        (latest_basket_subquery.c.latest_month_index.is_(None), current_index),
        else_=current_index - latest_basket_subquery.c.latest_month_index,
    )

    basket_gap = db.execute(
        select(func.count(Family.id))
        .outerjoin(latest_basket_subquery, latest_basket_subquery.c.family_id == Family.id)
        .where(Family.is_active.is_(True), months_without_expr >= months_threshold)
    ).scalar_one()
    high_vulnerability = db.execute(
        select(func.count(Family.id))
        .outerjoin(latest_basket_subquery, latest_basket_subquery.c.family_id == Family.id)
        .where(
            Family.is_active.is_(True),
            Family.vulnerability.in_(tuple(VULNERABILITY_ALERT_LEVELS)),
            months_without_expr >= 2,
        )
    ).scalar_one()
    overdue_loans = db.execute(
        select(func.count(Loan.id)).where(
            Loan.status == LoanStatus.ACTIVE,
            Loan.due_date.is_not(None),
            Loan.due_date < date.today(),
        )
    ).scalar_one()

    return {
        "Sem cesta >= 3 meses": basket_gap,
        "Alta vulnerabilidade sem atendimento": high_vulnerability,
        "Empréstimos em atraso": overdue_loans,
    }


def social_visits_overview(db) -> tuple[int, int, int, int]:
    total_requests = db.execute(select(func.count(VisitRequest.id))).scalar_one()
    pending = db.execute(
        select(func.count(VisitRequest.id)).where(VisitRequest.status == VisitRequestStatus.PENDING)
    ).scalar_one()
    overdue = db.execute(
        select(func.count(VisitRequest.id)).where(
            VisitRequest.status == VisitRequestStatus.PENDING,
            VisitRequest.scheduled_date < date.today(),
        )
    ).scalar_one()
    completed_month = db.execute(
        select(func.count(VisitRequest.id)).where(
            VisitRequest.status == VisitRequestStatus.COMPLETED,
            func.extract("month", VisitRequest.scheduled_date) == date.today().month,
            func.extract("year", VisitRequest.scheduled_date) == date.today().year,
        )
    ).scalar_one()
    return total_requests, pending, overdue, completed_month


def neighborhood_heatmap(db, city: str | None = None, state: str | None = None) -> list[dict[str, object]]:
    normalized_neighborhood = func.upper(func.trim(Family.neighborhood))
    stmt = (
        select(
            normalized_neighborhood.label("neighborhood_normalized"),
            func.count(Family.id).label("active_families"),
            func.sum(
                case(
                    (Family.vulnerability.in_(tuple(VULNERABILITY_ALERT_LEVELS)), 1),
                    else_=0,
                )
            ).label("alerts"),
        )
        .where(
            Family.is_active.is_(True),
            Family.neighborhood.is_not(None),
            func.trim(Family.neighborhood) != "",
        )
        .group_by(normalized_neighborhood)
        .order_by(func.count(Family.id).desc(), normalized_neighborhood.asc())
    )
    if city:
        stmt = stmt.where(Family.city == city)
    if state:
        stmt = stmt.where(Family.state == state)

    rows = db.execute(stmt).all()
    return [
        {
            "neighborhood": str(row.neighborhood_normalized or "").title(),
            "neighborhood_normalized": str(row.neighborhood_normalized or ""),
            "active_families": int(row.active_families or 0),
            "alerts": int(row.alerts or 0),
        }
        for row in rows
    ]


def families_attended_in_month(db, month: int, year: int) -> list[dict[str, str]]:
    stmt = (
        select(Family.responsible_name, Family.responsible_cpf, Family.responsible_rg)
        .join(FoodBasket, FoodBasket.family_id == Family.id)
        .where(
            Family.is_active.is_(True),
            FoodBasket.reference_month == month,
            FoodBasket.reference_year == year,
            FoodBasket.status == FoodBasketStatus.DELIVERED,
        )
        .group_by(Family.id, Family.responsible_name, Family.responsible_cpf, Family.responsible_rg)
        .order_by(Family.responsible_name.asc())
    )
    rows = db.execute(stmt).all()
    return [
        {
            "responsible_name": row.responsible_name,
            "responsible_cpf": _format_cpf(row.responsible_cpf),
            "responsible_rg": _format_rg(row.responsible_rg),
        }
        for row in rows
    ]


def equipment_status_details(db) -> list[dict[str, str]]:
    active_loan = (
        select(Loan.id)
        .where(
            Loan.equipment_id == Equipment.id,
            Loan.status == LoanStatus.ACTIVE,
        )
        .order_by(Loan.loan_date.desc(), Loan.id.desc())
        .limit(1)
        .correlate(Equipment)
        .scalar_subquery()
    )

    stmt = (
        select(Equipment, Loan, Family)
        .outerjoin(Loan, Loan.id == active_loan)
        .outerjoin(Family, Family.id == Loan.family_id)
        .where(
            or_(
                Equipment.status.in_((EquipmentStatus.LOANED, EquipmentStatus.UNAVAILABLE)),
                Loan.id.is_not(None),
            )
        )
        .order_by(Equipment.code.asc())
    )
    rows = db.execute(stmt).all()

    data: list[dict[str, str]] = []
    for equipment, loan, family in rows:
        if loan is not None and loan.status == LoanStatus.ACTIVE and loan.due_date and loan.due_date < date.today():
            status_label = "Em atraso"
        elif equipment.status == EquipmentStatus.UNAVAILABLE:
            status_label = "Em manutenção"
        elif equipment.status == EquipmentStatus.LOANED or loan is not None:
            status_label = "Emprestado"
        else:
            status_label = equipment.status.value

        data.append(
            {
                "equipment_code": equipment.code,
                "equipment_description": equipment.description,
                "status_label": status_label,
                "family_name": family.responsible_name if family else "-",
                "due_date": loan.due_date.isoformat() if loan and loan.due_date else "-",
            }
        )
    return data
