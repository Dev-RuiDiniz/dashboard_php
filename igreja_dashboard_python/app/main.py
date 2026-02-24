from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
import hashlib
import logging
import secrets
import re
from time import perf_counter
from uuid import uuid4

from fastapi import Body, Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.closures.lock_guard import require_month_open
from app.core.auth import ROLE_DEFINITIONS, get_current_user, has_permissions, require_permissions, require_roles
from app.core.auth_cookie import AUTH_COOKIE_NAME, clear_auth_cookie, debug_auth, set_auth_cookie
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import (
    create_access_token,
    decode_access_token_with_reason,
    get_password_hash,
    validate_password,
    verify_password,
)
from app.closures.routes import router as closures_router
from app.dashboard.routes import router as dashboard_router
from app.db.session import (
    AuthSessionLocal,
    SessionLocal,
    database_ready,
    get_engine_error,
    validate_database_configuration,
)
from app.deliveries.routes import router as deliveries_router
from app.history.monthly_history import router as monthly_history_router
from app.eligibility.engine import get_system_settings
from app.pdf import generate_report_pdf
from app.models import (
    AuditLog,
    Child,
    ConsentTerm,
    ChildSex,
    DeliveryEvent,
    Dependent,
    Equipment,
    EquipmentCondition,
    EquipmentStatus,
    EquipmentType,
    Family,
    FamilyBenefitStatus,
    FamilyWorker,
    FoodBasket,
    FoodBasketStatus,
    Loan,
    LoanStatus,
    PasswordResetToken,
    DocumentStatus,
    Referral,
    ReferralStatus,
    ReferralTarget,
    SpiritualDecision,
    StreetTime,
    Role,
    StreetPerson,
    StreetService,
    SystemSettings,
    User,
    VisitExecution,
    VisitExecutionResult,
    VisitRequest,
    VisitRequestStatus,
    VulnerabilityLevel,
)
from app.reports.routes import router as reports_router
from app.security.rate_limit import enforce_login_rate_limit, ensure_login_not_locked, register_login_attempt
from app.services.audit import log_action
from app.services.viacep_client import (
    ViaCEPError,
    ViaCEPInvalidCEPError,
    ViaCEPNotFoundError,
    ViaCEPUnavailableError,
    fetch_address_by_cep,
    normalize_cep,
)

setup_logging()
logger = logging.getLogger("app.audit")


def _bootstrap_auth_defaults() -> None:
    with AuthSessionLocal() as db:
        existing_roles = {role.name: role for role in db.execute(select(Role)).scalars().all()}
        for role_name, definition in ROLE_DEFINITIONS.items():
            permissions = ",".join(sorted(definition["permissions"]))
            role = existing_roles.get(role_name)
            if role:
                role.description = definition["description"]
                role.permissions = permissions
            else:
                db.add(
                    Role(
                        name=role_name,
                        description=definition["description"],
                        permissions=permissions,
                    )
                )
        for role in existing_roles.values():
            if role.name not in ROLE_DEFINITIONS:
                db.delete(role)
        db.commit()
        admin_user = db.execute(select(User).limit(1)).scalar_one_or_none()
        if not admin_user:
            admin_role = db.execute(select(Role).where(Role.name == "Admin")).scalar_one()
            new_admin = User(
                name=settings.default_admin_name,
                email=settings.default_admin_email,
                hashed_password=get_password_hash(settings.default_admin_password),
                roles=[admin_role],
            )
            db.add(new_admin)
            db.commit()




def _bootstrap_consent_term() -> None:
    with SessionLocal() as db:
        active = db.execute(select(ConsentTerm).where(ConsentTerm.active.is_(True))).scalar_one_or_none()
        if active:
            return
        db.add(
            ConsentTerm(
                version="v1",
                content=(
                    "Autorizo o tratamento dos dados pessoais informados para execução "
                    "dos serviços socioassistenciais da Ação Social."
                ),
                active=True,
            )
        )
        db.commit()


def _active_consent_term(db) -> ConsentTerm | None:
    return db.execute(select(ConsentTerm).where(ConsentTerm.active.is_(True))).scalar_one_or_none()


def _require_consent(consent_accepted: bool, active_term: ConsentTerm | None) -> None:
    if not active_term:
        raise ValueError("Não existe termo de consentimento ativo configurado.")
    if not consent_accepted:
        raise ValueError("É obrigatório aceitar o termo de consentimento LGPD.")


def _mask_cpf(value: str | None) -> str:
    digits = _normalize_cpf(value or "")
    if len(digits) != 11:
        return value or ""
    return f"***.***.***-{digits[-2:]}"

def _validate_runtime_settings() -> bool:
    app_env = settings.app_env.lower()
    is_valid = True

    if app_env == "production" and not settings.secret_key.strip():
        logger.error("Config inválida: SECRET_KEY precisa estar definido em produção.")
        is_valid = False

    db_valid, db_error = validate_database_configuration(app_env=app_env)
    if not db_valid:
        logger.error("Config inválida: %s", db_error)
        is_valid = False

    return is_valid


@asynccontextmanager
async def lifespan(_: FastAPI):
    runtime_valid = _validate_runtime_settings()
    db_config_valid, db_config_error = validate_database_configuration(settings.app_env)
    app.state.runtime_config_valid = runtime_valid
    app.state.db_config_valid = db_config_valid
    app.state.db_config_error = db_config_error

    if db_config_valid and database_ready():
        try:
            _bootstrap_auth_defaults()
            _bootstrap_consent_term()
            logger.info("Bootstrap inicial concluído.")
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao executar bootstrap inicial do banco.")
    else:
        logger.error(
            "Banco indisponível durante startup.",
            extra={"error": str(get_engine_error())},
        )

    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(deliveries_router)
app.include_router(closures_router)
app.include_router(monthly_history_router)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:  # noqa: BLE001
    logger.exception("Falha ao montar diretório estático; seguindo sem /static.")

templates = Jinja2Templates(directory="templates")


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception(
        "Erro de banco de dados durante request.",
        extra={"path": request.url.path},
    )
    return Response(
        content="Banco de dados indisponível.",
        status_code=503,
        media_type="text/plain",
    )


VULNERABILITY_OPTIONS = [level.value for level in VulnerabilityLevel]
CHILD_SEX_OPTIONS = [sex.value for sex in ChildSex]
EQUIPMENT_STATUS_OPTIONS = [status.value for status in EquipmentStatus]
EQUIPMENT_TYPE_OPTIONS = [item.value for item in EquipmentType]
EQUIPMENT_CONDITION_OPTIONS = [item.value for item in EquipmentCondition]
FOOD_BASKET_STATUS_OPTIONS = [status.value for status in FoodBasketStatus]
FAMILY_BENEFIT_STATUS_OPTIONS = [item.value for item in FamilyBenefitStatus]
REFERRAL_STATUS_OPTIONS = [status.value for status in ReferralStatus]
REFERRAL_TARGET_OPTIONS = [item.value for item in ReferralTarget]
DOCUMENT_STATUS_OPTIONS = [item.value for item in DocumentStatus]
STREET_TIME_OPTIONS = [item.value for item in StreetTime]
SPIRITUAL_DECISION_OPTIONS = [item.value for item in SpiritualDecision]
VISIT_REQUEST_STATUS_OPTIONS = [status.value for status in VisitRequestStatus]
VISIT_EXECUTION_RESULT_OPTIONS = [status.value for status in VisitExecutionResult]
DEFAULT_STREET_SERVICE_TYPES = [
    "Banho",
    "Roupa",
    "Alimentação",
    "Corte de cabelo",
    "Encaminhamento social",
]
VULNERABILITY_ALERT_LEVELS = {VulnerabilityLevel.HIGH, VulnerabilityLevel.EXTREME}


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
        "can_view_audit": has_permissions(current_user, {"manage_users"}),
        "can_manage_config": has_permissions(current_user, {"manage_users"}),
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


def _normalize_cpf(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _validate_cpf(value: str) -> str:
    cpf = _normalize_cpf(value)
    if len(cpf) != 11:
        raise ValueError("CPF deve ter 11 dígitos.")
    if cpf == cpf[0] * 11:
        raise ValueError("CPF inválido.")
    total = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit = (total * 10) % 11
    digit = 0 if digit == 10 else digit
    if digit != int(cpf[9]):
        raise ValueError("CPF inválido.")
    total = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit = (total * 10) % 11
    digit = 0 if digit == 10 else digit
    if digit != int(cpf[10]):
        raise ValueError("CPF inválido.")
    return cpf


def _cpf_conflict(
    db, cpf: str, family_id: int | None = None, dependent_id: int | None = None
) -> str | None:
    family_stmt = select(Family).where(Family.responsible_cpf == cpf)
    family = db.execute(family_stmt).scalar_one_or_none()
    if family and family.id != family_id:
        return "CPF já cadastrado para um responsável familiar."
    dependent_stmt = select(Dependent).where(Dependent.cpf == cpf)
    dependent = db.execute(dependent_stmt).scalar_one_or_none()
    if dependent and dependent.id != dependent_id:
        return "CPF já cadastrado para um dependente."
    return None


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Data inválida.") from exc


def _parse_child_sex(value: str) -> ChildSex:
    try:
        return ChildSex(value)
    except ValueError as exc:
        raise ValueError("Selecione um sexo válido (M/F/O/NI).") from exc


def _calculate_age(birth_date: date) -> int:
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def _child_form_context(
    request: Request, child: Child | None, families: list[Family], error: str | None
) -> dict[str, object]:
    context = _template_context(request)
    context.update(
        {
            "child": child,
            "families": families,
            "child_sex_options": CHILD_SEX_OPTIONS,
            "error": error,
        }
    )
    return context


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value.replace(",", "."))
    except ValueError as exc:
        raise ValueError("Valor numérico inválido.") from exc


def _normalize_optional_cep(value: str | None) -> str | None:
    clean = (value or "").strip()
    if not clean:
        return None
    return normalize_cep(clean)


def _validate_state(value: str | None) -> str | None:
    clean = (value or "").strip().upper()
    if not clean:
        return None
    if len(clean) != 2 or not clean.isalpha():
        raise ValueError("UF deve ter 2 letras.")
    return clean


def normalize_neighborhood(value: str | None) -> str:
    return (value or "").strip().upper()


def _validate_neighborhood(value: str | None) -> str:
    clean = normalize_neighborhood(value)
    if not clean:
        raise ValueError("Bairro é obrigatório.")
    return clean


def _require_value(value: str, field_label: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_label} é obrigatório.")
    return value.strip()


def _normalize_email(value: str) -> str:
    email = (value or "").strip().lower()
    if not email:
        raise ValueError("E-mail é obrigatório.")
    return email


def _parse_vulnerability(value: str) -> VulnerabilityLevel:
    try:
        return VulnerabilityLevel(value)
    except ValueError as exc:
        raise ValueError("Selecione um nível de vulnerabilidade válido.") from exc


def _token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _password_reset_message() -> str:
    return "Se existir uma conta para este e-mail, enviaremos um link de redefinição."




def _recalculate_family_income(family: Family) -> None:
    workers_income = sum(item.monthly_income or 0 for item in family.workers)
    dependents_income = sum(item.income or 0 for item in family.dependents)
    family.total_income = round(workers_income + dependents_income, 2)
    family.workers_count = len(family.workers)

def _street_form_context(
    request: Request,
    person: StreetPerson | None,
    error: str | None,
    active_consent_term: ConsentTerm | None = None,
) -> dict[str, object]:
    context = _template_context(request)
    context.update({"person": person, "error": error, "active_consent_term": active_consent_term, "document_status_options": DOCUMENT_STATUS_OPTIONS, "street_time_options": STREET_TIME_OPTIONS, "spiritual_decision_options": SPIRITUAL_DECISION_OPTIONS})
    return context


def _validate_street_cpf(db, value: str, person_id: int | None = None) -> str:
    cpf = _validate_cpf(value)
    stmt = select(StreetPerson).where(StreetPerson.cpf == cpf)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing and existing.id != person_id:
        raise ValueError("CPF já cadastrado para outra pessoa em situação de rua.")
    return cpf


def _parse_reference_month_year(month_year: str) -> tuple[int, int]:
    clean = (month_year or "").strip()
    if not clean:
        raise ValueError("Mês/ano é obrigatório.")
    try:
        month_value, year_value = clean.split("/")
        month = int(month_value)
        year = int(year_value)
    except ValueError as exc:
        raise ValueError("Use o formato MM/AAAA para mês/ano.") from exc
    if month < 1 or month > 12:
        raise ValueError("Mês inválido.")
    if year < 2000 or year > 2100:
        raise ValueError("Ano inválido.")
    return month, year


