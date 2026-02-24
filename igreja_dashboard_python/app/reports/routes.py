from __future__ import annotations

from datetime import date
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from app.core.auth import has_permissions, require_permissions
from app.core.config import settings
from app.db.session import SessionLocal
from app.pdf import generate_report_pdf
from app.reports import queries
from app.reports.exporters import build_csv, build_xlsx

router = APIRouter(prefix="/relatorios", tags=["reports"])
logger = logging.getLogger("app.audit")


def _parse_optional_int(value: str | None, field_name: str) -> int | None:
    if value is None:
        return None

    cleaned = value.strip()
    if cleaned == "":
        return None

    try:
        parsed = int(cleaned)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "type": "int_parsing",
                    "loc": ["query", field_name],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                    "input": value,
                }
            ],
        ) from exc

    if field_name == "month" and not 1 <= parsed <= 12:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "type": "less_than_equal",
                    "loc": ["query", "month"],
                    "msg": "Input should be less than or equal to 12",
                    "input": parsed,
                    "ctx": {"le": 12},
                }
            ],
        )

    return parsed
templates = Jinja2Templates(directory="templates")


def get_db():
    try:
        db = SessionLocal()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao abrir sessão de relatórios.")
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


def _resolve_rows(db, report_type: str, year: int | None, month: int | None):
    if report_type == "familias":
        data = queries.families_report(db)
        headers = ["Responsável", "CPF", "Status", "Vulnerabilidade"]
        rows = [
            [
                family.responsible_name,
                family.responsible_cpf,
                "Ativa" if family.is_active else "Inativa",
                family.vulnerability.value,
            ]
            for family in data
        ]
        return headers, rows

    if report_type == "cestas":
        data = queries.baskets_report(db, year=year, month=month)
        headers = ["Família", "Período", "Status"]
        rows = [
            [
                basket.family.responsible_name,
                f"{basket.reference_month:02d}/{basket.reference_year}",
                basket.status.value,
            ]
            for basket in data
        ]
        return headers, rows

    if report_type == "equipamentos":
        data = queries.equipment_report(db)
        headers = ["Equipamento", "Família", "Status", "Data empréstimo", "Previsão devolução"]
        rows = [
            [
                loan.equipment.code,
                loan.family.responsible_name,
                loan.status.value,
                loan.loan_date.isoformat(),
                loan.due_date.isoformat() if loan.due_date else "-",
            ]
            for loan in data
        ]
        return headers, rows

    if report_type == "criancas":
        data = queries.children_report(db)
        headers = ["Nome", "Nascimento", "Sexo", "Família"]
        rows = [
            [
                child.name,
                child.birth_date.isoformat(),
                child.sex.value,
                child.family.responsible_name if child.family else "-",
            ]
            for child in data
        ]
        return headers, rows

    if report_type == "encaminhamentos":
        data = queries.referrals_report(db)
        headers = ["Pessoa", "Casa de recuperação", "Data", "Status"]
        rows = [
            [
                referral.person.full_name if referral.person and referral.person.full_name else "Não informado",
                referral.recovery_home,
                referral.referral_date.isoformat(),
                referral.status.value,
            ]
            for referral in data
        ]
        return headers, rows

    if report_type == "visitas":
        data = queries.visits_report(db, year=year, month=month)
        headers = ["Família", "Data agendada", "Status", "Solicitação"]
        rows = [
            [
                item.family.responsible_name,
                item.scheduled_date.isoformat(),
                item.status.value,
                item.request_notes or "-",
            ]
            for item in data
        ]
        return headers, rows

    if report_type == "rua":
        data = queries.street_people_report(db)
        headers = ["Nome", "Local referência", "Qtd. atendimentos", "Último encaminhamento"]
        rows = [
            [
                item["name"],
                item["reference_location"],
                item["service_count"],
                item["last_referral_status"],
            ]
            for item in data
        ]
        return headers, rows

    if report_type == "bairros":
        data = queries.neighborhood_report(db, year=year, month=month)
        headers = ["Bairro", "Total famílias", "Total cestas", "Total alertas"]
        rows = [
            [
                item["neighborhood"],
                item["families_total"],
                item["baskets_total"],
                item["alerts_total"],
            ]
            for item in data
        ]
        return headers, rows

    data = queries.alerts_report(db)
    headers = ["Família", "Tipo", "Tempo"]
    rows = [[item["family"], item["type"], item["duration"]] for item in data]
    return headers, rows


