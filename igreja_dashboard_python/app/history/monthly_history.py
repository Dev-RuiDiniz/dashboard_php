from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.core.auth import has_permissions, require_roles
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import MonthlyClosure, MonthlyClosureStatus, User

router = APIRouter(tags=["monthly-history"])
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _template_context(request: Request) -> dict[str, object]:
    current_user = getattr(request.state, "user", None)
    return {
        "request": request,
        "app_name": settings.app_name,
        "client_name": settings.client_name,
        "client_department": settings.client_department,
        "status": "OK",
        "app_env": settings.app_env,
        "current_user": current_user,
        "can_manage_users": has_permissions(current_user, {"manage_users"}),
        "can_manage_families": has_permissions(current_user, {"manage_families"}),
        "can_view_equipment": has_permissions(current_user, {"view_equipment"}),
        "can_manage_equipment": has_permissions(current_user, {"manage_equipment"}),
        "can_view_baskets": has_permissions(current_user, {"view_baskets"}),
        "can_manage_baskets": has_permissions(current_user, {"manage_baskets"}),
        "can_view_street": has_permissions(current_user, {"view_street"}),
        "can_manage_street": has_permissions(current_user, {"manage_street"}),
        "can_view_visits": has_permissions(current_user, {"view_visits"}),
        "can_manage_visits": has_permissions(current_user, {"manage_visits"}),
        "can_admin": has_permissions(current_user, {"manage_users"}),
    }


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


def _parse_reference_month(value: str, field: str) -> tuple[int, int]:
    try:
        parsed = datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Parâmetro '{field}' deve estar no formato YYYY-MM.") from exc
    return parsed.year, parsed.month


def _snapshot_from_closure(closure: MonthlyClosure) -> tuple[dict, str]:
    if closure.official_snapshot_json:
        return closure.official_snapshot_json, "official_snapshot_json"
    if closure.summary_snapshot_json:
        return closure.summary_snapshot_json, "summary_snapshot_json"
    return {"totals": {}, "indicators": {}}, "none"


def _referrals_count(raw: object) -> int:
    if isinstance(raw, dict):
        return _to_int(raw.get("total", 0))
    return _to_int(raw)


def _kpis_from_snapshot(snapshot: dict) -> dict[str, int | float | None]:
    totals = snapshot.get("totals", {}) if isinstance(snapshot, dict) else {}
    indicators = snapshot.get("indicators", {}) if isinstance(snapshot, dict) else {}

    avg_vulnerability = _to_float(indicators.get("avg_vulnerability"))
    if avg_vulnerability is None:
        avg_vulnerability = _to_float(totals.get("avg_vulnerability"))

    return {
        "families_attended": _to_int(totals.get("families_attended", 0)),
        "deliveries_count": _to_int(totals.get("deliveries_count", 0)),
        "children_count": _to_int(totals.get("children_count", 0)),
        "referrals_count": _referrals_count(totals.get("referrals_count", 0)),
        "avg_vulnerability": avg_vulnerability,
    }


@router.get("/historico", response_class=HTMLResponse)
def monthly_history_list(
    request: Request,
    year: int | None = Query(default=None),
    status: str | None = Query(default=None),
    db=Depends(get_db),
    _: User = Depends(require_roles("Admin", "Operador", "Leitura")),
):
    query = select(MonthlyClosure)
    if year is not None:
        query = query.where(MonthlyClosure.year == year)
    if status in {"OPEN", "CLOSED"}:
        query = query.where(MonthlyClosure.status == MonthlyClosureStatus(status))

    closures = db.execute(query.order_by(MonthlyClosure.year.desc(), MonthlyClosure.month.desc())).scalars().all()

    rows: list[dict[str, object]] = []
    for closure in closures:
        is_official = bool(closure.official_pdf_path)
        if status == "OFICIAL" and not is_official:
            continue
        snapshot, source = _snapshot_from_closure(closure)
        kpis = _kpis_from_snapshot(snapshot)
        rows.append(
            {
                "year": closure.year,
                "month": closure.month,
                "period": f"{closure.year}-{closure.month:02d}",
                "status": closure.status.value,
                "is_official": is_official,
                "kpis": kpis,
                "source": source,
            }
        )

    years = db.execute(select(MonthlyClosure.year).distinct().order_by(MonthlyClosure.year.desc())).scalars().all()

    context = _template_context(request)
    context.update(
        {
            "rows": rows,
            "filter_year": year,
            "filter_status": status or "",
            "years": years,
        }
    )
    return templates.TemplateResponse("monthly_history_list.html", context)


