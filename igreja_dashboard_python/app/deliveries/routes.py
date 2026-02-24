from __future__ import annotations

from datetime import date, datetime
import logging
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.closures.lock_guard import require_month_open
from app.core.auth import has_permissions, require_permissions, require_roles
from app.core.config import settings
from app.eligibility.engine import get_system_settings, list_eligible_families
from app.db.session import SessionLocal
from app.models import (
    Child,
    DeliveryEvent,
    DeliveryEventStatus,
    DeliveryInvite,
    DeliveryInviteStatus,
    DeliveryWithdrawal,
    Family,
    User,
)
from app.pdf import generate_report_pdf
from app.reports.exporters import build_csv, build_xlsx
from app.services.audit import log_action

router = APIRouter(prefix="/entregas", tags=["deliveries"])
logger = logging.getLogger("app.audit")
templates = Jinja2Templates(directory="templates")


class EventCreatePayload(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str | None = None
    event_date: date
    has_children_list: bool = False


class InvitePayload(BaseModel):
    mode: str = Field(pattern="^(manual|automatic)$")
    family_ids: list[int] = Field(default_factory=list)


class WithdrawalPayload(BaseModel):
    signature_name: str = Field(min_length=2, max_length=120)
    signature_accepted: bool
    notes: str | None = None


class EventClosePayload(BaseModel):
    notes: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _generate_withdrawal_code(db, event_id: int) -> str:
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(20):
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        exists = db.execute(
            select(DeliveryInvite.id).where(
                DeliveryInvite.event_id == event_id,
                DeliveryInvite.withdrawal_code == code,
            )
        ).scalar_one_or_none()
        if not exists:
            return code
    raise HTTPException(status_code=500, detail="Falha ao gerar código de retirada único.")


def _eligible_families_auto(db) -> list[Family]:
    settings_row = get_system_settings(db)
    limit = settings.event_delivery_monthly_limit or 100
    rows = list_eligible_families(db, settings=settings_row, limit=limit)
    return [row["family"] for row in rows]


@router.post("/eventos")
def create_delivery_event(
    payload: EventCreatePayload,
    db=Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Operador")),
):
    require_month_open(db, target_date=payload.event_date)
    event = DeliveryEvent(
        title=payload.title.strip(),
        description=(payload.description or "").strip() or None,
        event_date=payload.event_date,
        created_by_user_id=current_user.id,
        has_children_list=payload.has_children_list,
    )
    db.add(event)
    db.flush()
    log_action(db, current_user.id, "CREATE_EVENT", "delivery_event", event.id, after={"title": event.title, "event_date": event.event_date, "status": event.status})
    db.commit()
    db.refresh(event)
    return {
        "id": event.id,
        "title": event.title,
        "event_date": event.event_date.isoformat(),
        "status": event.status.value,
        "has_children_list": event.has_children_list,
    }


@router.get("/eventos")
def list_delivery_events(
    db=Depends(get_db),
    _current_user: User = Depends(require_permissions("view_families")),
):
    events = (
        db.execute(select(DeliveryEvent).order_by(DeliveryEvent.event_date.desc(), DeliveryEvent.id.desc()))
        .scalars()
        .all()
    )
    return [
        {
            "id": event.id,
            "title": event.title,
            "event_date": event.event_date.isoformat(),
            "status": event.status.value,
            "has_children_list": event.has_children_list,
        }
        for event in events
    ]


@router.post("/eventos/{event_id}/convidar")
def invite_families(
    event_id: int,
    payload: InvitePayload,
    db=Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Operador")),
):
    event = db.get(DeliveryEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    require_month_open(db, target_date=event.event_date)

    if payload.mode == "manual":
        if not payload.family_ids:
            raise HTTPException(
                status_code=400, detail="Informe ao menos uma família para convite manual."
            )
        families = (
            db.execute(
                select(Family).where(Family.id.in_(payload.family_ids)).order_by(Family.id.asc())
            )
            .scalars()
            .all()
        )
    else:
        families = _eligible_families_auto(db)

    if not families:
        return {"event_id": event_id, "invited": 0, "family_ids": []}

    invited_ids: list[int] = []
    for family in families:
        if not family.is_active:
            if payload.mode == "manual":
                raise HTTPException(
                    status_code=400,
                    detail=f"Família inativa não pode ser convidada: {family.id}.",
                )
            continue

        existing = db.execute(
            select(DeliveryInvite.id).where(
                DeliveryInvite.event_id == event_id,
                DeliveryInvite.family_id == family.id,
            )
        ).scalar_one_or_none()
        if existing:
            continue

        invite = DeliveryInvite(
            event_id=event_id,
            family_id=family.id,
            withdrawal_code=_generate_withdrawal_code(db, event_id),
            status=DeliveryInviteStatus.INVITED,
        )
        db.add(invite)
        invited_ids.append(family.id)

    db.flush()
    log_action(db, current_user.id, "INVITE_FAMILIES", "delivery_event", event.id, after={"invited_count": len(invited_ids), "mode": payload.mode})
    db.commit()
    return {"event_id": event_id, "invited": len(invited_ids), "family_ids": invited_ids}


@router.post("/eventos/{event_id}/retirada/{family_id}")
def register_withdrawal(
    event_id: int,
    family_id: int,
    payload: WithdrawalPayload,
    db=Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Operador")),
):
    event = db.get(DeliveryEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    require_month_open(db, target_date=event.event_date)
    if event.status != DeliveryEventStatus.OPEN:
        raise HTTPException(status_code=400, detail="Evento fechado: retirada não permitida.")
    if payload.signature_accepted is not True:
        raise HTTPException(
            status_code=400, detail="Assinatura deve ser aceita para confirmar retirada."
        )

    invite = db.execute(
        select(DeliveryInvite).where(
            DeliveryInvite.event_id == event_id,
            DeliveryInvite.family_id == family_id,
        )
    ).scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="Família não foi convidada para este evento.")

    already = db.execute(
        select(DeliveryWithdrawal.id).where(
            DeliveryWithdrawal.event_id == event_id,
            DeliveryWithdrawal.family_id == family_id,
        )
    ).scalar_one_or_none()
    if already:
        raise HTTPException(
            status_code=409, detail="Retirada já registrada para a família neste evento."
        )

    withdrawal = DeliveryWithdrawal(
        event_id=event_id,
        family_id=family_id,
        confirmed_by_user_id=current_user.id,
        signature_name=payload.signature_name.strip(),
        signature_accepted=payload.signature_accepted,
        notes=(payload.notes or "").strip() or None,
    )
    db.add(withdrawal)
    invite.status = DeliveryInviteStatus.WITHDRAWN

    try:
        db.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Retirada duplicada bloqueada.") from exc

    log_action(
        db,
        current_user.id,
        "CONFIRM_WITHDRAWAL",
        "delivery_withdrawal",
        withdrawal.id,
        after={
            "event_id": event_id,
            "family_id": family_id,
            "signature_accepted": payload.signature_accepted,
        },
    )
    db.commit()
    return {"event_id": event_id, "family_id": family_id, "status": "WITHDRAWN"}


@router.post("/eventos/{event_id}/close")
def close_event(
    event_id: int,
    payload: EventClosePayload,
    db=Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Operador")),
):
    event = db.get(DeliveryEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    if event.status == DeliveryEventStatus.CLOSED:
        raise HTTPException(status_code=409, detail="Evento já encerrado.")

    event.status = DeliveryEventStatus.CLOSED
    db.flush()
    log_action(
        db,
        current_user.id,
        "CLOSE_EVENT",
        "delivery_event",
        event.id,
        after={"status": event.status.value, "notes": (payload.notes or "").strip() or None},
    )
    db.commit()
    return {"event_id": event.id, "status": event.status.value}


def _event_export_rows(db, event_id: int) -> tuple[str, list[str], list[list[object]]]:
    event = db.execute(
        select(DeliveryEvent)
        .options(
            selectinload(DeliveryEvent.invites).selectinload(DeliveryInvite.family),
            selectinload(DeliveryEvent.withdrawals),
        )
        .where(DeliveryEvent.id == event_id)
    ).scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    withdrawals_map = {item.family_id: item for item in event.withdrawals}
    headers = [
        "Família",
        "CPF responsável",
        "Bairro",
        "Código retirada",
        "Status",
        "Confirmado por",
        "Data confirmação",
    ]
    rows: list[list[object]] = []
    for invite in event.invites:
        family = invite.family
        withdrawal = withdrawals_map.get(invite.family_id)
        rows.append(
            [
                family.responsible_name if family else "-",
                family.responsible_cpf if family else "-",
                family.neighborhood if family and family.neighborhood else "-",
                invite.withdrawal_code,
                invite.status.value,
                withdrawal.confirmed_by_user_id if withdrawal else "-",
                withdrawal.confirmed_at.isoformat() if withdrawal else "-",
            ]
        )
    return event.title, headers, rows


@router.get("/eventos/{event_id}/export.csv")
def export_event_csv(
    event_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Operador")),
):
    _, headers, rows = _event_export_rows(db, event_id)
    csv_content = build_csv(headers, rows)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="entregas-evento-{event_id}.csv"'},
    )


@router.get("/eventos/{event_id}/export.xlsx")
def export_event_xlsx(
    event_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Operador")),
):
    title, headers, rows = _event_export_rows(db, event_id)
    xlsx_content = build_xlsx(title[:31] or "Evento", headers, rows)
    return Response(
        content=xlsx_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="entregas-evento-{event_id}.xlsx"'},
    )


def _template_context(request: Request) -> dict[str, object]:
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


def _mask_cpf(value: str) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if len(digits) != 11:
        return "-"
    return f"***.***.***-{digits[-2:]}"


def _calculate_age(birth_date: date) -> int:
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def _event_children_rows(db, event_id: int) -> tuple[DeliveryEvent, list[dict[str, object]]]:
    event = db.get(DeliveryEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    if not event.has_children_list:
        return event, []

    confirmed_family_ids = (
        db.execute(
            select(DeliveryInvite.family_id).where(
                DeliveryInvite.event_id == event_id,
                DeliveryInvite.status == DeliveryInviteStatus.WITHDRAWN,
            )
        )
        .scalars()
        .all()
    )

    if not confirmed_family_ids:
        return event, []

    children = (
        db.execute(
            select(Child)
            .options(selectinload(Child.family))
            .where(Child.family_id.in_(confirmed_family_ids))
            .order_by(Child.name.asc())
        )
        .scalars()
        .all()
    )

    rows: list[dict[str, object]] = []
    for child in children:
        family = child.family
        rows.append(
            {
                "name": child.name,
                "age": _calculate_age(child.birth_date),
                "sex": child.sex.value,
                "family_name": family.responsible_name if family else "-",
                "neighborhood": family.neighborhood if family and family.neighborhood else "-",
                "responsible_name": family.responsible_name if family else "-",
                "responsible_cpf_masked": _mask_cpf(family.responsible_cpf if family else ""),
            }
        )
    return event, rows


@router.get("/eventos/{event_id}/criancas", response_class=HTMLResponse)
def event_children_list(
    request: Request,
    event_id: int,
    db=Depends(get_db),
    _current_user: User = Depends(require_permissions("view_families")),
):
    event, rows = _event_children_rows(db, event_id)
    context = _template_context(request)
    context.update({"event": event, "children": rows})
    return templates.TemplateResponse("event_children_list.html", context)


def _children_export_table(
    db, event_id: int
) -> tuple[DeliveryEvent, list[str], list[list[object]]]:
    event, rows = _event_children_rows(db, event_id)
    headers = [
        "Nome criança",
        "Idade",
        "Sexo",
        "Família",
        "Bairro",
        "Responsável",
        "CPF responsável",
    ]
    table_rows = [
        [
            row["name"],
            row["age"],
            row["sex"],
            row["family_name"],
            row["neighborhood"],
            row["responsible_name"],
            row["responsible_cpf_masked"],
        ]
        for row in rows
    ]
    return event, headers, table_rows


@router.get("/eventos/{event_id}/criancas/export.xlsx")
def export_event_children_xlsx(
    event_id: int,
    db=Depends(get_db),
    _current_user: User = Depends(require_permissions("view_families")),
):
    event, headers, rows = _children_export_table(db, event_id)
    xlsx_content = build_xlsx((event.title[:31] or "Criancas"), headers, rows)
    return Response(
        content=xlsx_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": (
                f'attachment; filename="entregas-evento-{event_id}-criancas.xlsx"'
            )
        },
    )


@router.get("/eventos/{event_id}/criancas/export.pdf")
def export_event_children_pdf(
    request: Request,
    event_id: int,
    db=Depends(get_db),
    _current_user: User = Depends(require_permissions("view_families")),
):
    event, headers, rows = _children_export_table(db, event_id)
    current_user = getattr(request.state, "user", None)
    pdf_content = generate_report_pdf(
        title=f"Lista de Crianças — Evento {event.title}",
        month=event.event_date.month,
        year=event.event_date.year,
        sections=[
            {
                "type": "table",
                "title": "Crianças confirmadas",
                "headers": headers,
                "rows": rows,
            },
            {
                "type": "text",
                "title": "Totalizadores",
                "content": f"Total de registros: {len(rows)} | Total de crianças: {len(rows)}",
            },
        ],
        metadata={
            "generated_by": getattr(current_user, "name", "Sistema"),
            "generated_at": datetime.now(),
            "institution": "Primeira Igreja Batista de Taubaté",
        },
    )
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="entregas-evento-{event_id}-criancas.pdf"'
        },
    )


@router.get("/eventos/{event_id}/export.pdf")
def export_event_pdf(
    request: Request,
    event_id: int,
    db=Depends(get_db),
    _current_user: User = Depends(require_permissions("view_families")),
):
    title, headers, rows = _event_export_rows(db, event_id)
    current_user = getattr(request.state, "user", None)
    pdf_content = generate_report_pdf(
        title=f"Evento de Entrega: {title}",
        month=None,
        year=None,
        sections=[
            {
                "type": "table",
                "title": "Convidados e retiradas",
                "headers": headers,
                "rows": rows,
            },
            {
                "type": "text",
                "title": "Totalizadores",
                "content": f"Total de registros: {len(rows)} | Total convidados: {len(rows)}",
            },
        ],
        metadata={
            "generated_by": getattr(current_user, "name", "Sistema"),
            "generated_at": datetime.now(),
            "institution": "Primeira Igreja Batista de Taubaté",
        },
    )
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="entregas-evento-{event_id}.pdf"'},
    )