def _build_basket_alerts(db, family: Family, months_without_basket: int = 3) -> list[str]:
    alerts: list[str] = []
    latest = db.execute(
        select(FoodBasket)
        .where(FoodBasket.family_id == family.id, FoodBasket.status == FoodBasketStatus.DELIVERED)
        .order_by(FoodBasket.reference_year.desc(), FoodBasket.reference_month.desc())
        .limit(1)
    ).scalar_one_or_none()
    if latest:
        months_since = (date.today().year - latest.reference_year) * 12 + (
            date.today().month - latest.reference_month
        )
        if months_since >= months_without_basket:
            alerts.append(f"Família sem cesta há {months_since} meses.")
    if family.vulnerability in VULNERABILITY_ALERT_LEVELS:
        if not latest:
            alerts.append("Vulnerabilidade alta sem atendimento recente de cestas.")
        else:
            months_since = (date.today().year - latest.reference_year) * 12 + (
                date.today().month - latest.reference_month
            )
            if months_since >= 2:
                alerts.append("Vulnerabilidade alta sem atendimento recente de cestas.")
    return alerts


def _build_visit_alerts(family: Family) -> list[str]:
    alerts: list[str] = []
    pending = [item for item in family.visit_requests if item.status == VisitRequestStatus.PENDING]
    overdue = [item for item in pending if item.scheduled_date < date.today()]
    if pending:
        alerts.append(f"{len(pending)} visita(s) pendente(s).")
    if overdue:
        alerts.append(f"{len(overdue)} visita(s) em atraso.")
    return alerts


def _family_form_context(
    request: Request,
    family: Family | None,
    error: str | None,
    active_consent_term: ConsentTerm | None = None,
) -> dict[str, object]:
    context = _template_context(request)
    context.update(
        {
            "family": family,
            "error": error,
            "vulnerability_options": VULNERABILITY_OPTIONS,
            "active_consent_term": active_consent_term,
            "family_benefit_status_options": FAMILY_BENEFIT_STATUS_OPTIONS,
        }
    )
    return context


def _equipment_form_context(
    request: Request,
    equipment: Equipment | None,
    error: str | None,
    is_locked: bool = False,
) -> dict[str, object]:
    context = _template_context(request)
    context.update(
        {
            "equipment": equipment,
            "error": error,
            "equipment_status_options": EQUIPMENT_STATUS_OPTIONS,
            "equipment_type_options": EQUIPMENT_TYPE_OPTIONS,
            "equipment_condition_options": EQUIPMENT_CONDITION_OPTIONS,
            "is_locked": is_locked,
        }
    )
    return context


def _loan_form_context(
    request: Request,
    equipment: Equipment,
    families: list[Family],
    error: str | None,
) -> dict[str, object]:
    context = _template_context(request)
    context.update({"equipment": equipment, "families": families, "error": error})
    return context


def _generate_equipment_code(db) -> str:
    codes = db.execute(select(Equipment.code)).scalars().all()
    max_sequence = 0
    for code in codes:
        match = re.match(r"BEN-(\d+)$", code)
        if match:
            max_sequence = max(max_sequence, int(match.group(1)))
    next_sequence = max_sequence + 1
    existing_codes = set(codes)
    while True:
        candidate = f"BEN-{next_sequence:02d}"
        if candidate not in existing_codes:
            return candidate
        next_sequence += 1


def _ensure_database_runtime_ready(request: Request) -> None:
    db_config_valid = getattr(request.app.state, "db_config_valid", True)
    if db_config_valid:
        return

    detail = getattr(
        request.app.state,
        "db_config_error",
        "Banco de dados indisponível por configuração inválida.",
    )
    raise HTTPException(status_code=503, detail=detail)


def get_db(request: Request):
    _ensure_database_runtime_ready(request)
    try:
        db = SessionLocal()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao abrir sessão de banco.")
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.") from exc
    try:
        yield db
    finally:
        db.close()


def get_auth_db(request: Request):
    _ensure_database_runtime_ready(request)
    try:
        db = AuthSessionLocal()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao abrir sessão de autenticação.")
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.") from exc
    try:
        yield db
    finally:
        db.close()


def on_startup() -> None:
    _validate_runtime_settings()
    if not database_ready():
        logger.error(
            "Banco indisponível durante startup.",
            extra={"error": str(get_engine_error())},
        )
        return
    try:
        _bootstrap_auth_defaults()
    except Exception:  # noqa: BLE001
        logger.exception("Falha ao executar bootstrap inicial do banco.")


AUTHENTICATED_SSR_PATH_PREFIXES = (
    "/dashboard",
    "/familias",
    "/equipamentos",
    "/rua",
    "/admin",
    "/relatorios",
    "/busca",
)


def _is_authenticated_ssr_path(path: str) -> bool:
    return any(
        path == prefix or path.startswith(f"{prefix}/")
        for prefix in AUTHENTICATED_SSR_PATH_PREFIXES
    )


def _apply_no_cache_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Vary"] = "Cookie"


def _log_set_cookie(path: str, response: Response) -> None:
    set_cookie_header = response.headers.get("set-cookie", "")
    logger.info(
        "auth_cookie_write",
        extra={
            "path": path,
            "contains_set_cookie": bool(set_cookie_header),
            "cookie_name": AUTH_COOKIE_NAME,
            "contains_auth_cookie": f"{AUTH_COOKIE_NAME}=" in set_cookie_header,
        },
    )


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    request.state.user = None
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    started = perf_counter()

    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    debug_info = debug_auth(request)
    auth_reason = "missing"
    if not token:
        token = request.cookies.get(AUTH_COOKIE_NAME)
    if token:
        payload, decode_reason = decode_access_token_with_reason(token)
        auth_reason = decode_reason
        if payload and payload.get("sub"):
            user_id = int(payload["sub"])
            try:
                with AuthSessionLocal() as db:
                    stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
                    user = db.execute(stmt).scalar_one_or_none()
                    if user and user.is_active:
                        request.state.user = user
                        auth_reason = "ok"
                    else:
                        auth_reason = "user_inactive_or_not_found"
            except Exception:  # noqa: BLE001
                auth_reason = "db_unavailable"
                logger.exception(
                    "Falha ao resolver usuário autenticado por indisponibilidade do banco."
                )
        elif decode_reason == "ok":
            auth_reason = "missing_sub_claim"

    response = await call_next(request)
    duration_ms = round((perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id

    user = getattr(request.state, "user", None)
    logger.info(
        "http_request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else None,
            "user_id": user.id if user else None,
            "app_env": settings.app_env,
            "has_cookie_auth": debug_info["has_cookie"],
            "cookie_name": AUTH_COOKIE_NAME,
            "auth_reason": auth_reason,
        },
    )

    if _is_authenticated_ssr_path(request.url.path):
        _apply_no_cache_headers(response)

    return response


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("home.html", _template_context(request))


@app.get("/health", response_class=HTMLResponse)
def health(request: Request) -> HTMLResponse:
    context = _template_context(request)
    context.update(
        {
            "runtime_config_valid": getattr(request.app.state, "runtime_config_valid", True),
            "db_config_valid": getattr(request.app.state, "db_config_valid", True),
            "db_config_error": getattr(request.app.state, "db_config_error", None),
        }
    )
    return templates.TemplateResponse("health.html", context)


@app.get("/api/cep/{cep}")
def cep_lookup(cep: str):
    try:
        address = fetch_address_by_cep(cep)
    except ViaCEPInvalidCEPError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_CEP", "message": str(exc)},
        ) from exc
    except ViaCEPNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "CEP_NOT_FOUND", "message": str(exc)},
        ) from exc
    except ViaCEPUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "VIACEP_UNAVAILABLE", "message": str(exc)},
        ) from exc
    except ViaCEPError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "VIACEP_UNAVAILABLE", "message": str(exc)},
        ) from exc
    return {
        "cep": address.cep,
        "street": address.street,
        "neighborhood": address.neighborhood,
        "city": address.city,
        "state": address.state,
        "complement": address.complement,
    }


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request) -> HTMLResponse:
    context = _template_context(request)
    context.update({"error": None})
    return templates.TemplateResponse("login.html", context)


@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db=Depends(get_auth_db),
):
    ip = _client_ip(request)
    try:
        normalized_email = _normalize_email(email)
    except ValueError:
        normalized_email = ""

    enforce_login_rate_limit(
        db,
        ip,
        limit=settings.login_rate_limit_max_requests,
        window_minutes=settings.login_rate_limit_window_minutes,
    )

    stmt = (
        select(User)
        .options(selectinload(User.roles))
        .where(func.lower(User.email) == normalized_email)
    )
    user = db.execute(stmt).scalar_one_or_none()

    ensure_login_not_locked(
        db,
        normalized_email,
        ip,
        user_id=user.id if user else None,
        max_failures=settings.login_lockout_max_failures,
        window_minutes=settings.login_lockout_window_minutes,
    )

    if not user or not verify_password(password, user.hashed_password) or not user.is_active:
        register_login_attempt(
            db,
            identity=normalized_email,
            ip=ip,
            success=False,
            user_id=user.id if user else None,
        )
        context = _template_context(request)
        context.update({"error": "Credenciais inválidas."})
        return templates.TemplateResponse(
            "login.html", context, status_code=status.HTTP_401_UNAUTHORIZED
        )

    register_login_attempt(db, identity=normalized_email, ip=ip, success=True, user_id=user.id)
    access_token = create_access_token({"sub": str(user.id)})
    redirect_url = "/admin/users" if user.has_permissions({"view_users"}) else "/"
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    set_auth_cookie(response, access_token)
    _log_set_cookie("/login", response)
    return response


@app.post("/auth/login")
def login_api(payload: dict = Body(...), db=Depends(get_auth_db)):
    email = str(payload.get("email") or payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Informe usuário/e-mail e senha.")

    normalized_email = _normalize_email(email)
    stmt = (
        select(User)
        .options(selectinload(User.roles))
        .where(func.lower(User.email) == normalized_email)
    )
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuário inativo.")

    access_token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "roles": [role.name for role in user.roles],
        },
    }


@app.get("/password/forgot", response_class=HTMLResponse)
def forgot_password_form(request: Request) -> HTMLResponse:
    context = _template_context(request)
    context.update({"error": None, "info": None})
    return templates.TemplateResponse("auth_forgot_password.html", context)


@app.post("/password/forgot", response_class=HTMLResponse)
def forgot_password_submit(
    request: Request,
    email: str = Form(...),
    db=Depends(get_auth_db),
) -> HTMLResponse:
    context = _template_context(request)
    message = _password_reset_message()
    normalized_email = (email or "").strip().lower()
    if normalized_email:
        user = db.execute(select(User).where(func.lower(User.email) == normalized_email)).scalar_one_or_none()
        if user and user.is_active:
            raw_token = secrets.token_urlsafe(48)
            now = datetime.utcnow()
            db.add(
                PasswordResetToken(
                    user_id=user.id,
                    token_hash=_token_hash(raw_token),
                    created_at=now,
                    expires_at=now + timedelta(minutes=settings.password_reset_token_ttl_minutes),
                    request_ip=_client_ip(request),
                    user_agent=(request.headers.get("user-agent") or "")[:255] or None,
                )
            )
            db.commit()
            if settings.app_env.lower() != "production":
                context["dev_reset_link"] = f"/password/reset?token={raw_token}"
    context["info"] = message
    context["error"] = None
    return templates.TemplateResponse("auth_forgot_password.html", context)


@app.get("/password/reset", response_class=HTMLResponse)
def reset_password_form(request: Request, token: str = "", db=Depends(get_auth_db)) -> HTMLResponse:
    token_hash = _token_hash(token) if token else ""
    now = datetime.utcnow()
    token_row = db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at >= now,
        )
    ).scalar_one_or_none()
    if not token_row:
        context = _template_context(request)
        context.update({"error": "Token inválido ou expirado.", "token": "", "show_form": False})
        return templates.TemplateResponse("auth_reset_password.html", context, status_code=400)

    context = _template_context(request)
    context.update({"error": None, "token": token, "show_form": True})
    return templates.TemplateResponse("auth_reset_password.html", context)


@app.post("/password/reset", response_class=HTMLResponse)
def reset_password_submit(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    db=Depends(get_auth_db),
):
    token_hash = _token_hash(token)
    now = datetime.utcnow()
    token_row = db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at >= now,
        )
    ).scalar_one_or_none()
    if not token_row:
        context = _template_context(request)
        context.update({"error": "Token inválido ou expirado.", "token": "", "show_form": False})
        return templates.TemplateResponse("auth_reset_password.html", context, status_code=400)

    user = db.get(User, token_row.user_id)
    errors = validate_password(password)
    if not user or errors:
        context = _template_context(request)
        context.update({"error": " ".join(errors) if errors else "Token inválido ou expirado.", "token": token, "show_form": True})
        return templates.TemplateResponse("auth_reset_password.html", context, status_code=400)

    user.hashed_password = get_password_hash(password)
    token_row.used_at = now
    db.commit()
    context = _template_context(request)
    context.update({"error": None, "token": "", "show_form": False, "success": "Senha redefinida com sucesso. Faça login."})
    return templates.TemplateResponse("auth_reset_password.html", context)