@router.get("/historico/{year}/{month}", response_class=HTMLResponse)
def monthly_history_detail(
    request: Request,
    year: int,
    month: int,
    db=Depends(get_db),
    _: User = Depends(require_roles("Admin", "Operador", "Leitura")),
):
    closure = db.execute(select(MonthlyClosure).where(MonthlyClosure.year == year, MonthlyClosure.month == month)).scalar_one_or_none()
    if not closure:
        raise HTTPException(status_code=404, detail="Histórico mensal não encontrado.")

    snapshot, source = _snapshot_from_closure(closure)
    kpis = _kpis_from_snapshot(snapshot)

    default_to = f"{year}-{month:02d}"
    default_from = f"{year - 1}-{month:02d}"

    context = _template_context(request)
    context.update(
        {
            "closure": closure,
            "year": year,
            "month": month,
            "period": f"{year}-{month:02d}",
            "kpis": kpis,
            "snapshot_source": source,
            "default_from": default_from,
            "default_to": default_to,
            "has_avg_vulnerability": kpis["avg_vulnerability"] is not None,
        }
    )
    return templates.TemplateResponse("monthly_history_detail.html", context)


@router.get("/api/historico/series")
def monthly_history_series(
    from_period: str = Query(..., alias="from"),
    to_period: str = Query(..., alias="to"),
    db=Depends(get_db),
    _: User = Depends(require_roles("Admin", "Operador", "Leitura")),
):
    from_year, from_month = _parse_reference_month(from_period, "from")
    to_year, to_month = _parse_reference_month(to_period, "to")

    if (from_year, from_month) > (to_year, to_month):
        raise HTTPException(status_code=422, detail="Parâmetro 'from' deve ser menor ou igual a 'to'.")

    closures = db.execute(
        select(MonthlyClosure)
        .where(
            (MonthlyClosure.year > from_year)
            | ((MonthlyClosure.year == from_year) & (MonthlyClosure.month >= from_month)),
            (MonthlyClosure.year < to_year)
            | ((MonthlyClosure.year == to_year) & (MonthlyClosure.month <= to_month)),
        )
        .order_by(MonthlyClosure.year.asc(), MonthlyClosure.month.asc())
    ).scalars().all()

    labels: list[str] = []
    families_attended: list[int] = []
    deliveries_count: list[int] = []
    children_count: list[int] = []
    avg_vulnerability: list[float | None] = []

    for closure in closures:
        snapshot, _ = _snapshot_from_closure(closure)
        kpis = _kpis_from_snapshot(snapshot)
        labels.append(f"{closure.year}-{closure.month:02d}")
        families_attended.append(_to_int(kpis["families_attended"]))
        deliveries_count.append(_to_int(kpis["deliveries_count"]))
        children_count.append(_to_int(kpis["children_count"]))
        avg_vulnerability.append(_to_float(kpis["avg_vulnerability"]))

    return {
        "labels": labels,
        "families_attended": families_attended,
        "deliveries_count": deliveries_count,
        "children_count": children_count,
        "avg_vulnerability": avg_vulnerability,
    }


@router.get("/historico/{year}/{month}/snapshot.json")
def monthly_history_snapshot_json(
    year: int,
    month: int,
    db=Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    closure = db.execute(select(MonthlyClosure).where(MonthlyClosure.year == year, MonthlyClosure.month == month)).scalar_one_or_none()
    if not closure:
        raise HTTPException(status_code=404, detail="Histórico mensal não encontrado.")

    snapshot, source = _snapshot_from_closure(closure)
    return {
        "period": f"{year}-{month:02d}",
        "snapshot_source": source,
        "snapshot": snapshot,
    }
