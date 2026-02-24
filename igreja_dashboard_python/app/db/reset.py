from __future__ import annotations

import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, func, inspect, select, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.auth import ROLE_DEFINITIONS
from app.core.config import BASE_DIR, settings
from app.core.security import get_password_hash
from app.models import (
    Equipment,
    EquipmentStatus,
    Family,
    FoodBasket,
    FoodBasketStatus,
    Loan,
    LoanStatus,
    Role,
    User,
    VisitExecution,
)

logger = logging.getLogger("app.db_reset")

PROTECTED_APP_ENV = "production"
DEFAULT_RESET_TOKEN = "RESET_ALLOWED"


@dataclass(slots=True)
class ResetContext:
    database_url: str
    app_env: str
    is_sqlite: bool
    is_postgres: bool
    sqlite_path: Path | None


def build_reset_context(database_url: str | None = None, app_env: str | None = None) -> ResetContext:
    effective_url = (database_url or os.getenv("DATABASE_URL") or settings.database_url).strip()
    if effective_url.startswith("postgres://"):
        effective_url = effective_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif effective_url.startswith("postgresql://") and "+" not in effective_url.split("://", 1)[0]:
        effective_url = effective_url.replace("postgresql://", "postgresql+psycopg://", 1)

    effective_env = (app_env or os.getenv("APP_ENV") or settings.app_env or "development").strip().lower()
    is_sqlite = effective_url.startswith("sqlite")
    is_postgres = effective_url.startswith("postgresql")
    sqlite_path: Path | None = None

    if is_sqlite:
        sqlite_path = _extract_sqlite_file_path(effective_url)

    return ResetContext(
        database_url=effective_url,
        app_env=effective_env,
        is_sqlite=is_sqlite,
        is_postgres=is_postgres,
        sqlite_path=sqlite_path,
    )


def _extract_sqlite_file_path(database_url: str) -> Path | None:
    url = make_url(database_url)
    if url.database in (None, "", ":memory:"):
        return None
    return Path(url.database).expanduser().resolve()


def _mask_database_url(database_url: str) -> str:
    try:
        url = make_url(database_url)
    except Exception:  # noqa: BLE001
        return database_url
    if url.password is None:
        return database_url
    return str(url.set(password="***"))


def enforce_reset_safety(context: ResetContext) -> None:
    confirm = os.getenv("RESET_DB_CONFIRM", "").strip().upper()
    if confirm != "YES":
        raise RuntimeError("Reset bloqueado: defina RESET_DB_CONFIRM=YES.")

    reset_token = os.getenv("RESET_DB_TOKEN", "").strip()
    required_token = os.getenv("REQUIRE_RESET_TOKEN", DEFAULT_RESET_TOKEN).strip() or DEFAULT_RESET_TOKEN

    if context.app_env == PROTECTED_APP_ENV:
        if not reset_token:
            raise RuntimeError("Reset em produção exige RESET_DB_TOKEN.")
        if reset_token != required_token:
            raise RuntimeError("Reset em produção bloqueado: RESET_DB_TOKEN inválido.")
    elif reset_token and reset_token != required_token:
        raise RuntimeError("RESET_DB_TOKEN informado não confere com REQUIRE_RESET_TOKEN.")


def _dispose_global_engine() -> None:
    try:
        from app.db import session as db_session

        current_engine = db_session.get_engine()
        if current_engine is not None:
            current_engine.dispose()
    except Exception:  # noqa: BLE001
        logger.debug("Falha ao descartar engine global antes do reset", exc_info=True)


def _remove_sqlite_artifacts(context: ResetContext, remove_legacy_sqlite: bool) -> list[Path]:
    removed: list[Path] = []
    if context.sqlite_path and context.sqlite_path.exists():
        context.sqlite_path.unlink()
        removed.append(context.sqlite_path)

    if not remove_legacy_sqlite:
        return removed

    data_dir = (BASE_DIR / "data").resolve()
    candidate_patterns = ("*.db", "*.sqlite", "*.sqlite3")
    for pattern in candidate_patterns:
        for candidate in data_dir.glob(pattern):
            resolved = candidate.resolve()
            if context.sqlite_path and resolved == context.sqlite_path:
                continue
            if resolved.exists():
                resolved.unlink()
                removed.append(resolved)

    wal_suffixes = ("-wal", "-shm", "-journal")
    for suffix in wal_suffixes:
        if context.sqlite_path:
            sidecar = Path(f"{context.sqlite_path}{suffix}")
            if sidecar.exists():
                sidecar.unlink()
                removed.append(sidecar)

    data_dir.mkdir(parents=True, exist_ok=True)
    return removed