@app.get("/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    clear_auth_cookie(response)
    _log_set_cookie("/logout", response)
    return response


@app.get("/admin/users", response_class=HTMLResponse)
def list_users(
    request: Request,
    db=Depends(get_auth_db),
    current_user: User = Depends(require_permissions("view_users")),
) -> HTMLResponse:
    stmt = (
        select(User)
        .options(selectinload(User.roles))
        .where(User.is_active.in_([True, False]))
        .order_by(User.name)
    )
    users = db.execute(stmt).scalars().all()
    context = _template_context(request)
    context.update({"users": users, "current_user": current_user})
    return templates.TemplateResponse("admin_users.html", context)


@app.get("/admin/usuarios")
def admin_users_alias() -> RedirectResponse:
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/admin/users/new", response_class=HTMLResponse)
def new_user_form(
    request: Request,
    db=Depends(get_auth_db),
    current_user: User = Depends(require_permissions("manage_users")),
) -> HTMLResponse:
    roles = db.execute(select(Role).order_by(Role.name)).scalars().all()
    context = _template_context(request)
    context.update({"roles": roles, "user": None, "error": None})
    return templates.TemplateResponse("admin_user_form.html", context)


@app.post("/admin/users/new")
def create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role_ids: list[int] = Form(default=[]),
    is_active: bool = Form(default=False),
    db=Depends(get_auth_db),
    current_user: User = Depends(require_permissions("manage_users")),
):
    context = _template_context(request)
    normalized_email = _normalize_email(email)
    existing_user = db.execute(
        select(User).where(func.lower(User.email) == normalized_email)
    ).scalar_one_or_none()
    if existing_user:
        context.update({"roles": db.execute(select(Role).order_by(Role.name)).scalars().all()})
        context.update({"user": None, "error": "E-mail já cadastrado."})
        return templates.TemplateResponse("admin_user_form.html", context, status_code=400)
    password_errors = validate_password(password)
    if password_errors:
        context.update({"roles": db.execute(select(Role).order_by(Role.name)).scalars().all()})
        context.update({"user": None, "error": " ".join(password_errors)})
        return templates.TemplateResponse("admin_user_form.html", context, status_code=400)
    roles = db.execute(select(Role).where(Role.id.in_(role_ids))).scalars().all()
    user = User(
        name=name,
        email=normalized_email,
        hashed_password=get_password_hash(password),
        is_active=is_active,
        roles=roles,
    )
    db.add(user)
    db.commit()
    response = RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)
    _log_set_cookie("/admin/users/new", response)
    return response


@app.get("/admin/users/{user_id}/edit", response_class=HTMLResponse)
def edit_user_form(
    request: Request,
    user_id: int,
    db=Depends(get_auth_db),
    current_user: User = Depends(require_permissions("manage_users")),
) -> HTMLResponse:
    user = db.get(User, user_id)
    if not user:
        return RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)
    roles = db.execute(select(Role).order_by(Role.name)).scalars().all()
    context = _template_context(request)
    context.update({"roles": roles, "user": user, "error": None})
    return templates.TemplateResponse("admin_user_form.html", context)


@app.post("/admin/users/{user_id}/edit")
def update_user(
    request: Request,
    user_id: int,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(default=""),
    role_ids: list[int] = Form(default=[]),
    is_active: bool = Form(default=False),
    db=Depends(get_auth_db),
    current_user: User = Depends(require_permissions("manage_users")),
):
    user = db.get(User, user_id)
    if not user:
        return RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)
    normalized_email = _normalize_email(email)
    if user.email != normalized_email:
        existing_user = db.execute(
            select(User).where(func.lower(User.email) == normalized_email)
        ).scalar_one_or_none()
        if existing_user:
            roles = db.execute(select(Role).order_by(Role.name)).scalars().all()
            context = _template_context(request)
            context.update({"roles": roles, "user": user, "error": "E-mail já cadastrado."})
            return templates.TemplateResponse("admin_user_form.html", context, status_code=400)
    if password:
        password_errors = validate_password(password)
        if password_errors:
            roles = db.execute(select(Role).order_by(Role.name)).scalars().all()
            context = _template_context(request)
            context.update({"roles": roles, "user": user, "error": " ".join(password_errors)})
            return templates.TemplateResponse("admin_user_form.html", context, status_code=400)
    user.name = name
    user.email = normalized_email
    user.is_active = is_active
    if password:
        user.hashed_password = get_password_hash(password)
    user.roles = db.execute(select(Role).where(Role.id.in_(role_ids))).scalars().all()
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/admin/config", response_class=HTMLResponse)
def admin_config_form(
    request: Request,
    db=Depends(get_db),
    current_user: User = Depends(require_roles("Admin")),
) -> HTMLResponse:
    config = get_system_settings(db)
    updater_name = None
    if config.updated_by_user_id:
        updater = db.execute(select(User).where(User.id == config.updated_by_user_id)).scalar_one_or_none()
        updater_name = updater.name if updater else None
    context = _template_context(request)
    context.update({"config": config, "updater_name": updater_name, "error": None})
    return templates.TemplateResponse("admin_config.html", context)


@app.post("/admin/config")
def admin_config_update(
    request: Request,
    delivery_month_limit: int = Form(...),
    min_months_since_last_delivery: int = Form(...),
    min_vulnerability_level: int = Form(...),
    require_documentation_complete: bool = Form(default=False),
    db=Depends(get_db),
    current_user: User = Depends(require_roles("Admin")),
) -> Response:
    errors: list[str] = []
    if delivery_month_limit < 0:
        errors.append("Limite de entregas por mês deve ser >= 0.")
    if min_months_since_last_delivery < 0 or min_months_since_last_delivery > 24:
        errors.append("Meses mínimos sem entrega deve estar entre 0 e 24.")
    if min_vulnerability_level < 0 or min_vulnerability_level > 4:
        errors.append("Vulnerabilidade mínima deve estar entre 0 e 4.")

    config = get_system_settings(db)
    if errors:
        context = _template_context(request)
        updater_name = None
        if config.updated_by_user_id:
            updater = db.execute(select(User).where(User.id == config.updated_by_user_id)).scalar_one_or_none()
            updater_name = updater.name if updater else None
        config.delivery_month_limit = delivery_month_limit
        config.min_months_since_last_delivery = min_months_since_last_delivery
        config.min_vulnerability_level = min_vulnerability_level
        config.require_documentation_complete = require_documentation_complete
        context.update({"config": config, "updater_name": updater_name, "error": " ".join(errors)})
        return templates.TemplateResponse("admin_config.html", context, status_code=400)

    config.delivery_month_limit = delivery_month_limit
    config.min_months_since_last_delivery = min_months_since_last_delivery
    config.min_vulnerability_level = min_vulnerability_level
    config.require_documentation_complete = require_documentation_complete
    config.updated_by_user_id = current_user.id
    config.updated_at = datetime.utcnow()
    db.add(config)
    db.commit()

    return RedirectResponse(url="/admin/config", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/admin/consentimento", response_class=HTMLResponse)
def admin_consent_terms(
    request: Request,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_users")),
) -> HTMLResponse:
    terms = db.execute(select(ConsentTerm).order_by(ConsentTerm.created_at.desc())).scalars().all()
    context = _template_context(request)
    context.update({"terms": terms, "current_user": current_user, "error": None})
    return templates.TemplateResponse("admin_consentimento.html", context)


@app.post("/admin/consentimento")
def create_consent_term(
    request: Request,
    version: str = Form(...),
    content: str = Form(...),
    active: bool = Form(default=False),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_users")),
) -> Response:
    parsed_version = (version or "").strip()
    parsed_content = (content or "").strip()
    if not parsed_version or not parsed_content:
        context = _template_context(request)
        terms = db.execute(select(ConsentTerm).order_by(ConsentTerm.created_at.desc())).scalars().all()
        context.update({"terms": terms, "current_user": current_user, "error": "Versão e conteúdo são obrigatórios."})
        return templates.TemplateResponse("admin_consentimento.html", context, status_code=400)
    exists = db.execute(select(ConsentTerm).where(ConsentTerm.version == parsed_version)).scalar_one_or_none()
    if exists:
        context = _template_context(request)
        terms = db.execute(select(ConsentTerm).order_by(ConsentTerm.created_at.desc())).scalars().all()
        context.update({"terms": terms, "current_user": current_user, "error": "Versão já cadastrada."})
        return templates.TemplateResponse("admin_consentimento.html", context, status_code=400)

    if active:
        for term in db.execute(select(ConsentTerm).where(ConsentTerm.active.is_(True))).scalars().all():
            term.active = False

    term = ConsentTerm(version=parsed_version, content=parsed_content, active=active)
    db.add(term)
    db.commit()
    return RedirectResponse(url="/admin/consentimento", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/admin/audit", response_class=HTMLResponse)
def admin_audit_logs(
    request: Request,
    entity: str = "",
    entity_id: str = "",
    user_id: str = "",
    start_date: str = "",
    end_date: str = "",
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_users")),
) -> HTMLResponse:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    if entity.strip():
        stmt = stmt.where(AuditLog.entity == entity.strip())
    if entity_id.strip().isdigit():
        stmt = stmt.where(AuditLog.entity_id == int(entity_id.strip()))
    if user_id.strip().isdigit():
        stmt = stmt.where(AuditLog.user_id == int(user_id.strip()))
    if start_date.strip():
        stmt = stmt.where(AuditLog.created_at >= datetime.fromisoformat(start_date.strip()))
    if end_date.strip():
        stmt = stmt.where(AuditLog.created_at <= datetime.fromisoformat(f"{end_date.strip()}T23:59:59"))

    logs = db.execute(stmt.limit(500)).scalars().all()
    context = _template_context(request)
    context.update(
        {
            "logs": logs,
            "filters": {
                "entity": entity,
                "entity_id": entity_id,
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
            },
            "current_user": current_user,
        }
    )
    return templates.TemplateResponse("admin_audit.html", context)


@app.get("/busca", response_class=HTMLResponse)
def global_search(
    request: Request,
    q: str = "",
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("view_families")),
) -> HTMLResponse:
    term = (q or "").strip()
    families = []
    children = []
    equipment_items = []
    events = []
    if term:
        families = db.execute(
            select(Family)
            .where(
                Family.responsible_name.ilike(f"%{term}%")
                | Family.responsible_cpf.ilike(f"%{term}%")
                | Family.neighborhood.ilike(f"%{term}%")
            )
            .order_by(Family.responsible_name.asc())
            .limit(20)
        ).scalars().all()
        children = db.execute(
            select(Child).options(selectinload(Child.family)).where(Child.name.ilike(f"%{term}%")).order_by(Child.name.asc()).limit(20)
        ).scalars().all()
        equipment_items = db.execute(
            select(Equipment)
            .where(Equipment.code.ilike(f"%{term}%") | Equipment.description.ilike(f"%{term}%"))
            .order_by(Equipment.code.asc())
            .limit(20)
        ).scalars().all()
        events = db.execute(
            select(DeliveryEvent).where(DeliveryEvent.title.ilike(f"%{term}%")).order_by(DeliveryEvent.event_date.desc()).limit(20)
        ).scalars().all()

    context = _template_context(request)
    context.update({
        "query": term,
        "families": families,
        "children": children,
        "equipment_items": equipment_items,
        "events": events,
        "current_user": current_user,
    })
    return templates.TemplateResponse("search_results.html", context)


@app.get("/timeline")
def timeline(
    family_id: int | None = None,
    person_id: int | None = None,
    db=Depends(get_db),
    _current_user: User = Depends(require_permissions("view_families")),
):
    if not family_id and not person_id:
        raise HTTPException(status_code=400, detail="Informe family_id ou person_id.")

    events: list[dict[str, object]] = []
    if family_id:
        baskets = db.execute(select(FoodBasket).where(FoodBasket.family_id == family_id)).scalars().all()
        visits = db.execute(select(VisitRequest).where(VisitRequest.family_id == family_id)).scalars().all()
        loans = db.execute(select(Loan).where(Loan.family_id == family_id)).scalars().all()
        events.extend(
            {
                "type": "food_basket",
                "date": basket.created_at,
                "status": basket.status.value,
                "reference": f"{basket.reference_month:02d}/{basket.reference_year}",
            }
            for basket in baskets
        )
        events.extend(
            {
                "type": "visit",
                "date": visit.created_at,
                "status": visit.status.value,
                "notes": visit.request_notes,
            }
            for visit in visits
        )
        events.extend(
            {
                "type": "equipment_loan",
                "date": loan.loan_date,
                "status": loan.status.value,
                "notes": loan.notes,
            }
            for loan in loans
        )

    if person_id:
        services = db.execute(select(StreetService).where(StreetService.person_id == person_id)).scalars().all()
        referrals = db.execute(select(Referral).where(Referral.person_id == person_id)).scalars().all()
        events.extend(
            {
                "type": "street_service",
                "date": service.service_date,
                "status": "DONE",
                "notes": service.notes,
            }
            for service in services
        )
        events.extend(
            {
                "type": "referral",
                "date": referral.created_at,
                "status": referral.status.value,
                "notes": referral.notes,
            }
            for referral in referrals
        )

    events.sort(key=lambda item: item.get("date") or datetime.min, reverse=True)
    return {
        "family_id": family_id,
        "person_id": person_id,
        "total": len(events),
        "items": [
            {
                **item,
                "date": item["date"].isoformat() if item.get("date") else None,
            }
            for item in events
        ],
    }


@app.get("/familias", response_class=HTMLResponse)
def list_families(
    request: Request,
    name: str | None = None,
    cpf: str | None = None,
    neighborhood: str | None = None,
    vulnerability: str | None = None,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("view_families")),
) -> HTMLResponse:
    stmt = select(Family).order_by(Family.responsible_name)
    if name:
        stmt = stmt.where(Family.responsible_name.ilike(f"%{name}%"))
    if cpf:
        cpf_digits = _normalize_cpf(cpf)
        if cpf_digits:
            stmt = stmt.where(Family.responsible_cpf == cpf_digits)
    if neighborhood:
        stmt = stmt.where(Family.neighborhood.ilike(f"%{neighborhood}%"))
    if vulnerability:
        if vulnerability in VULNERABILITY_OPTIONS:
            stmt = stmt.where(Family.vulnerability == VulnerabilityLevel(vulnerability))
    families = db.execute(stmt).scalars().all()
    family_alerts = {family.id: _build_basket_alerts(db, family) for family in families}
    context = _template_context(request)
    context.update(
        {
            "families": families,
            "filters": {
                "name": name or "",
                "cpf": cpf or "",
                "neighborhood": neighborhood or "",
                "vulnerability": vulnerability or "",
            },
            "vulnerability_options": VULNERABILITY_OPTIONS,
            "current_user": current_user,
            "family_alerts": family_alerts,
        }
    )
    return templates.TemplateResponse("families_list.html", context)


