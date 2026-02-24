from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.closures.monthly_official_pdf import render_official_monthly_pdf
from app.closures.monthly_official_report import build_official_monthly_snapshot
from app.closures.monthly_pdf import render_monthly_closure_pdf
from app.closures.monthly_snapshot import build_monthly_snapshot
from app.core.auth import has_permissions, require_roles
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import MonthlyClosure, MonthlyClosureStatus, User
from app.security.hashing import sha256_hex
from app.services.audit import log_action
from app.storage.filesystem import (
    build_monthly_official_pdf_path,
    build_monthly_pdf_path,
    ensure_reports_dir,
    save_pdf_bytes,
)

router = APIRouter(prefix="/admin/fechamento", tags=["monthly-closure"])
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
        "current_user": current_user,
        "can_manage_users": has_permissions(current_user, {"manage_users"}),
    }


def _get_or_create_closure(db, month: int, year: int) -> MonthlyClosure:
    closure = db.execute(
        select(MonthlyClosure).where(MonthlyClosure.month == month, MonthlyClosure.year == year)
    ).scalar_one_or_none()
    if closure:
        return closure
    closure = MonthlyClosure(month=month, year=year, status=MonthlyClosureStatus.OPEN)
    db.add(closure)
    db.flush()
    return closure


def _get_closed_closure(db, month: int, year: int) -> MonthlyClosure:
    closure = db.execute(
        select(MonthlyClosure).where(
            MonthlyClosure.month == month,
            MonthlyClosure.year == year,
            MonthlyClosure.status == MonthlyClosureStatus.CLOSED,
        )
    ).scalar_one_or_none()
    if not closure:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mês precisa estar CLOSED para gerar relatório oficial.",
        )
    return closure


@router.get("", response_class=HTMLResponse)
def monthly_closure_page(
    request: Request,
    month: int | None = None,
    year: int | None = None,
    db=Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    now = datetime.now(timezone.utc)
    target_month = month or now.month
    target_year = year or now.year
    if not 1 <= target_month <= 12:
        raise HTTPException(status_code=422, detail="Mês inválido.")

    closure = db.execute(
        select(MonthlyClosure).where(MonthlyClosure.month == target_month, MonthlyClosure.year == target_year)
    ).scalar_one_or_none()
    context = _template_context(request)
    context.update(
        {
            "month": target_month,
            "year": target_year,
            "closure": closure,
            "snapshot_json": closure.summary_snapshot_json if closure else None,
        }
    )
    return templates.TemplateResponse("admin_monthly_closure.html", context)


@router.post("/close")
def close_month(
    request: Request,
    month: int = Form(...),
    year: int = Form(...),
    db=Depends(get_db),
    current_user: User = Depends(require_roles("Admin")),
):
    if not 1 <= month <= 12:
        raise HTTPException(status_code=422, detail="Mês inválido.")

    closure = _get_or_create_closure(db, month, year)
    if closure.status == MonthlyClosureStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mês já está fechado.")

    before = {"status": closure.status.value, "month": month, "year": year}
    snapshot = build_monthly_snapshot(db, month=month, year=year, generated_by_user_id=current_user.id)
    pdf_content = render_monthly_closure_pdf(
        snapshot,
        {
            "month": month,
            "year": year,
            "generated_by": current_user.name,
            "generated_at": datetime.now(timezone.utc),
        },
    )
    relative_path = build_monthly_pdf_path(year=year, month=month)
    saved_path = save_pdf_bytes(relative_path, pdf_content)

    closure.status = MonthlyClosureStatus.CLOSED
    closure.closed_by_user_id = current_user.id
    closure.closed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    closure.summary_snapshot_json = snapshot
    closure.pdf_report_path = saved_path

    log_action(
        db,
        current_user.id,
        "MONTH_CLOSE",
        "monthly_closure",
        closure.id,
        before=before,
        after={
            "status": closure.status.value,
            "month": month,
            "year": year,
            "pdf_report_path": closure.pdf_report_path,
        },
    )
    db.commit()
    return RedirectResponse(url=f"/admin/fechamento?month={month}&year={year}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{year}/{month}/gerar-relatorio-oficial")
def generate_official_monthly_report(
    year: int,
    month: int,
    db=Depends(get_db),
    current_user: User = Depends(require_roles("Admin")),
):
    closure = _get_closed_closure(db, month, year)

    previous_official_path = closure.official_pdf_path
    has_official = bool(previous_official_path)
    override_enabled = bool(settings.admin_override)
    if has_official and not override_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Relatório oficial já gerado e é imutável sem ADMIN_OVERRIDE=true.",
        )

    try:
        snapshot_official = build_official_monthly_snapshot(db, month=month, year=year, generated_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    signed_at = datetime.now(timezone.utc)
    pdf_bytes = render_official_monthly_pdf(
        snapshot_official,
        signature={"name": current_user.name, "user_id": current_user.id, "signed_at": signed_at.isoformat()},
        metadata={
            "month": month,
            "year": year,
            "generated_by": current_user.name,
            "generated_at": signed_at,
            "institution": settings.client_name,
        },
    )
    sha256 = sha256_hex(pdf_bytes)

    relative_path = build_monthly_official_pdf_path(year=year, month=month)
    try:
        saved_path = save_pdf_bytes(relative_path, pdf_bytes, overwrite=override_enabled)
    except FileExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Arquivo oficial já existe em storage e sobrescrita está bloqueada.",
        ) from exc

    closure.official_pdf_path = saved_path
    closure.official_pdf_sha256 = sha256
    closure.official_snapshot_json = snapshot_official
    closure.official_signed_by_user_id = current_user.id
    closure.official_signed_at = signed_at.replace(tzinfo=None)

    action = "MONTHLY_OFFICIAL_REPORT_REGENERATED" if has_official and override_enabled else "MONTHLY_OFFICIAL_REPORT_GENERATED"
    log_action(
        db,
        current_user.id,
        action,
        "monthly_closure",
        closure.id,
        before={
            "official_pdf_path": previous_official_path,
        },
        after={
            "path": saved_path,
            "sha256": sha256,
            "signed_by": current_user.id,
            "signed_at": signed_at.isoformat(),
            "override": bool(has_official and override_enabled),
        },
    )

    if has_official and override_enabled:
        log_action(
            db,
            current_user.id,
            "MONTHLY_OFFICIAL_REPORT_OVERRIDE",
            "monthly_closure",
            closure.id,
            before={"admin_override": False},
            after={"admin_override": True},
        )

    db.commit()
    return RedirectResponse(url=f"/admin/fechamento?month={month}&year={year}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/reopen")