def _totals_for_report(report_type: str, rows: list[list[object]]) -> str:
    total = len(rows)
    if report_type == "cestas":
        return f"Total de registros: {total} | Total de cestas: {total}"
    if report_type == "criancas":
        return f"Total de registros: {total} | Total de crianças: {total}"
    if report_type == "encaminhamentos":
        return f"Total de registros: {total} | Total de encaminhamentos: {total}"
    if report_type == "equipamentos":
        return f"Total de registros: {total} | Total de empréstimos: {total}"
    if report_type in {"alertas", "pendencias"}:
        return f"Total de registros: {total} | Total de pendências: {total}"
    return f"Total de registros: {total}"


def _report_title(report_type: str) -> str:
    mapping = {
        "familias": "Relatório de Famílias",
        "cestas": "Relatório de Cestas",
        "criancas": "Relatório de Crianças",
        "encaminhamentos": "Relatório de Encaminhamentos",
        "equipamentos": "Relatório de Equipamentos",
        "pendencias": "Relatório de Pendências",
        "alertas": "Relatório de Pendências",
    }
    return mapping.get(report_type, f"Relatório {report_type.title()}")


def _normalize_report_type(report_type: str) -> str:
    if report_type == "pendencias":
        return "alertas"
    return report_type


def _build_pdf_response(
    report_type: str,
    year: int | None,
    month: int | None,
    headers: list[str],
    rows: list[list[object]],
    generated_by: str,
) -> Response:
    normalized = _normalize_report_type(report_type)
    title = _report_title(report_type)
    sections = [
        {
            "type": "table",
            "title": "Dados",
            "headers": headers,
            "rows": rows,
        },
        {
            "type": "text",
            "title": "Totalizadores",
            "content": _totals_for_report(normalized, rows),
        },
    ]
    content = generate_report_pdf(
        title=title,
        month=month,
        year=year,
        sections=sections,
        metadata={
            "generated_by": generated_by,
            "generated_at": datetime.now(),
            "institution": "Primeira Igreja Batista de Taubaté",
        },
    )
    filename = f"relatorio-{report_type}-{date.today().isoformat()}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("", response_class=HTMLResponse)
def reports_page(
    request: Request,
    report_type: str = Query(default="familias"),
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    db=Depends(get_db),
    _=Depends(
        require_permissions(
            "view_families", "view_equipment", "view_baskets", "view_street", "view_visits"
        )
    ),
) -> HTMLResponse:
    parsed_year = _parse_optional_int(year, "year")
    parsed_month = _parse_optional_int(month, "month")
    headers, rows = _resolve_rows(db, report_type, parsed_year, parsed_month)
    context = template_context(request)
    context.update(
        {
            "report_type": report_type,
            "headers": headers,
            "rows": rows,
            "year": parsed_year,
            "month": parsed_month,
        }
    )
    return templates.TemplateResponse("reports/reports.html", context)


@router.get("/export.csv")
def export_csv(
    report_type: str = Query(default="familias"),
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    db=Depends(get_db),
    _=Depends(
        require_permissions(
            "manage_families",
            "manage_equipment",
            "manage_baskets",
            "manage_street",
            "manage_visits",
        )
    ),
) -> Response:
    parsed_year = _parse_optional_int(year, "year")
    parsed_month = _parse_optional_int(month, "month")
    normalized = _normalize_report_type(report_type)
    headers, rows = _resolve_rows(db, normalized, parsed_year, parsed_month)
    content = build_csv(headers, rows)
    filename = f"relatorio-{report_type}-{date.today().isoformat()}.csv"
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export.xlsx")
def export_xlsx(
    report_type: str = Query(default="familias"),
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    db=Depends(get_db),
    _=Depends(
        require_permissions(
            "manage_families",
            "manage_equipment",
            "manage_baskets",
            "manage_street",
            "manage_visits",
        )
    ),
) -> Response:
    parsed_year = _parse_optional_int(year, "year")
    parsed_month = _parse_optional_int(month, "month")
    normalized = _normalize_report_type(report_type)
    headers, rows = _resolve_rows(db, normalized, parsed_year, parsed_month)
    content = build_xlsx(normalized.capitalize(), headers, rows)
    filename = f"relatorio-{report_type}-{date.today().isoformat()}.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/familias.pdf")
