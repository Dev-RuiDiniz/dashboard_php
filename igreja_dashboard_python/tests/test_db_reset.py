from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.reset import build_reset_context, enforce_reset_safety, run_reset
from app.models import Role, User


def test_enforce_reset_safety_requires_confirmation(monkeypatch):
    monkeypatch.delenv("RESET_DB_CONFIRM", raising=False)
    context = build_reset_context(database_url="sqlite:////tmp/test_reset_guard.db", app_env="development")

    try:
        enforce_reset_safety(context)
        assert False, "Reset deveria falhar sem confirmação explícita"
    except RuntimeError as exc:
        assert "RESET_DB_CONFIRM=YES" in str(exc)


def test_run_reset_sqlite_creates_seeded_admin(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "reset_seed.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("RESET_DB_CONFIRM", "YES")
    monkeypatch.setenv("ADMIN_EMAIL", "seed-admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "Senha1234")
    monkeypatch.setenv("ADMIN_NAME", "Seed Admin")
    monkeypatch.delenv("RESET_DB_TOKEN", raising=False)

    run_reset(database_url=db_url, app_env="development", remove_legacy_sqlite=False)
    run_reset(database_url=db_url, app_env="development", remove_legacy_sqlite=False)

    engine = create_engine(db_url, future=True)
    with Session(engine) as db:
        users = db.execute(select(User).where(User.email == "seed-admin@example.com")).scalars().all()
        roles = db.execute(select(Role).where(Role.name == "Admin")).scalars().all()
        user_roles = users[0].role_names()

    engine.dispose()

    assert len(users) == 1
    assert len(roles) == 1
    assert "Admin" in user_roles


def test_enforce_reset_safety_requires_token_in_production(monkeypatch):
    monkeypatch.setenv("RESET_DB_CONFIRM", "YES")
    monkeypatch.setenv("REQUIRE_RESET_TOKEN", "token-correto")
    monkeypatch.delenv("RESET_DB_TOKEN", raising=False)

    context = build_reset_context(database_url="postgresql+psycopg://user:pass@localhost/db", app_env="production")

    try:
        enforce_reset_safety(context)
        assert False, "Reset deveria falhar em produção sem token"
    except RuntimeError as exc:
        assert "RESET_DB_TOKEN" in str(exc)

    monkeypatch.setenv("RESET_DB_TOKEN", "token-correto")
    enforce_reset_safety(context)
