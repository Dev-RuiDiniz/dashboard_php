from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.auth import has_permissions, require_permissions
from app.core.config import settings
from app.dashboard import queries
from app.dashboard.service import build_dashboard_data
from app.db.session import SessionLocal

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger("app.audit")


def get_db():
    try:
        db = SessionLocal()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao abrir sessão do dashboard.")
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.") from exc
    try:
        yield db
    finally:
        db.close()


def template_context(request: Request) -> dict[str, object]:
    current_user = getattr(request.state, "user", None)
    return {
        "request": request,
        "app_name": settings.app_name,
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
    }


@router.get("", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    neighborhood: str | None = Query(default=None),
    eligible_limit: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db),
    _=Depends(require_permissions("view_families", "view_equipment", "view_baskets")),
) -> HTMLResponse:
    dashboard = build_dashboard_data(db, neighborhood=neighborhood, eligible_limit=eligible_limit)
    context = template_context(request)
    context.update({"dashboard": dashboard, "eligible_filters": {"neighborhood": neighborhood or "", "eligible_limit": eligible_limit}})
    return templates.TemplateResponse("dashboard/dashboard.html", context)


@router.get("/mapa-calor-bairros", response_class=HTMLResponse)
def neighborhood_heatmap_page(
    request: Request,
    city: str | None = Query(default=None),
    state: str | None = Query(default=None),
    db=Depends(get_db),
    _=Depends(require_permissions("view_families")),
) -> HTMLResponse:
    rows = queries.neighborhood_heatmap(db, city=city, state=state)
    max_total = max((row["active_families"] for row in rows), default=0)
    context = template_context(request)
    context.update(
        {
            "rows": rows,
            "max_total": max_total,
            "filters": {"city": city or "", "state": state or ""},
        }
    )
    return templates.TemplateResponse("dashboard/neighborhood_heatmap.html", context)
