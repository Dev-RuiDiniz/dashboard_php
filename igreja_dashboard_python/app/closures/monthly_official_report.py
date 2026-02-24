from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.models import MonthlyClosure, MonthlyClosureStatus

TRACKED_KPIS = [
    "families_attended",
    "people_followed",
    "children_count",
    "deliveries_count",
    "referrals_count",
    "visits_count",
    "loans_count",
    "pending_docs_count",
    "pending_visits_count",
    "avg_vulnerability",
]

VULNERABILITY_SCORE = {
    "Sem vulnerabilidade": 0,
    "Baixa": 1,
    "Média": 2,
    "Alta": 3,
    "Extrema": 4,
}


def _month_back(month: int, year: int) -> tuple[int, int]:
    if month == 1:
        return 12, year - 1
    return month - 1, year


def _to_int(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _read_totals(snapshot: dict) -> dict[str, int | float | None]:
    totals = snapshot.get("totals", {}) if isinstance(snapshot, dict) else {}
    indicators = snapshot.get("indicators", {}) if isinstance(snapshot, dict) else {}

    referrals_value = totals.get("referrals_count", 0)
    if isinstance(referrals_value, dict):
        referrals_count = _to_int(referrals_value.get("total", 0))
    else:
        referrals_count = _to_int(referrals_value)

    loans_value = totals.get("loans_count")
    if loans_value is None:
        loans_value = totals.get("equipment_loans_count", 0)

    people_followed = totals.get("people_followed")
    if people_followed is None:
        people_followed = totals.get("street_services_count", 0)

    avg_vulnerability = _to_float(indicators.get("avg_vulnerability"))
    if avg_vulnerability is None:
        avg_vulnerability = _to_float(totals.get("avg_vulnerability"))

    return {
        "families_attended": _to_int(totals.get("families_attended", 0)),
        "people_followed": _to_int(people_followed),
        "children_count": _to_int(totals.get("children_count", 0)),
        "deliveries_count": _to_int(totals.get("deliveries_count", 0)),
        "referrals_count": referrals_count,
        "visits_count": _to_int(totals.get("visits_count", 0)),
        "loans_count": _to_int(loans_value),
        "pending_docs_count": _to_int(totals.get("pending_docs_count", 0)),
        "pending_visits_count": _to_int(totals.get("pending_visits_count", 0)),
        "avg_vulnerability": avg_vulnerability,
    }


def _extract_by_neighborhood(snapshot: dict) -> list[dict]:
    if not isinstance(snapshot, dict):
        return []

    source = snapshot.get("by_neighborhood")
    if isinstance(source, list):
        return source

    breakdowns = snapshot.get("breakdowns", {})
    if isinstance(breakdowns, dict):
        values = breakdowns.get("by_neighborhood")
        if isinstance(values, list):
            return values
    return []


def _derive_avg_vulnerability(snapshot: dict) -> float | None:
    level_counts = (
        snapshot.get("breakdowns", {}).get("families_by_vulnerability", {})
        if isinstance(snapshot, dict)
        else {}
    )
    if not isinstance(level_counts, dict) or not level_counts:
        return None

    total = 0
    weight = 0
    for level, amount in level_counts.items():
        count = _to_int(amount)
        weight += VULNERABILITY_SCORE.get(level, 0) * count
        total += count
    if total == 0:
        return None
    return round(weight / total, 2)


def compute_month_over_month_delta(current: dict, previous: dict | None) -> dict:
    deltas: dict[str, dict[str, object]] = {}
    current_totals = _read_totals(current)
    previous_totals = _read_totals(previous or {}) if previous else {}

    for kpi in TRACKED_KPIS:
        curr = current_totals.get(kpi)
        prev = previous_totals.get(kpi) if previous else None

        if isinstance(curr, float) or isinstance(prev, float):
            curr_num = _to_float(curr)
            prev_num = _to_float(prev)
        else:
            curr_num = float(_to_int(curr))
            prev_num = float(_to_int(prev)) if previous else None

        absolute = None if prev_num is None or curr_num is None else round(curr_num - prev_num, 2)
        percent: float | str | None
        if prev_num in (None, 0) or curr_num is None:
            percent = "N/A"
        else:
            percent = round(((curr_num - prev_num) / prev_num) * 100, 2)

        deltas[kpi] = {
            "current": curr,
            "previous": prev,
            "absolute": absolute,
            "percent": percent,
        }

    return deltas


def build_previous_month_snapshot(db, month: int, year: int) -> dict | None:
    prev_month, prev_year = _month_back(month, year)
    previous = db.execute(
        select(MonthlyClosure).where(
            MonthlyClosure.month == prev_month,
            MonthlyClosure.year == prev_year,
            MonthlyClosure.status == MonthlyClosureStatus.CLOSED,
        )
    ).scalar_one_or_none()
    if not previous:
        return None

    return previous.official_snapshot_json or previous.summary_snapshot_json


def build_official_monthly_snapshot(db, month: int, year: int, generated_by: int | None = None) -> dict:
    closure = db.execute(
        select(MonthlyClosure).where(
            MonthlyClosure.month == month,
            MonthlyClosure.year == year,
            MonthlyClosure.status == MonthlyClosureStatus.CLOSED,
        )
    ).scalar_one_or_none()

    if not closure or not closure.summary_snapshot_json:
        raise ValueError("Mês precisa estar CLOSED para gerar relatório oficial.")

    base_snapshot = closure.summary_snapshot_json
    previous_snapshot = build_previous_month_snapshot(db, month, year)

    totals = _read_totals(base_snapshot)
    if totals["avg_vulnerability"] is None:
        totals["avg_vulnerability"] = _derive_avg_vulnerability(base_snapshot)

    official_snapshot = {
        "totals": totals,
        "indicators": {
            "avg_vulnerability": totals["avg_vulnerability"],
            "pending_docs_count": totals["pending_docs_count"],
            "pending_visits_count": totals["pending_visits_count"],
            "other_pending": base_snapshot.get("indicators", {}).get("other_pending", []),
        },
        "by_neighborhood": _extract_by_neighborhood(base_snapshot),
        "mom": compute_month_over_month_delta({"totals": totals}, previous_snapshot),
        "metadata": {
            "month": month,
            "year": year,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": generated_by,
            "sources": base_snapshot.get("metadata", {}).get("data_sources", []),
            "comparison_base": "previous_closed_month" if previous_snapshot else "none",
        },
    }
    return official_snapshot