@app.get("/pessoas")
def people_alias() -> RedirectResponse:
    return RedirectResponse(url="/rua", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/entregas", response_class=HTMLResponse)
def deliveries_page(
    request: Request,
    db=Depends(get_db),
    _current_user: User = Depends(require_permissions("view_families")),
) -> HTMLResponse:
    events = db.execute(select(DeliveryEvent).order_by(DeliveryEvent.event_date.desc())).scalars().all()
    context = _template_context(request)
    context.update({"events": events})
    return templates.TemplateResponse("deliveries_list.html", context)


@app.get("/criancas", response_class=HTMLResponse)
def list_children(
    request: Request,
    family_id: int | None = None,
    idade_min: int | None = None,
    idade_max: int | None = None,
    sexo: str | None = None,
    nome: str | None = None,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("view_families")),
) -> HTMLResponse:
    stmt = select(Child).options(selectinload(Child.family)).join(Family).order_by(Child.name.asc())
    if family_id is not None:
        stmt = stmt.where(Child.family_id == family_id)
    if sexo and sexo in CHILD_SEX_OPTIONS:
        stmt = stmt.where(Child.sex == ChildSex(sexo))
    if nome:
        stmt = stmt.where(Child.name.ilike(f"%{nome.strip()}%"))

    children = db.execute(stmt).scalars().all()
    filtered_children: list[dict[str, object]] = []
    for child in children:
        age = _calculate_age(child.birth_date)
        if idade_min is not None and age < idade_min:
            continue
        if idade_max is not None and age > idade_max:
            continue
        filtered_children.append({"child": child, "age": age})

    families = (
        db.execute(
            select(Family).where(Family.is_active.is_(True)).order_by(Family.responsible_name.asc())
        )
        .scalars()
        .all()
    )

    context = _template_context(request)
    context.update(
        {
            "children": filtered_children,
            "families": families,
            "filters": {
                "family_id": family_id,
                "idade_min": idade_min,
                "idade_max": idade_max,
                "sexo": sexo or "",
                "nome": nome or "",
            },
            "child_sex_options": CHILD_SEX_OPTIONS,
            "current_user": current_user,
        }
    )
    return templates.TemplateResponse("children_list.html", context)


@app.get("/criancas/nova", response_class=HTMLResponse)
def new_child_form(
    request: Request,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
) -> HTMLResponse:
    families = (
        db.execute(
            select(Family).where(Family.is_active.is_(True)).order_by(Family.responsible_name.asc())
        )
        .scalars()
        .all()
    )
    context = _child_form_context(request, None, families, None)
    return templates.TemplateResponse("children_form.html", context)


@app.post("/criancas")
def create_child(
    request: Request,
    family_id: int = Form(...),
    name: str = Form(...),
    birth_date: str = Form(...),
    sex: str = Form(default=ChildSex.NI.value),
    notes: str = Form(default=""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
):
    families = (
        db.execute(
            select(Family).where(Family.is_active.is_(True)).order_by(Family.responsible_name.asc())
        )
        .scalars()
        .all()
    )
    try:
        parsed_name = _require_value(name, "Nome")
        parsed_birth_date = _parse_date(birth_date)
        parsed_sex = _parse_child_sex(sex)
        family = db.get(Family, family_id)
        if not family:
            raise ValueError("Família não encontrada.")
        if not family.is_active:
            raise ValueError("Família inativa: cadastro de criança não permitido.")
    except ValueError as exc:
        context = _child_form_context(request, None, families, str(exc))
        return templates.TemplateResponse("children_form.html", context, status_code=400)

    child = Child(
        family_id=family_id,
        name=parsed_name,
        birth_date=parsed_birth_date,
        sex=parsed_sex,
        notes=(notes or "").strip() or None,
    )
    db.add(child)
    db.commit()
    return RedirectResponse(url=f"/criancas/{child.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/criancas/{child_id}", response_class=HTMLResponse)
def view_child(
    request: Request,
    child_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("view_families")),
) -> HTMLResponse:
    child = db.execute(
        select(Child).options(selectinload(Child.family)).where(Child.id == child_id)
    ).scalar_one_or_none()
    if not child:
        return RedirectResponse(url="/criancas", status_code=status.HTTP_303_SEE_OTHER)

    context = _template_context(request)
    context.update(
        {"child": child, "age": _calculate_age(child.birth_date), "current_user": current_user}
    )
    return templates.TemplateResponse("children_detail.html", context)


@app.get("/criancas/{child_id}/edit", response_class=HTMLResponse)
def edit_child_form(
    request: Request,
    child_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
) -> HTMLResponse:
    child = db.get(Child, child_id)
    if not child:
        return RedirectResponse(url="/criancas", status_code=status.HTTP_303_SEE_OTHER)
    families = (
        db.execute(
            select(Family).where(Family.is_active.is_(True)).order_by(Family.responsible_name.asc())
        )
        .scalars()
        .all()
    )
    context = _child_form_context(request, child, families, None)
    return templates.TemplateResponse("children_form.html", context)


