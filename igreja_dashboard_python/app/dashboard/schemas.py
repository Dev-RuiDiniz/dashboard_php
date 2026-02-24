from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KPITrend:
    current: int
    previous: int


@dataclass
class FamilyKPI:
    total_active: int
    with_alerts: int
    attended_this_month: int


@dataclass
class BasketKPI:
    total_this_month: int
    monthly_comparison: KPITrend
    families_without_recent_basket: int


@dataclass
class VisitKPI:
    total_requests: int
    pending: int
    overdue: int
    completed_this_month: int


@dataclass
class EquipmentKPI:
    total_registered: int
    loaned_now: int
    overdue: int
    maintenance: int


@dataclass
class AttendedFamilyRow:
    responsible_name: str
    responsible_cpf: str
    responsible_rg: str


@dataclass
class EquipmentStatusRow:
    equipment_code: str
    equipment_description: str
    status_label: str
    family_name: str
    due_date: str


@dataclass
class AlertKPI:
    total_active: int
    by_type: dict[str, int]


@dataclass
class EligibleFamilyRow:
    family_id: int
    responsible_name: str
    neighborhood: str
    vulnerability: str
    last_delivery: str
    doc_pending: bool


@dataclass
class DashboardData:
    families: FamilyKPI
    baskets: BasketKPI
    equipment: EquipmentKPI
    visits: VisitKPI
    alerts: AlertKPI
    attended_families: list[AttendedFamilyRow]
    equipment_statuses: list[EquipmentStatusRow]
    eligible_families: list[EligibleFamilyRow]