def _reset_postgres_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS auth CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS domain CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


def _run_alembic_upgrade(database_url: str) -> None:
    alembic_cfg = Config(str(BASE_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BASE_DIR / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")


def seed_minimal(db_session: Session) -> None:
    role_map = {role.name: role for role in db_session.execute(select(Role)).scalars().all()}
    for role_name, definition in ROLE_DEFINITIONS.items():
        permissions = ",".join(sorted(definition["permissions"]))
        role = role_map.get(role_name)
        if role:
            role.description = str(definition["description"])
            role.permissions = permissions
        else:
            role = Role(name=role_name, description=str(definition["description"]), permissions=permissions)
            db_session.add(role)
            role_map[role_name] = role

    for role in list(role_map.values()):
        if role.name not in ROLE_DEFINITIONS:
            db_session.delete(role)

    admin_name = os.getenv("ADMIN_NAME") or os.getenv("DEFAULT_ADMIN_NAME") or settings.default_admin_name
    admin_email = (
        os.getenv("ADMIN_EMAIL") or os.getenv("DEFAULT_ADMIN_EMAIL") or settings.default_admin_email
    )
    admin_password = (
        os.getenv("ADMIN_PASSWORD")
        or os.getenv("DEFAULT_ADMIN_PASSWORD")
        or settings.default_admin_password
    )

    admin_role = role_map["Admin"]
    admin = db_session.execute(select(User).where(User.email == admin_email)).scalar_one_or_none()
    if not admin:
        admin = User(
            name=admin_name,
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            is_active=True,
            roles=[admin_role],
        )
        db_session.add(admin)
    else:
        admin.name = admin_name
        admin.is_active = True
        if not any(role.name == "Admin" for role in admin.roles):
            admin.roles.append(admin_role)

    db_session.commit()


def _assert_table_exists(inspector: Any, table: str, schema: str | None = None) -> None:
    if not inspector.has_table(table, schema=schema):
        qualified = f"{schema}.{table}" if schema else table
        raise AssertionError(f"Tabela obrigatória ausente: {qualified}")


def _assert_constraints(engine: Engine) -> None:
    inspector = inspect(engine)
    schema = "domain" if engine.dialect.name == "postgresql" else None
    auth_schema = "auth" if engine.dialect.name == "postgresql" else None

    required_tables = [
        ("users", auth_schema),
        ("roles", auth_schema),
        ("user_roles", auth_schema),
        ("families", schema),
        ("dependents", schema),
        ("equipment", schema),
        ("loans", schema),
        ("food_baskets", schema),
        ("street_people", schema),
        ("street_services", schema),
        ("referrals", schema),
        ("visit_requests", schema),
        ("visit_executions", schema),
    ]
    for table, table_schema in required_tables:
        _assert_table_exists(inspector, table, table_schema)

    user_uniques = inspector.get_unique_constraints("users", schema=auth_schema)
    if not any(set(u.get("column_names") or []) == {"email"} for u in user_uniques):
        raise AssertionError("Constraint unique de users.email não encontrada.")

    basket_uniques = inspector.get_unique_constraints("food_baskets", schema=schema)
    expected_basket = {"family_id", "reference_year", "reference_month"}
    if not any(set(u.get("column_names") or []) == expected_basket for u in basket_uniques):
        raise AssertionError("Constraint unique de food_baskets (family_id, year, month) ausente.")

    dependent_fks = inspector.get_foreign_keys("dependents", schema=schema)
    if not any("family_id" in (fk.get("constrained_columns") or []) for fk in dependent_fks):
        raise AssertionError("FK dependents.family_id ausente.")

    visit_uniques = inspector.get_unique_constraints("visit_executions", schema=schema)
    if not any(set(u.get("column_names") or []) == {"visit_request_id"} for u in visit_uniques):
        raise AssertionError("Constraint unique de visit_executions.visit_request_id ausente.")


def _run_domain_roundtrip(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as db:
        family = Family(
            responsible_name="Família Reset",
            responsible_cpf="99988877766",
            phone="12999990000",
            birth_date=date(1980, 1, 1),
            neighborhood="Centro",
            city="Taubaté",
            state="SP",
            vulnerability="Baixa",
            is_active=True,
        )
        db.add(family)
        db.flush()

        basket = FoodBasket(
            family_id=family.id,
            reference_year=2030,
            reference_month=1,
            status=FoodBasketStatus.DELIVERED,
            notes="Seed de validação",
        )
        equipment = Equipment(
            code="EQ-RESET-01",
            description="Cadeira de rodas validação",
            status=EquipmentStatus.AVAILABLE,
        )
        db.add_all([basket, equipment])
        db.flush()

        loan = Loan(
            equipment_id=equipment.id,
            family_id=family.id,
            loan_date=date(2030, 1, 2),
            status=LoanStatus.ACTIVE,
            notes="Roundtrip",
        )
        db.add(loan)
        db.commit()

    with session_factory() as db:
        family_count = db.execute(select(func.count(Family.id)).where(Family.is_active.is_(True))).scalar_one()
        if family_count <= 0:
            raise AssertionError("Validação falhou: não há famílias ativas após roundtrip.")

        grouped = db.execute(
            select(Family.neighborhood, func.count(Family.id))
            .where(Family.neighborhood.is_not(None))
            .group_by(Family.neighborhood)
        ).all()
        grouped_map = {row[0]: row[1] for row in grouped}
        if grouped_map.get("Centro", 0) < 1:
            raise AssertionError("Validação de agregação por bairro falhou.")

        loaded_basket = db.execute(
            select(FoodBasket).where(
                FoodBasket.reference_year == 2030,
                FoodBasket.reference_month == 1,
            )
        ).scalar_one_or_none()
        if not loaded_basket:
            raise AssertionError("FoodBasket de validação não encontrado após commit.")


def _verify_postgres_persistence(database_url: str) -> None:
    script = (
        "from sqlalchemy import create_engine,text;"
        "engine=create_engine('" + database_url.replace("'", "\\'") + "',future=True);"
        "conn=engine.connect();"
        "rows=conn.execute(text('SELECT COUNT(*) FROM domain.families')).scalar_one();"
        "print(rows);"
        "conn.close();"
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    value = int((result.stdout or "0").strip() or "0")
    if value <= 0:
        raise AssertionError("Persistência Postgres falhou: leitura em novo processo retornou 0 famílias.")


def run_post_reset_validations(database_url: str) -> None:
    engine = create_engine(database_url, future=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    try:
        _assert_constraints(engine)
        _run_domain_roundtrip(session_factory)
        if engine.dialect.name == "postgresql":
            _verify_postgres_persistence(database_url)
    finally:
        engine.dispose()


def run_reset(database_url: str | None = None, app_env: str | None = None, remove_legacy_sqlite: bool = True) -> None:
    context = build_reset_context(database_url=database_url, app_env=app_env)

    masked_url = _mask_database_url(context.database_url)
    logger.info("Iniciando reset de banco | APP_ENV=%s | DATABASE_URL=%s", context.app_env, masked_url)

    enforce_reset_safety(context)

    _dispose_global_engine()

    if context.is_sqlite:
        removed = _remove_sqlite_artifacts(context, remove_legacy_sqlite=remove_legacy_sqlite)
        logger.info("SQLite resetado; artefatos removidos: %s", [str(item) for item in removed])
    elif context.is_postgres:
        engine = create_engine(context.database_url, future=True)
        try:
            _reset_postgres_schema(engine)
        finally:
            engine.dispose()
    else:
        raise RuntimeError("Dialeto de banco não suportado para reset. Use SQLite ou PostgreSQL.")

    _run_alembic_upgrade(context.database_url)

    engine = create_engine(context.database_url, future=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    try:
        with session_factory() as db:
            seed_minimal(db)
    except SQLAlchemyError as exc:
        raise RuntimeError("Falha ao executar seed mínimo.") from exc
    finally:
        engine.dispose()

    run_post_reset_validations(context.database_url)
    logger.info("Reset concluído com sucesso")
