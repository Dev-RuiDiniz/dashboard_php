from __future__ import annotations

from app.dashboard import queries
from app.dashboard.schemas import (
    AlertKPI,
    BasketKPI,
    DashboardData,
    EquipmentKPI,
    EquipmentStatusRow,
    FamilyKPI,
    KPITrend,
    VisitKPI,
    AttendedFamilyRow,
    EligibleFamilyRow,
)
from app.eligibility.engine import get_system_settings, list_eligible_families


def build_dashboard_data(db, neighborhood: str | None = None, eligible_limit: int = 20) -> DashboardData:
    current_month, current_year, previous_month, previous_year = queries.month_window()

    total_active = queries.count_active_families(db)
    families_with_alerts = queries.count_families_with_alerts(db)
    families_attended = queries.count_families_attended_in_month(db, current_month, current_year)

    baskets_current = queries.count_baskets_by_month(db, current_month, current_year)
    baskets_previous = queries.count_baskets_by_month(db, previous_month, previous_year)
    families_without_recent = queries.count_families_without_recent_basket(db)

    total_equipment, loaned_now, overdue = queries.equipment_overview(db)
    maintenance = queries.count_equipment_in_maintenance(db)
    attended_families_rows = queries.families_attended_in_month(db, current_month, current_year)
    equipment_status_rows = queries.equipment_status_details(db)
    visits_total, visits_pending, visits_overdue, visits_completed_month = (
        queries.social_visits_overview(db)
    )
    alert_by_type = queries.alert_distribution(db)

    settings = get_system_settings(db)
    eligible_rows = list_eligible_families(
        db,
        settings=settings,
        limit=eligible_limit,
        neighborhood=neighborhood,
    )

    return DashboardData(
        families=FamilyKPI(
            total_active=total_active,
            with_alerts=families_with_alerts,
            attended_this_month=families_attended,
        ),
        baskets=BasketKPI(
            total_this_month=baskets_current,
            monthly_comparison=KPITrend(current=baskets_current, previous=baskets_previous),
            families_without_recent_basket=families_without_recent,
        ),
        equipment=EquipmentKPI(
            total_registered=total_equipment,
            loaned_now=loaned_now,
            overdue=overdue,
            maintenance=maintenance,
        ),
        visits=VisitKPI(
            total_requests=visits_total,
            pending=visits_pending,
            overdue=visits_overdue,
            completed_this_month=visits_completed_month,
        ),
        alerts=AlertKPI(total_active=sum(alert_by_type.values()), by_type=alert_by_type),
        attended_families=[AttendedFamilyRow(**row) for row in attended_families_rows],
        equipment_statuses=[EquipmentStatusRow(**row) for row in equipment_status_rows],
        eligible_families=[
            EligibleFamilyRow(
                family_id=item["family"].id,
                responsible_name=item["family"].responsible_name,
                neighborhood=item["family"].neighborhood or "-",
                vulnerability=item["family"].vulnerability.value,
                last_delivery=item["last_delivery_date"].strftime("%d/%m/%Y")
                if item["last_delivery_date"]
                else "Nunca",
                doc_pending=item["doc_pending"],
            )
            for item in eligible_rows
        ],
    )