def reopen_month_disabled(
    _: User = Depends(require_roles("Admin")),
):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Reabertura de mês desabilitada.")


@router.get("/{year}/{month}/pdf")
def download_monthly_pdf(
    year: int,
    month: int,
    db=Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    closure = db.execute(
        select(MonthlyClosure).where(
            MonthlyClosure.month == month,
            MonthlyClosure.year == year,
            MonthlyClosure.status == MonthlyClosureStatus.CLOSED,
        )
    ).scalar_one_or_none()
    if not closure or not closure.pdf_report_path:
        raise HTTPException(status_code=404, detail="PDF oficial não encontrado para o mês.")

    file_path = ensure_reports_dir() / Path(closure.pdf_report_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado no storage local.")

    return FileResponse(file_path, media_type="application/pdf", filename=file_path.name)


@router.get("/{year}/{month}/relatorio-oficial.pdf")
def download_official_monthly_pdf(
    year: int,
    month: int,
    db=Depends(get_db),
    _: User = Depends(require_roles("Admin", "Operador", "Leitura")),
):
    closure = _get_closed_closure(db, month, year)
    if not closure.official_pdf_path:
        raise HTTPException(status_code=404, detail="Relatório oficial ainda não foi gerado para o mês.")

    file_path = ensure_reports_dir() / Path(closure.official_pdf_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo PDF oficial não encontrado no storage local.")

    response = FileResponse(file_path, media_type="application/pdf", filename=file_path.name)
    if closure.official_pdf_sha256:
        response.headers["X-Content-SHA256"] = closure.official_pdf_sha256
    return response


@router.get("/{year}/{month}/snapshot.json")
def monthly_snapshot_json(
    year: int,
    month: int,
    db=Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    closure = db.execute(
        select(MonthlyClosure).where(
            MonthlyClosure.month == month,
            MonthlyClosure.year == year,
            MonthlyClosure.status == MonthlyClosureStatus.CLOSED,
        )
    ).scalar_one_or_none()
    if not closure:
        raise HTTPException(status_code=404, detail="Fechamento não encontrado.")
    return closure.summary_snapshot_json or {}


@router.get("/{year}/{month}/relatorio-oficial.snapshot.json")
def monthly_official_snapshot_json(
    year: int,
    month: int,
    db=Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    closure = _get_closed_closure(db, month, year)
    if not closure.official_snapshot_json:
        raise HTTPException(status_code=404, detail="Relatório oficial ainda não foi gerado para o mês.")
    return closure.official_snapshot_json