@app.post("/criancas/{child_id}")
def update_child(
    request: Request,
    child_id: int,
    family_id: int = Form(...),
    name: str = Form(...),
    birth_date: str = Form(...),
    sex: str = Form(default=ChildSex.NI.value),
    notes: str = Form(default=""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
):
    child = db.get(Child, child_id)
    if not child:
        return RedirectResponse(url="/criancas", status_code=status.HTTP_303_SEE_OTHER)

    families = (
        db.execute(
            select(Family).where(Family.is_active.is_(True)).order_by(Family.responsible_name.asc())
        )
        .scalars()
        .all()
    )
    try:
        parsed_name = _require_value(name, "Nome")
        parsed_birth_date = _parse_date(birth_date)
        parsed_sex = _parse_child_sex(sex)
        family = db.get(Family, family_id)
        if not family:
            raise ValueError("Família não encontrada.")
        if not family.is_active:
            raise ValueError("Família inativa: cadastro de criança não permitido.")
    except ValueError as exc:
        context = _child_form_context(request, child, families, str(exc))
        return templates.TemplateResponse("children_form.html", context, status_code=400)

    child.family_id = family_id
    child.name = parsed_name
    child.birth_date = parsed_birth_date
    child.sex = parsed_sex
    child.notes = (notes or "").strip() or None
    db.commit()
    return RedirectResponse(url=f"/criancas/{child.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/criancas/{child_id}/delete")
def delete_child(
    child_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
) -> RedirectResponse:
    child = db.get(Child, child_id)
    if child:
        db.delete(child)
        db.commit()
    return RedirectResponse(url="/criancas", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/familias/nova/step/{step}", response_class=HTMLResponse)
def family_wizard_step(
    request: Request,
    step: int,
    current_user: User = Depends(require_permissions("manage_families")),
) -> HTMLResponse:
    if step < 1 or step > 4:
        return RedirectResponse(url="/familias/nova/step/1", status_code=status.HTTP_303_SEE_OTHER)
    context = _template_context(request)
    context.update({"step": step, "form_data": {}, "current_user": current_user, "error": None})
    return templates.TemplateResponse("family_wizard_step.html", context)


@app.post("/familias/nova/step/{step}")
def family_wizard_submit(
    request: Request,
    step: int,
    responsible_name: str = Form(default=""),
    responsible_cpf: str = Form(default=""),
    phone: str = Form(default=""),
    birth_date: str = Form(default=""),
    cep: str = Form(default=""),
    street: str = Form(default=""),
    number: str = Form(default=""),
    neighborhood: str = Form(default=""),
    city: str = Form(default=""),
    state: str = Form(default=""),
    socioeconomic_profile: str = Form(default=""),
    documentation_status: str = Form(default=""),
    vulnerability: str = Form(default=VulnerabilityLevel.MEDIUM.value),
    consent_accepted: bool = Form(default=False),
    consent_signature_name: str = Form(default=""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
):
    form_data = {
        "responsible_name": responsible_name,
        "responsible_cpf": responsible_cpf,
        "phone": phone,
        "birth_date": birth_date,
        "cep": cep,
        "street": street,
        "number": number,
        "neighborhood": neighborhood,
        "city": city,
        "state": state,
        "socioeconomic_profile": socioeconomic_profile,
        "documentation_status": documentation_status,
        "vulnerability": vulnerability,
        "consent_accepted": consent_accepted,
    }
    if step < 4:
        return templates.TemplateResponse("family_wizard_step.html", {**_template_context(request), "step": step + 1, "form_data": form_data, "vulnerability_options": VULNERABILITY_OPTIONS, "current_user": current_user, "error": None})

    active_term = _active_consent_term(db)
    try:
        family = Family(
            responsible_name=_require_value(responsible_name, "Nome completo"),
            responsible_cpf=_validate_cpf(responsible_cpf),
            phone=_require_value(phone, "Telefone"),
            birth_date=_parse_date(birth_date),
            cep=_normalize_optional_cep(cep),
            street=street or None,
            number=number or None,
            neighborhood=_validate_neighborhood(neighborhood),
            city=city or None,
            state=_validate_state(state),
            vulnerability=_parse_vulnerability(vulnerability),
            socioeconomic_profile=socioeconomic_profile or None,
            documentation_status=documentation_status or None,
            consent_accepted=consent_accepted,
            consent_term_version=active_term.version if active_term else None,
            is_active=True,
        )
        _require_consent(consent_accepted, active_term)
        if _cpf_conflict(db, family.responsible_cpf):
            raise ValueError("CPF já cadastrado.")
    except ValueError as exc:
        return templates.TemplateResponse("family_wizard_step.html", {**_template_context(request), "step": 4, "form_data": form_data, "vulnerability_options": VULNERABILITY_OPTIONS, "current_user": current_user, "error": str(exc) }, status_code=400)

    db.add(family)
    _recalculate_family_income(family)
    db.commit()
    return RedirectResponse(url=f"/familias/{family.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/familias/nova", response_class=HTMLResponse)
def new_family_form(
    request: Request,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
) -> HTMLResponse:
    context = _family_form_context(request, None, None, _active_consent_term(db))
    return templates.TemplateResponse("family_form.html", context)


@app.post("/familias/nova")
def create_family(
    request: Request,
    responsible_name: str = Form(...),
    responsible_cpf: str = Form(...),
    responsible_rg: str = Form(default=""),
    phone: str = Form(...),
    birth_date: str = Form(...),
    cep: str = Form(default=""),
    street: str = Form(default=""),
    number: str = Form(default=""),
    complement: str = Form(default=""),
    neighborhood: str = Form(default=""),
    city: str = Form(default=""),
    state: str = Form(default=""),
    latitude: str = Form(default=""),
    longitude: str = Form(default=""),
    socioeconomic_profile: str = Form(default=""),
    documentation_status: str = Form(default=""),
    vulnerability: str = Form(...),
    partner_name: str = Form(default=""),
    partner_cpf: str = Form(default=""),
    marital_status: str = Form(default=""),
    education_level: str = Form(default=""),
    housing_type: str = Form(default=""),
    chronic_diseases: str = Form(default=""),
    social_benefits: str = Form(default=""),
    church_attendance: bool = Form(default=False),
    needs_visit_alert: bool = Form(default=False),
    adults_count: int = Form(default=1),
    birth_certificate_present: bool = Form(default=True),
    birth_certificate_missing_count: int = Form(default=0),
    workers_data: str = Form(default=""),
    is_active: bool = Form(default=False),
    consent_accepted: bool = Form(default=False),
    consent_signature_name: str = Form(default=""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
):
    active_term = _active_consent_term(db)
    try:
        responsible_name = _require_value(responsible_name, "Nome completo")
        phone = _require_value(phone, "Telefone")
        cpf = _validate_cpf(responsible_cpf)
        conflict = _cpf_conflict(db, cpf)
        if conflict:
            raise ValueError(conflict)
        parsed_birth_date = _parse_date(birth_date)
        parsed_cep = _normalize_optional_cep(cep)
        parsed_state = _validate_state(state)
        parsed_neighborhood = _validate_neighborhood(neighborhood)
        parsed_latitude = _parse_float(latitude)
        parsed_longitude = _parse_float(longitude)
        vulnerability_value = _parse_vulnerability(vulnerability)
        partner_cpf_value = _validate_cpf(partner_cpf) if partner_cpf.strip() else None
        if partner_cpf_value and partner_cpf_value == cpf:
            raise ValueError("CPF do parceiro(a) deve ser diferente do responsável.")
        if adults_count < 1 or adults_count > 12:
            raise ValueError("Quantidade de adultos deve estar entre 1 e 12.")
        if birth_certificate_missing_count < 0:
            raise ValueError("Quantidade de certidões faltantes inválida.")
        workers_payload: list[tuple[str, float]] = []
        if workers_data.strip():
            for raw in workers_data.splitlines():
                if not raw.strip():
                    continue
                try:
                    name, income_text = raw.split(";", 1)
                except ValueError as exc:
                    raise ValueError("Use uma linha por trabalhador no formato Nome;Renda.") from exc
                parsed_name = _require_value(name, "Nome do trabalhador")
                parsed_income = _parse_float(income_text)
                if parsed_income is None or parsed_income < 0:
                    raise ValueError("Renda do trabalhador inválida.")
                workers_payload.append((parsed_name, parsed_income))
        if len(workers_payload) > 10:
            raise ValueError("Máximo de 10 trabalhadores por família.")
        _require_consent(consent_accepted, active_term)
    except ValueError as exc:
        context = _family_form_context(request, None, str(exc), active_term)
        return templates.TemplateResponse("family_form.html", context, status_code=400)
    family = Family(
        responsible_name=responsible_name,
        responsible_cpf=cpf,
        responsible_rg=responsible_rg or None,
        partner_name=partner_name.strip() or None,
        partner_cpf=partner_cpf_value,
        phone=phone,
        birth_date=parsed_birth_date,
        cep=parsed_cep,
        street=street or None,
        number=number or None,
        complement=complement or None,
        neighborhood=parsed_neighborhood,
        city=city or None,
        state=parsed_state,
        latitude=parsed_latitude,
        longitude=parsed_longitude,
        socioeconomic_profile=socioeconomic_profile or None,
        documentation_status=documentation_status or None,
        vulnerability=vulnerability_value,
        marital_status=marital_status.strip() or None,
        education_level=education_level.strip() or None,
        housing_type=housing_type.strip() or None,
        chronic_diseases=chronic_diseases.strip() or None,
        social_benefits=social_benefits.strip() or None,
        church_attendance=church_attendance,
        needs_visit_alert=needs_visit_alert,
        adults_count=adults_count,
        birth_certificate_present=birth_certificate_present,
        birth_certificate_missing_count=birth_certificate_missing_count,
        is_active=is_active,
        consent_term_version=active_term.version if active_term else None,
        consent_accepted=consent_accepted,
        consent_accepted_at=datetime.utcnow(),
        consent_accepted_by_user_id=current_user.id,
    )
    db.add(family)
    db.flush()
    for worker_name, worker_income in workers_payload:
        db.add(FamilyWorker(family_id=family.id, name=worker_name, monthly_income=worker_income))
    db.flush()
    _recalculate_family_income(family)
    log_action(
        db,
        current_user.id,
        "CREATE",
        "family",
        family.id,
        after={
            "id": family.id,
            "responsible_name": family.responsible_name,
            "responsible_cpf": family.responsible_cpf,
            "consent_term_version": family.consent_term_version,
        },
    )
    _recalculate_family_income(family)
    db.commit()
    return RedirectResponse(url=f"/familias/{family.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/familias/{family_id}/export.pdf")
def export_family_pdf(
    request: Request,
    family_id: int,
    db=Depends(get_db),
    _current_user: User = Depends(require_permissions("view_families")),
):
    family = db.execute(
        select(Family)
        .options(
            selectinload(Family.dependents),
            selectinload(Family.children),
            selectinload(Family.food_baskets),
            selectinload(Family.loans).selectinload(Loan.equipment),
        )
        .where(Family.id == family_id)
    ).scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="Família não encontrada.")

    current_user = getattr(request.state, "user", None)
    rows: list[list[object]] = [
        ["Responsável", family.responsible_name],
        ["CPF", family.responsible_cpf],
        ["Telefone", family.phone],
        ["Bairro", family.neighborhood or "-"],
        ["Socioeconômico", family.socioeconomic_profile or "-"],
        ["Documentação", family.documentation_status or "-"],
        ["Dependentes", len(family.dependents)],
        ["Crianças", len(family.children)],
        ["Entregas", len(family.food_baskets)],
        ["Empréstimos", len(family.loans)],
    ]
    pdf_content = generate_report_pdf(
        title=f"Ficha Família #{family.id}",
        month=None,
        year=None,
        sections=[
            {"type": "text", "title": "Identificação", "content": family.responsible_name},
            {"type": "table", "title": "Dados da família", "headers": ["Campo", "Valor"], "rows": rows},
            {
                "type": "text",
                "title": "Totalizadores",
                "content": (
                    f"Total de registros: {len(rows)} | Dependentes: {len(family.dependents)} "
                    f"| Crianças: {len(family.children)} | Entregas: {len(family.food_baskets)}"
                ),
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
        headers={"Content-Disposition": f'attachment; filename="familia-{family_id}.pdf"'},
    )


@app.get("/familias/{family_id}", response_class=HTMLResponse)
def view_family(
    request: Request,
    family_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("view_families")),
) -> HTMLResponse:
    stmt = (
        select(Family)
        .options(
            selectinload(Family.dependents),
            selectinload(Family.loans).selectinload(Loan.equipment),
            selectinload(Family.food_baskets),
            selectinload(Family.visit_requests).selectinload(VisitRequest.execution),
        )
        .where(Family.id == family_id)
    )
    family = db.execute(stmt).scalar_one_or_none()
    if not family:
        return RedirectResponse(url="/familias", status_code=status.HTTP_303_SEE_OTHER)
    context = _template_context(request)
    warning = None if family.is_active else "Família inativa: novos atendimentos estão bloqueados."
    basket_alerts = _build_basket_alerts(db, family)
    context.update(
        {
            "family": family,
            "current_user": current_user,
            "family_warning": warning,
            "basket_alerts": basket_alerts,
            "food_basket_status_options": FOOD_BASKET_STATUS_OPTIONS,
            "visit_request_status_options": VISIT_REQUEST_STATUS_OPTIONS,
            "visit_execution_result_options": VISIT_EXECUTION_RESULT_OPTIONS,
            "visit_pending_count": sum(
                1 for item in family.visit_requests if item.status == VisitRequestStatus.PENDING
            ),
            "visit_alerts": _build_visit_alerts(family),
        }
    )
    return templates.TemplateResponse("family_detail.html", context)


@app.get("/familias/{family_id}/editar", response_class=HTMLResponse)
def edit_family_form(
    request: Request,
    family_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
) -> HTMLResponse:
    family = db.get(Family, family_id)
    if not family:
        return RedirectResponse(url="/familias", status_code=status.HTTP_303_SEE_OTHER)
    context = _family_form_context(request, family, None, _active_consent_term(db))
    return templates.TemplateResponse("family_form.html", context)


@app.post("/familias/{family_id}/editar")
def update_family(
    request: Request,
    family_id: int,
    responsible_name: str = Form(...),
    responsible_cpf: str = Form(...),
    responsible_rg: str = Form(default=""),
    phone: str = Form(...),
    birth_date: str = Form(...),
    cep: str = Form(default=""),
    street: str = Form(default=""),
    number: str = Form(default=""),
    complement: str = Form(default=""),
    neighborhood: str = Form(default=""),
    city: str = Form(default=""),
    state: str = Form(default=""),
    latitude: str = Form(default=""),
    longitude: str = Form(default=""),
    socioeconomic_profile: str = Form(default=""),
    documentation_status: str = Form(default=""),
    vulnerability: str = Form(...),
    partner_name: str = Form(default=""),
    partner_cpf: str = Form(default=""),
    marital_status: str = Form(default=""),
    education_level: str = Form(default=""),
    housing_type: str = Form(default=""),
    chronic_diseases: str = Form(default=""),
    social_benefits: str = Form(default=""),
    church_attendance: bool = Form(default=False),
    needs_visit_alert: bool = Form(default=False),
    adults_count: int = Form(default=1),
    birth_certificate_present: bool = Form(default=True),
    birth_certificate_missing_count: int = Form(default=0),
    workers_data: str = Form(default=""),
    is_active: bool = Form(default=False),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
):
    family = db.get(Family, family_id)
    if not family:
        return RedirectResponse(url="/familias", status_code=status.HTTP_303_SEE_OTHER)
    try:
        responsible_name = _require_value(responsible_name, "Nome completo")
        phone = _require_value(phone, "Telefone")
        cpf = _validate_cpf(responsible_cpf)
        conflict = _cpf_conflict(db, cpf, family_id=family_id)
        if conflict:
            raise ValueError(conflict)
        parsed_birth_date = _parse_date(birth_date)
        parsed_cep = _normalize_optional_cep(cep)
        parsed_state = _validate_state(state)
        parsed_neighborhood = _validate_neighborhood(neighborhood)
        parsed_latitude = _parse_float(latitude)
        parsed_longitude = _parse_float(longitude)
        vulnerability_value = _parse_vulnerability(vulnerability)
    except ValueError as exc:
        context = _family_form_context(request, family, str(exc))
        return templates.TemplateResponse("family_form.html", context, status_code=400)
    family.responsible_name = responsible_name
    family.responsible_cpf = cpf
    family.responsible_rg = responsible_rg or None
    family.phone = phone
    family.birth_date = parsed_birth_date
    family.cep = parsed_cep
    family.street = street or None
    family.number = number or None
    family.complement = complement or None
    family.neighborhood = parsed_neighborhood
    family.city = city or None
    family.state = parsed_state
    family.latitude = parsed_latitude
    family.longitude = parsed_longitude
    family.socioeconomic_profile = socioeconomic_profile or None
    before = {
        "responsible_name": family.responsible_name,
        "responsible_cpf": family.responsible_cpf,
        "phone": family.phone,
        "vulnerability": family.vulnerability,
        "is_active": family.is_active,
    }
    family.documentation_status = documentation_status or None
    family.vulnerability = vulnerability_value
    family.is_active = is_active
    log_action(
        db,
        current_user.id,
        "UPDATE",
        "family",
        family.id,
        before=before,
        after={
            "responsible_name": family.responsible_name,
            "responsible_cpf": family.responsible_cpf,
            "phone": family.phone,
            "vulnerability": family.vulnerability,
            "is_active": family.is_active,
        },
    )
    _recalculate_family_income(family)
    db.commit()
    return RedirectResponse(url=f"/familias/{family.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/familias/{family_id}/inativar")
def inactivate_family(
    family_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
) -> RedirectResponse:
    family = db.get(Family, family_id)
    if family:
        before = {"is_active": family.is_active}
        family.is_active = False
        log_action(db, current_user.id, "DELETE", "family", family.id, before=before, after={"is_active": family.is_active})
        db.commit()
    return RedirectResponse(url=f"/familias/{family_id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/familias/{family_id}/dependentes/novo", response_class=HTMLResponse)
def new_dependent_form(
    request: Request,
    family_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
) -> HTMLResponse:
    family = db.get(Family, family_id)
    if not family:
        return RedirectResponse(url="/familias", status_code=status.HTTP_303_SEE_OTHER)
    if not family.is_active:
        stmt = select(Family).options(selectinload(Family.dependents)).where(Family.id == family_id)
        family = db.execute(stmt).scalar_one()
        context = _template_context(request)
        context.update(
            {
                "family": family,
                "current_user": current_user,
                "family_warning": "Família inativa: novos atendimentos estão bloqueados.",
            }
        )
        return templates.TemplateResponse("family_detail.html", context, status_code=403)
    context = _template_context(request)
    context.update({"family": family, "dependent": None, "error": None})
    return templates.TemplateResponse("dependent_form.html", context)


@app.post("/familias/{family_id}/dependentes/novo")
def create_dependent(
    request: Request,
    family_id: int,
    name: str = Form(...),
    cpf: str = Form(default=""),
    relationship: str = Form(...),
    birth_date: str = Form(...),
    income: str = Form(default=""),
    benefits: str = Form(default=""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
):
    family = db.get(Family, family_id)
    if not family:
        return RedirectResponse(url="/familias", status_code=status.HTTP_303_SEE_OTHER)
    if not family.is_active:
        context = _template_context(request)
        context.update(
            {
                "family": family,
                "dependent": None,
                "error": "Família inativa: novos atendimentos estão bloqueados.",
            }
        )
        return templates.TemplateResponse("dependent_form.html", context, status_code=403)
    context = _template_context(request)
    if len(family.dependents) >= 10:
        context.update({"family": family, "dependent": None, "error": "Máximo de 10 dependentes por família."})
        return templates.TemplateResponse("dependent_form.html", context, status_code=400)
    try:
        name = _require_value(name, "Nome completo")
        relationship = _require_value(relationship, "Parentesco")
        cpf_value = _validate_cpf(cpf) if cpf else None
        if cpf_value:
            conflict = _cpf_conflict(db, cpf_value)
            if conflict:
                raise ValueError(conflict)
        parsed_birth_date = _parse_date(birth_date)
        parsed_income = _parse_float(income)
    except ValueError as exc:
        context.update({"family": family, "dependent": None, "error": str(exc)})
        return templates.TemplateResponse("dependent_form.html", context, status_code=400)
    dependent = Dependent(
        family=family,
        name=name,
        cpf=cpf_value,
        relationship_type=relationship,
        birth_date=parsed_birth_date,
        income=parsed_income,
        benefits=benefits or None,
    )
    db.add(dependent)
    _recalculate_family_income(family)
    db.commit()
    return RedirectResponse(url=f"/familias/{family.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/familias/{family_id}/dependentes/{dependent_id}/editar", response_class=HTMLResponse)
def edit_dependent_form(
    request: Request,
    family_id: int,
    dependent_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
) -> HTMLResponse:
    dependent = db.get(Dependent, dependent_id)
    if not dependent or dependent.family_id != family_id:
        return RedirectResponse(url=f"/familias/{family_id}", status_code=status.HTTP_303_SEE_OTHER)
    context = _template_context(request)
    context.update({"family": dependent.family, "dependent": dependent, "error": None})
    return templates.TemplateResponse("dependent_form.html", context)


@app.post("/familias/{family_id}/dependentes/{dependent_id}/editar")
def update_dependent(
    request: Request,
    family_id: int,
    dependent_id: int,
    name: str = Form(...),
    cpf: str = Form(default=""),
    relationship: str = Form(...),
    birth_date: str = Form(...),
    income: str = Form(default=""),
    benefits: str = Form(default=""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
):
    dependent = db.get(Dependent, dependent_id)
    if not dependent or dependent.family_id != family_id:
        return RedirectResponse(url=f"/familias/{family_id}", status_code=status.HTTP_303_SEE_OTHER)
    if not dependent.family.is_active:
        context = _template_context(request)
        context.update(
            {
                "family": dependent.family,
                "dependent": dependent,
                "error": "Família inativa: novos atendimentos estão bloqueados.",
            }
        )
        return templates.TemplateResponse("dependent_form.html", context, status_code=403)
    context = _template_context(request)
    try:
        name = _require_value(name, "Nome completo")
        relationship = _require_value(relationship, "Parentesco")
        cpf_value = _validate_cpf(cpf) if cpf else None
        if cpf_value:
            conflict = _cpf_conflict(db, cpf_value, dependent_id=dependent_id)
            if conflict:
                raise ValueError(conflict)
        parsed_birth_date = _parse_date(birth_date)
        parsed_income = _parse_float(income)
    except ValueError as exc:
        context.update({"family": dependent.family, "dependent": dependent, "error": str(exc)})
        return templates.TemplateResponse("dependent_form.html", context, status_code=400)
    dependent.name = name
    dependent.cpf = cpf_value
    dependent.relationship_type = relationship
    dependent.birth_date = parsed_birth_date
    dependent.income = parsed_income
    dependent.benefits = benefits or None
    db.commit()
    return RedirectResponse(url=f"/familias/{family_id}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/familias/{family_id}/dependentes/{dependent_id}/remover")
def remove_dependent(
    family_id: int,
    dependent_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_families")),
) -> RedirectResponse:
    dependent = db.get(Dependent, dependent_id)
    if dependent and dependent.family_id == family_id:
        family = dependent.family
        db.delete(dependent)
        db.flush()
        _recalculate_family_income(family)
        db.commit()
    return RedirectResponse(url=f"/familias/{family_id}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/familias/{family_id}/cestas")
def create_food_basket(
    request: Request,
    family_id: int,
    month_year: str = Form(...),
    status_value: str = Form(FoodBasketStatus.DELIVERED.value),
    family_status: str = Form(FamilyBenefitStatus.ELIGIBLE.value),
    delivery_date: str = Form(""),
    quantity: int = Form(1),
    frequency_months: int = Form(1),
    last_withdrawal_at: str = Form(""),
    last_withdrawal_responsible: str = Form(""),
    notes: str = Form(default=""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_baskets")),
):
    if settings.feature_event_delivery:
        raise HTTPException(
            status_code=403,
            detail="Registro legado de cestas descontinuado. Use entregas por evento.",
        )
    family = db.get(Family, family_id)
    if not family:
        return RedirectResponse(url="/familias", status_code=status.HTTP_303_SEE_OTHER)
    stmt = (
        select(Family)
        .options(
            selectinload(Family.dependents),
            selectinload(Family.loans).selectinload(Loan.equipment),
            selectinload(Family.food_baskets),
            selectinload(Family.visit_requests).selectinload(VisitRequest.execution),
        )
        .where(Family.id == family_id)
    )
    family = db.execute(stmt).scalar_one()
    if not family.is_active:
        context = _template_context(request)
        context.update(
            {
                "family": family,
                "current_user": current_user,
                "family_warning": "Família inativa: novos atendimentos estão bloqueados.",
                "basket_alerts": _build_basket_alerts(db, family),
                "food_basket_status_options": FOOD_BASKET_STATUS_OPTIONS,
                "basket_error": "Família inativa: não é possível registrar cesta.",
                "visit_request_status_options": VISIT_REQUEST_STATUS_OPTIONS,
                "visit_execution_result_options": VISIT_EXECUTION_RESULT_OPTIONS,
                "visit_pending_count": sum(
                    1 for item in family.visit_requests if item.status == VisitRequestStatus.PENDING
                ),
                "visit_alerts": _build_visit_alerts(family),
            }
        )
        return templates.TemplateResponse("family_detail.html", context, status_code=403)
    if family.vulnerability == VulnerabilityLevel.NONE:
        context = _template_context(request)
        context.update(
            {
                "family": family,
                "current_user": current_user,
                "family_warning": None,
                "basket_alerts": _build_basket_alerts(db, family),
                "food_basket_status_options": FOOD_BASKET_STATUS_OPTIONS,
                "basket_error": "Família sem vulnerabilidade elegível para cesta.",
                "visit_request_status_options": VISIT_REQUEST_STATUS_OPTIONS,
                "visit_execution_result_options": VISIT_EXECUTION_RESULT_OPTIONS,
                "visit_pending_count": sum(
                    1 for item in family.visit_requests if item.status == VisitRequestStatus.PENDING
                ),
                "visit_alerts": _build_visit_alerts(family),
            }
        )
        return templates.TemplateResponse("family_detail.html", context, status_code=400)
    try:
        month, year = _parse_reference_month_year(month_year)
        basket_status = FoodBasketStatus(status_value)
        basket_family_status = FamilyBenefitStatus(family_status)
        parsed_delivery_date = _parse_date(delivery_date) if delivery_date else date.today()
        parsed_last_withdrawal = _parse_date(last_withdrawal_at) if last_withdrawal_at else None
        if quantity < 1:
            raise ValueError("Quantidade deve ser maior ou igual a 1.")
        if frequency_months < 1:
            raise ValueError("Frequência deve ser maior ou igual a 1 mês.")
    except ValueError as exc:
        context = _template_context(request)
        context.update(
            {
                "family": family,
                "current_user": current_user,
                "family_warning": None,
                "basket_alerts": _build_basket_alerts(db, family),
                "food_basket_status_options": FOOD_BASKET_STATUS_OPTIONS,
                "basket_error": str(exc),
                "visit_request_status_options": VISIT_REQUEST_STATUS_OPTIONS,
                "visit_execution_result_options": VISIT_EXECUTION_RESULT_OPTIONS,
                "visit_pending_count": sum(
                    1 for item in family.visit_requests if item.status == VisitRequestStatus.PENDING
                ),
                "visit_alerts": _build_visit_alerts(family),
            }
        )
        return templates.TemplateResponse("family_detail.html", context, status_code=400)
    require_month_open(db, month=month, year=year)

    existing = db.execute(
        select(FoodBasket).where(
            FoodBasket.family_id == family.id,
            FoodBasket.reference_month == month,
            FoodBasket.reference_year == year,
        )
    ).scalar_one_or_none()
    if existing:
        context = _template_context(request)
        context.update(
            {
                "family": family,
                "current_user": current_user,
                "family_warning": None,
                "basket_alerts": _build_basket_alerts(db, family),
                "food_basket_status_options": FOOD_BASKET_STATUS_OPTIONS,
                "basket_error": "Já existe cesta registrada para esta família no mês informado.",
                "visit_request_status_options": VISIT_REQUEST_STATUS_OPTIONS,
                "visit_execution_result_options": VISIT_EXECUTION_RESULT_OPTIONS,
                "visit_pending_count": sum(
                    1 for item in family.visit_requests if item.status == VisitRequestStatus.PENDING
                ),
                "visit_alerts": _build_visit_alerts(family),
            }
        )
        return templates.TemplateResponse("family_detail.html", context, status_code=400)
    db.add(
        FoodBasket(
            family_id=family.id,
            reference_month=month,
            reference_year=year,
            status=basket_status,
            family_status=basket_family_status,
            delivery_date=parsed_delivery_date,
            quantity=quantity,
            frequency_months=frequency_months,
            last_withdrawal_at=parsed_last_withdrawal,
            last_withdrawal_responsible=last_withdrawal_responsible.strip() or None,
            notes=notes or None,
        )
    )
    _recalculate_family_income(family)
    db.commit()
    return RedirectResponse(url=f"/familias/{family.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/familias/{family_id}/cestas/{basket_id}/editar")
def update_food_basket(
    request: Request,
    family_id: int,
    basket_id: int,
    status_value: str = Form(...),
    family_status: str = Form(FamilyBenefitStatus.ELIGIBLE.value),
    delivery_date: str = Form(""),
    quantity: int = Form(1),
    frequency_months: int = Form(1),
    last_withdrawal_at: str = Form(""),
    last_withdrawal_responsible: str = Form(""),
    notes: str = Form(default=""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_baskets")),
):
    basket = db.get(FoodBasket, basket_id)
    if not basket or basket.family_id != family_id:
        return RedirectResponse(url=f"/familias/{family_id}", status_code=status.HTTP_303_SEE_OTHER)
    require_month_open(db, month=basket.reference_month, year=basket.reference_year)
    try:
        basket.status = FoodBasketStatus(status_value)
        basket.family_status = FamilyBenefitStatus(family_status)
    except ValueError:
        basket.status = basket.status
    basket.delivery_date = _parse_date(delivery_date) if delivery_date else basket.delivery_date
    basket.quantity = quantity if quantity >= 1 else basket.quantity
    basket.frequency_months = frequency_months if frequency_months >= 1 else basket.frequency_months
    basket.last_withdrawal_at = _parse_date(last_withdrawal_at) if last_withdrawal_at else None
    basket.last_withdrawal_responsible = last_withdrawal_responsible.strip() or None
    basket.notes = notes or None
    db.commit()
    return RedirectResponse(url=f"/familias/{family_id}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/familias/{family_id}/cestas/{basket_id}/remover")
def remove_food_basket(
    family_id: int,
    basket_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_baskets")),
):
    basket = db.get(FoodBasket, basket_id)
    if basket and basket.family_id == family_id:
        require_month_open(db, month=basket.reference_month, year=basket.reference_year)
        db.delete(basket)
        db.commit()
    return RedirectResponse(url=f"/familias/{family_id}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/familias/{family_id}/visitas")
def create_visit_request(
    request: Request,
    family_id: int,
    scheduled_date: str = Form(...),
    request_notes: str = Form(default=""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_visits")),
):
    family = db.execute(
        select(Family)
        .options(
            selectinload(Family.dependents),
            selectinload(Family.loans).selectinload(Loan.equipment),
            selectinload(Family.food_baskets),
            selectinload(Family.visit_requests).selectinload(VisitRequest.execution),
        )
        .where(Family.id == family_id)
    ).scalar_one_or_none()
    if not family:
        return RedirectResponse(url="/familias", status_code=status.HTTP_303_SEE_OTHER)
    if not family.is_active:
        context = _template_context(request)
        context.update(
            {
                "family": family,
                "current_user": current_user,
                "family_warning": "Família inativa: novos atendimentos estão bloqueados.",
                "basket_alerts": _build_basket_alerts(db, family),
                "food_basket_status_options": FOOD_BASKET_STATUS_OPTIONS,
                "visit_request_status_options": VISIT_REQUEST_STATUS_OPTIONS,
                "visit_execution_result_options": VISIT_EXECUTION_RESULT_OPTIONS,
                "visit_pending_count": sum(
                    1 for item in family.visit_requests if item.status == VisitRequestStatus.PENDING
                ),
                "visit_alerts": _build_visit_alerts(family),
                "visit_error": "Família inativa: não é possível solicitar visita.",
            }
        )
        return templates.TemplateResponse("family_detail.html", context, status_code=403)
    try:
        parsed_date = _parse_date(scheduled_date)
    except ValueError as exc:
        context = _template_context(request)
        context.update(
            {
                "family": family,
                "current_user": current_user,
                "family_warning": None,
                "basket_alerts": _build_basket_alerts(db, family),
                "food_basket_status_options": FOOD_BASKET_STATUS_OPTIONS,
                "visit_request_status_options": VISIT_REQUEST_STATUS_OPTIONS,
                "visit_execution_result_options": VISIT_EXECUTION_RESULT_OPTIONS,
                "visit_pending_count": sum(
                    1 for item in family.visit_requests if item.status == VisitRequestStatus.PENDING
                ),
                "visit_alerts": _build_visit_alerts(family),
                "visit_error": str(exc),
            }
        )
        return templates.TemplateResponse("family_detail.html", context, status_code=400)
    require_month_open(db, target_date=parsed_date)
    db.add(
        VisitRequest(
            family_id=family.id,
            requested_by_user_id=current_user.id,
            scheduled_date=parsed_date,
            request_notes=request_notes or None,
        )
    )
    _recalculate_family_income(family)
    db.commit()
    return RedirectResponse(url=f"/familias/{family.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/familias/{family_id}/visitas/{visit_request_id}/executar")
def execute_visit_request(
    request: Request,
    family_id: int,
    visit_request_id: int,
    executed_at: str = Form(...),
    result_value: str = Form(VisitExecutionResult.COMPLETED.value),
    notes: str = Form(default=""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_visits")),
):
    family = db.execute(
        select(Family)
        .options(
            selectinload(Family.dependents),
            selectinload(Family.loans).selectinload(Loan.equipment),
            selectinload(Family.food_baskets),
            selectinload(Family.visit_requests).selectinload(VisitRequest.execution),
        )
        .where(Family.id == family_id)
    ).scalar_one_or_none()
    visit_request = db.get(VisitRequest, visit_request_id)
    if not family or not visit_request or visit_request.family_id != family.id:
        return RedirectResponse(url=f"/familias/{family_id}", status_code=status.HTTP_303_SEE_OTHER)
    try:
        executed_date = _parse_date(executed_at)
        result = VisitExecutionResult(result_value)
    except ValueError as exc:
        context = _template_context(request)
        context.update(
            {
                "family": family,
                "current_user": current_user,
                "family_warning": (
                    None
                    if family.is_active
                    else "Família inativa: novos atendimentos estão bloqueados."
                ),
                "basket_alerts": _build_basket_alerts(db, family),
                "food_basket_status_options": FOOD_BASKET_STATUS_OPTIONS,
                "visit_request_status_options": VISIT_REQUEST_STATUS_OPTIONS,
                "visit_execution_result_options": VISIT_EXECUTION_RESULT_OPTIONS,
                "visit_pending_count": sum(
                    1 for item in family.visit_requests if item.status == VisitRequestStatus.PENDING
                ),
                "visit_alerts": _build_visit_alerts(family),
                "visit_error": str(exc),
            }
        )
        return templates.TemplateResponse("family_detail.html", context, status_code=400)
    require_month_open(db, target_date=visit_request.scheduled_date)
    if visit_request.execution:
        visit_request.execution.executed_by_user_id = current_user.id
        visit_request.execution.executed_at = executed_date
        visit_request.execution.result = result
        visit_request.execution.notes = notes or None
    else:
        db.add(
            VisitExecution(
                visit_request_id=visit_request.id,
                executed_by_user_id=current_user.id,
                executed_at=executed_date,
                result=result,
                notes=notes or None,
            )
        )
    visit_request.status = (
        VisitRequestStatus.COMPLETED
        if result != VisitExecutionResult.NOT_COMPLETED
        else VisitRequestStatus.PENDING
    )
    _recalculate_family_income(family)
    db.commit()
    return RedirectResponse(url=f"/familias/{family.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/equipamentos", response_class=HTMLResponse)
def list_equipment(
    request: Request,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("view_equipment")),
) -> HTMLResponse:
    stmt = select(Equipment).order_by(Equipment.code)
    equipment_items = db.execute(stmt).scalars().all()
    context = _template_context(request)
    context.update({"equipment_items": equipment_items})
    return templates.TemplateResponse("equipment_list.html", context)


@app.get("/equipamentos/novo", response_class=HTMLResponse)
def new_equipment_form(
    request: Request,
    current_user: User = Depends(require_permissions("manage_equipment")),
) -> HTMLResponse:
    context = _equipment_form_context(request, None, None)
    return templates.TemplateResponse("equipment_form.html", context)


@app.post("/equipamentos/novo", response_model=None)
def create_equipment(
    request: Request,
    description: str = Form(...),
    equipment_type: str = Form(EquipmentType.OTHER.value),
    condition_status: str = Form(EquipmentCondition.GOOD.value),
    notes: str = Form(""),
    status_value: str = Form(EquipmentStatus.AVAILABLE.value),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_equipment")),
) -> RedirectResponse | HTMLResponse:
    try:
        description = _require_value(description, "Descrição")
        type_enum = EquipmentType(equipment_type)
        condition_enum = EquipmentCondition(condition_status)
        status_enum = EquipmentStatus(status_value)
    except ValueError as exc:
        context = _equipment_form_context(request, None, str(exc))
        return templates.TemplateResponse("equipment_form.html", context, status_code=400)
    code = _generate_equipment_code(db)
    equipment = Equipment(code=code, description=description, equipment_type=type_enum, condition_status=condition_enum, notes=notes.strip() or None, status=status_enum)
    db.add(equipment)
    db.commit()
    return RedirectResponse(
        url=f"/equipamentos/{equipment.id}", status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/equipamentos/{equipment_id}", response_class=HTMLResponse)
def view_equipment(
    request: Request,
    equipment_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("view_equipment")),
) -> HTMLResponse:
    stmt = (
        select(Equipment)
        .options(selectinload(Equipment.loans).selectinload(Loan.family))
        .where(Equipment.id == equipment_id)
    )
    equipment = db.execute(stmt).scalar_one_or_none()
    if not equipment:
        return RedirectResponse(url="/equipamentos", status_code=status.HTTP_303_SEE_OTHER)
    context = _template_context(request)
    context.update({"equipment": equipment})
    return templates.TemplateResponse("equipment_detail.html", context)


@app.get("/equipamentos/{equipment_id}/editar", response_class=HTMLResponse)
def edit_equipment_form(
    request: Request,
    equipment_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_equipment")),
) -> HTMLResponse:
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        return RedirectResponse(url="/equipamentos", status_code=status.HTTP_303_SEE_OTHER)
    is_locked = equipment.status == EquipmentStatus.LOANED
    context = _equipment_form_context(request, equipment, None, is_locked=is_locked)
    return templates.TemplateResponse("equipment_form.html", context)


@app.post("/equipamentos/{equipment_id}/editar", response_model=None)
def update_equipment(
    request: Request,
    equipment_id: int,
    description: str = Form(...),
    equipment_type: str = Form(EquipmentType.OTHER.value),
    condition_status: str = Form(EquipmentCondition.GOOD.value),
    notes: str = Form(""),
    status_value: str | None = Form(None),
    code: str = Form(""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_equipment")),
) -> RedirectResponse | HTMLResponse:
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        return RedirectResponse(url="/equipamentos", status_code=status.HTTP_303_SEE_OTHER)
    is_locked = equipment.status == EquipmentStatus.LOANED
    try:
        description = _require_value(description, "Descrição")
        type_enum = EquipmentType(equipment_type)
        condition_enum = EquipmentCondition(condition_status)
        status_enum = EquipmentStatus(status_value or equipment.status.value)
        if is_locked and code and code != equipment.code:
            raise ValueError("O código não pode ser alterado enquanto o item está emprestado.")
        if is_locked and status_enum != equipment.status:
            raise ValueError("O status não pode ser alterado enquanto o item está emprestado.")
        if code:
            normalized_code = code.strip()
            existing = db.execute(
                select(Equipment).where(Equipment.code == normalized_code)
            ).scalar_one_or_none()
            if existing and existing.id != equipment.id:
                raise ValueError("Código já utilizado em outro equipamento.")
            equipment.code = normalized_code
    except ValueError as exc:
        context = _equipment_form_context(request, equipment, str(exc), is_locked=is_locked)
        return templates.TemplateResponse("equipment_form.html", context, status_code=400)
    equipment.description = description
    equipment.equipment_type = type_enum
    equipment.condition_status = condition_enum
    equipment.notes = notes.strip() or None
    equipment.status = status_enum
    db.commit()
    return RedirectResponse(
        url=f"/equipamentos/{equipment.id}", status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/equipamentos/{equipment_id}/emprestimo", response_class=HTMLResponse)
def new_loan_form(
    request: Request,
    equipment_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_equipment")),
) -> HTMLResponse:
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        return RedirectResponse(url="/equipamentos", status_code=status.HTTP_303_SEE_OTHER)
    families = db.execute(select(Family).order_by(Family.responsible_name)).scalars().all()
    context = _loan_form_context(request, equipment, families, None)
    return templates.TemplateResponse("loan_form.html", context)


@app.post("/equipamentos/{equipment_id}/emprestimo", response_model=None)
def create_loan(
    request: Request,
    equipment_id: int,
    family_id: int = Form(...),
    loan_date: str = Form(...),
    due_date: str = Form(""),
    notes: str = Form(""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_equipment")),
) -> RedirectResponse | HTMLResponse:
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        return RedirectResponse(url="/equipamentos", status_code=status.HTTP_303_SEE_OTHER)
    families = db.execute(select(Family).order_by(Family.responsible_name)).scalars().all()
    try:
        if equipment.status != EquipmentStatus.AVAILABLE:
            raise ValueError("Item indisponível para empréstimo.")
        active_loan = db.execute(
            select(Loan).where(Loan.equipment_id == equipment.id, Loan.status == LoanStatus.ACTIVE)
        ).scalar_one_or_none()
        if active_loan:
            raise ValueError("Item já possui empréstimo ativo.")
        family = db.get(Family, family_id)
        if not family:
            raise ValueError("Família inválida.")
        if not family.is_active:
            raise ValueError("Família inativa: empréstimos estão bloqueados.")
        parsed_loan_date = _parse_date(loan_date)
        if not due_date:
            raise ValueError("Prazo de devolução é obrigatório.")
        parsed_due_date = _parse_date(due_date)
        if parsed_due_date < parsed_loan_date:
            raise ValueError("Prazo de devolução deve ser igual ou posterior à data de empréstimo.")
    except ValueError as exc:
        context = _loan_form_context(request, equipment, families, str(exc))
        return templates.TemplateResponse("loan_form.html", context, status_code=400)
    require_month_open(db, target_date=parsed_loan_date)
    loan = Loan(
        equipment=equipment,
        family=family,
        loan_date=parsed_loan_date,
        due_date=parsed_due_date,
        notes=notes or None,
        status=LoanStatus.ACTIVE,
    )
    equipment.status = EquipmentStatus.LOANED
    db.add(loan)
    db.flush()
    for worker_name, worker_income in workers_payload:
        db.add(FamilyWorker(family_id=family.id, name=worker_name, monthly_income=worker_income))
    db.flush()
    _recalculate_family_income(family)
    log_action(
        db,
        current_user.id,
        "LOAN",
        "equipment_loan",
        loan.id,
        after={"equipment_id": equipment.id, "family_id": family.id, "status": loan.status},
    )
    db.commit()
    return RedirectResponse(
        url=f"/equipamentos/{equipment.id}", status_code=status.HTTP_303_SEE_OTHER
    )


@app.post("/equipamentos/{equipment_id}/devolver", response_model=None)
def return_loan(
    request: Request,
    equipment_id: int,
    return_condition: str = Form(EquipmentCondition.GOOD.value),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_equipment")),
) -> RedirectResponse | HTMLResponse:
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        return RedirectResponse(url="/equipamentos", status_code=status.HTTP_303_SEE_OTHER)
    active_loan = db.execute(
        select(Loan).where(Loan.equipment_id == equipment.id, Loan.status == LoanStatus.ACTIVE)
    ).scalar_one_or_none()
    if not active_loan:
        stmt = (
            select(Equipment)
            .options(selectinload(Equipment.loans).selectinload(Loan.family))
            .where(Equipment.id == equipment_id)
        )
        equipment = db.execute(stmt).scalar_one()
        context = _template_context(request)
        context.update({"equipment": equipment, "error": "Nenhum empréstimo ativo para devolução."})
        return templates.TemplateResponse("equipment_detail.html", context, status_code=400)
    before = {"status": active_loan.status, "returned_at": active_loan.returned_at}
    require_month_open(db, target_date=active_loan.loan_date)
    try:
        parsed_return_condition = EquipmentCondition(return_condition)
    except ValueError:
        parsed_return_condition = EquipmentCondition.GOOD
    active_loan.status = LoanStatus.RETURNED
    active_loan.returned_at = date.today()
    active_loan.return_condition = parsed_return_condition
    equipment.status = EquipmentStatus.MAINTENANCE if parsed_return_condition == EquipmentCondition.NEEDS_REPAIR else EquipmentStatus.AVAILABLE
    log_action(
        db,
        current_user.id,
        "RETURN",
        "equipment_loan",
        active_loan.id,
        before=before,
        after={"status": active_loan.status, "returned_at": active_loan.returned_at},
    )
    db.commit()
    return RedirectResponse(
        url=f"/equipamentos/{equipment.id}", status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/rua", response_class=HTMLResponse)
def list_street_people(
    request: Request,
    q: str = "",
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("view_street")),
) -> HTMLResponse:
    stmt = select(StreetPerson).order_by(StreetPerson.created_at.desc())
    search = (q or "").strip()
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            StreetPerson.reference_location.ilike(like)
            | StreetPerson.full_name.ilike(like)
            | StreetPerson.cpf.ilike(f"%{_normalize_cpf(search)}%")
        )
    people = db.execute(stmt).scalars().all()
    context = _template_context(request)
    context.update({"people": people, "q": q, "current_user": current_user})
    return templates.TemplateResponse("street/street_people_list.html", context)


@app.get("/rua/nova", response_class=HTMLResponse)
def new_street_person_form(
    request: Request,
    db=Depends(get_db),
    _current_user: User = Depends(require_permissions("manage_street")),
) -> HTMLResponse:
    return templates.TemplateResponse(
        "street/street_person_form.html", _street_form_context(request, None, None, _active_consent_term(db))
    )


@app.post("/rua/nova")
def create_street_person(
    request: Request,
    full_name: str = Form(""),
    cpf: str = Form(""),
    rg: str = Form(""),
    birth_date: str = Form(""),
    approximate_age: str = Form(""),
    gender: str = Form(""),
    documents_status: str = Form(DocumentStatus.PARTIAL.value),
    street_time: str = Form(""),
    immediate_needs: str = Form(""),
    wants_prayer: bool = Form(default=False),
    accepts_visit: bool = Form(default=False),
    spiritual_decision: str = Form(""),
    reference_location: str = Form(...),
    benefit_notes: str = Form(""),
    general_notes: str = Form(""),
    consent_accepted: bool = Form(default=False),
    consent_signature_name: str = Form(default=""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_street")),
):
    active_term = _active_consent_term(db)
    try:
        reference = _require_value(reference_location, "Local de referência")
        parsed_cpf = _validate_street_cpf(db, cpf) if cpf.strip() else None
        parsed_birth_date = _parse_date(birth_date) if birth_date else None
        parsed_approximate_age = int(approximate_age) if approximate_age.strip() else None
        if parsed_approximate_age is not None and parsed_approximate_age < 0:
            raise ValueError("Idade aproximada inválida.")
        parsed_documents_status = DocumentStatus(documents_status)
        parsed_street_time = StreetTime(street_time) if street_time else None
        parsed_spiritual_decision = SpiritualDecision(spiritual_decision) if spiritual_decision else None
        signature_name = consent_signature_name.strip() or (current_user.name if consent_accepted else "")
        _require_consent(consent_accepted, active_term)
    except ValueError as exc:
        person = StreetPerson(
            full_name=full_name or None,
            cpf=_normalize_cpf(cpf) if cpf else None,
            rg=rg or None,
            gender=gender or None,
            documents_status=DocumentStatus.PARTIAL,
            reference_location=reference_location or "",
            benefit_notes=benefit_notes or None,
            general_notes=general_notes or None,
        )
        return templates.TemplateResponse(
            "street/street_person_form.html",
            _street_form_context(request, person, str(exc), active_term),
            status_code=400,
        )

    person = StreetPerson(
        full_name=full_name.strip() or None,
        cpf=parsed_cpf,
        rg=rg.strip() or None,
        birth_date=parsed_birth_date,
        approximate_age=parsed_approximate_age,
        gender=gender.strip() or None,
        documents_status=parsed_documents_status,
        street_time=parsed_street_time,
        immediate_needs=immediate_needs.strip() or None,
        wants_prayer=wants_prayer,
        accepts_visit=accepts_visit,
        spiritual_decision=parsed_spiritual_decision,
        reference_location=reference,
        benefit_notes=benefit_notes.strip() or None,
        general_notes=general_notes.strip() or None,
        consent_term_version=active_term.version if active_term else None,
        consent_accepted=consent_accepted,
        consent_accepted_at=datetime.utcnow(),
        consent_accepted_by_user_id=current_user.id,
    )
    db.add(person)
    db.flush()
    log_action(db, current_user.id, "CREATE", "street_person", person.id, after={"id": person.id, "cpf": person.cpf, "reference_location": person.reference_location})
    db.commit()
    return RedirectResponse(url=f"/rua/{person.id}", status_code=status.HTTP_303_SEE_OTHER)




@app.get("/pessoas/{person_id}/export.pdf")
def export_street_person_pdf(
    request: Request,
    person_id: int,
    db=Depends(get_db),
    _current_user: User = Depends(require_permissions("view_street")),
):
    person = db.execute(
        select(StreetPerson)
        .options(selectinload(StreetPerson.services), selectinload(StreetPerson.referrals))
        .where(StreetPerson.id == person_id)
    ).scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")

    current_user = getattr(request.state, "user", None)
    rows = [
        ["Nome", person.full_name or "Não informado"],
        ["CPF", person.cpf or "-"],
        ["RG", person.rg or "-"],
        ["Local de referência", person.reference_location],
        ["Atendimentos", len(person.services)],
        ["Encaminhamentos", len(person.referrals)],
        ["Status", "Ativo" if person.is_active else "Inativo"],
    ]

    pdf_content = generate_report_pdf(
        title=f"Ficha Pessoa em Situação de Rua #{person.id}",
        month=None,
        year=None,
        sections=[
            {"type": "table", "title": "Dados cadastrais", "headers": ["Campo", "Valor"], "rows": rows},
            {
                "type": "text",
                "title": "Totalizadores",
                "content": (
                    f"Total de registros: {len(rows)} | Total de atendimentos: {len(person.services)} "
                    f"| Total de encaminhamentos: {len(person.referrals)}"
                ),
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
        headers={"Content-Disposition": f'attachment; filename="pessoa-{person_id}.pdf"'},
    )

@app.get("/rua/{person_id}", response_class=HTMLResponse)
def street_person_detail(
    request: Request,
    person_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("view_street")),
) -> HTMLResponse:
    stmt = (
        select(StreetPerson)
        .options(selectinload(StreetPerson.services), selectinload(StreetPerson.referrals))
        .where(StreetPerson.id == person_id)
    )
    person = db.execute(stmt).scalar_one_or_none()
    if not person:
        return RedirectResponse(url="/rua", status_code=status.HTTP_303_SEE_OTHER)
    context = _template_context(request)
    context.update(
        {
            "person": person,
            "error": None,
            "service_error": None,
            "referral_error": None,
            "service_types": DEFAULT_STREET_SERVICE_TYPES,
            "referral_status_options": REFERRAL_STATUS_OPTIONS,
            "referral_target_options": REFERRAL_TARGET_OPTIONS,
            "current_user": current_user,
        }
    )
    return templates.TemplateResponse("street/street_person_detail.html", context)


@app.post("/rua/{person_id}/atendimentos")
def create_street_service(
    request: Request,
    person_id: int,
    service_type: str = Form(...),
    service_date: str = Form(...),
    responsible_name: str = Form(...),
    notes: str = Form(""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_street")),
):
    person = db.get(StreetPerson, person_id)
    if not person:
        return RedirectResponse(url="/rua", status_code=status.HTTP_303_SEE_OTHER)
    try:
        parsed_service_type = _require_value(service_type, "Tipo de atendimento")
        parsed_service_date = _parse_date(service_date)
        parsed_responsible = _require_value(responsible_name, "Responsável")
    except ValueError as exc:
        return _street_person_detail_with_error(
            request, db, person_id, current_user, service_error=str(exc)
        )
    require_month_open(db, target_date=parsed_service_date)
    db.add(
        StreetService(
            person_id=person.id,
            service_type=parsed_service_type,
            service_date=parsed_service_date,
            responsible_name=parsed_responsible,
            notes=notes.strip() or None,
        )
    )
    db.commit()
    return RedirectResponse(url=f"/rua/{person.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/rua/{person_id}/encaminhamentos")
def create_referral(
    request: Request,
    person_id: int,
    recovery_home: str = Form(...),
    referral_date: str = Form(...),
    target: str = Form(ReferralTarget.OTHER.value),
    status_value: str = Form(ReferralStatus.REFERRED.value),
    notes: str = Form(""),
    db=Depends(get_db),
    current_user: User = Depends(require_permissions("manage_street")),
):
    person = db.get(StreetPerson, person_id)
    if not person:
        return RedirectResponse(url="/rua", status_code=status.HTTP_303_SEE_OTHER)
    try:
        parsed_home = _require_value(recovery_home, "Casa de recuperação")
        parsed_date = _parse_date(referral_date)
        parsed_status = ReferralStatus(status_value)
        parsed_target = ReferralTarget(target)
    except ValueError as exc:
        return _street_person_detail_with_error(
            request, db, person_id, current_user, referral_error=str(exc)
        )
    require_month_open(db, target_date=parsed_date)
    db.add(
        Referral(
            person_id=person.id,
            recovery_home=parsed_home,
            referral_date=parsed_date,
            target=parsed_target,
            status=parsed_status,
            notes=notes.strip() or None,
        )
    )
    db.commit()
    return RedirectResponse(url=f"/rua/{person.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/rua/encaminhamentos/{referral_id}/status")
def update_referral_status(
    referral_id: int,
    status_value: str = Form(...),
    db=Depends(get_db),
    _current_user: User = Depends(require_permissions("manage_street")),
):
    referral = db.get(Referral, referral_id)
    if not referral:
        return RedirectResponse(url="/rua", status_code=status.HTTP_303_SEE_OTHER)
    require_month_open(db, target_date=referral.referral_date)
    try:
        referral.status = ReferralStatus(status_value)
    except ValueError:
        return RedirectResponse(
            url=f"/rua/{referral.person_id}", status_code=status.HTTP_303_SEE_OTHER
        )
    db.commit()
    return RedirectResponse(url=f"/rua/{referral.person_id}", status_code=status.HTTP_303_SEE_OTHER)


def _street_person_detail_with_error(
    request: Request,
    db,
    person_id: int,
    current_user: User,
    service_error: str | None = None,
    referral_error: str | None = None,
):
    stmt = (
        select(StreetPerson)
        .options(selectinload(StreetPerson.services), selectinload(StreetPerson.referrals))
        .where(StreetPerson.id == person_id)
    )
    person = db.execute(stmt).scalar_one()
    context = _template_context(request)
    context.update(
        {
            "person": person,
            "error": None,
            "service_error": service_error,
            "referral_error": referral_error,
            "service_types": DEFAULT_STREET_SERVICE_TYPES,
            "referral_status_options": REFERRAL_STATUS_OPTIONS,
            "referral_target_options": REFERRAL_TARGET_OPTIONS,
            "current_user": current_user,
        }
    )
    return templates.TemplateResponse("street/street_person_detail.html", context, status_code=400)


@app.get("/me")
def whoami(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"id": str(current_user.id), "name": current_user.name, "email": current_user.email}