def report_familias_pdf(
    request: Request,
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    db=Depends(get_db),
    _=Depends(require_permissions("view_families")),
) -> Response:
    parsed_year = _parse_optional_int(year, "year")
    parsed_month = _parse_optional_int(month, "month")
    headers, rows = _resolve_rows(db, "familias", parsed_year, parsed_month)
    current_user = getattr(request.state, "user", None)
    return _build_pdf_response(
        "familias",
        parsed_year,
        parsed_month,
        headers,
        rows,
        getattr(current_user, "name", "Sistema"),
    )


@router.get("/cestas.pdf")
def report_cestas_pdf(
    request: Request,
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    db=Depends(get_db),
    _=Depends(require_permissions("view_baskets")),
) -> Response:
    parsed_year = _parse_optional_int(year, "year")
    parsed_month = _parse_optional_int(month, "month")
    headers, rows = _resolve_rows(db, "cestas", parsed_year, parsed_month)
    current_user = getattr(request.state, "user", None)
    return _build_pdf_response(
        "cestas", parsed_year, parsed_month, headers, rows, getattr(current_user, "name", "Sistema")
    )


@router.get("/criancas.pdf")
def report_criancas_pdf(
    request: Request,
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    db=Depends(get_db),
    _=Depends(require_permissions("view_families")),
) -> Response:
    parsed_year = _parse_optional_int(year, "year")
    parsed_month = _parse_optional_int(month, "month")
    headers, rows = _resolve_rows(db, "criancas", parsed_year, parsed_month)
    current_user = getattr(request.state, "user", None)
    return _build_pdf_response(
        "criancas", parsed_year, parsed_month, headers, rows, getattr(current_user, "name", "Sistema")
    )


@router.get("/encaminhamentos.pdf")
def report_encaminhamentos_pdf(
    request: Request,
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    db=Depends(get_db),
    _=Depends(require_permissions("view_street")),
) -> Response:
    parsed_year = _parse_optional_int(year, "year")
    parsed_month = _parse_optional_int(month, "month")
    headers, rows = _resolve_rows(db, "encaminhamentos", parsed_year, parsed_month)
    current_user = getattr(request.state, "user", None)
    return _build_pdf_response(
        "encaminhamentos",
        parsed_year,
        parsed_month,
        headers,
        rows,
        getattr(current_user, "name", "Sistema"),
    )


@router.get("/equipamentos.pdf")
def report_equipamentos_pdf(
    request: Request,
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    db=Depends(get_db),
    _=Depends(require_permissions("view_equipment")),
) -> Response:
    parsed_year = _parse_optional_int(year, "year")
    parsed_month = _parse_optional_int(month, "month")
    headers, rows = _resolve_rows(db, "equipamentos", parsed_year, parsed_month)
    current_user = getattr(request.state, "user", None)
    return _build_pdf_response(
        "equipamentos",
        parsed_year,
        parsed_month,
        headers,
        rows,
        getattr(current_user, "name", "Sistema"),
    )


@router.get("/pendencias.pdf")
def report_pendencias_pdf(
    request: Request,
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    db=Depends(get_db),
    _=Depends(require_permissions("view_families", "view_baskets", "view_equipment", "view_visits")),
) -> Response:
    parsed_year = _parse_optional_int(year, "year")
    parsed_month = _parse_optional_int(month, "month")
    headers, rows = _resolve_rows(db, "alertas", parsed_year, parsed_month)
    current_user = getattr(request.state, "user", None)
    return _build_pdf_response(
        "pendencias", parsed_year, parsed_month, headers, rows, getattr(current_user, "name", "Sistema")
    )
