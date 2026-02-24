from __future__ import annotations

import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app.main as main
from app.closures.routes import get_db as closures_get_db
from app.dashboard.routes import get_db as dashboard_get_db
from app.deliveries.routes import get_db as deliveries_get_db
from app.history.monthly_history import get_db as history_get_db
from app.reports.routes import get_db as reports_get_db


@pytest.fixture
def client(tmp_path: Path):
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )
    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    alembic_cfg = Config(str(ROOT_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(ROOT_DIR / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")

    main.engine = engine
    main.auth_engine = engine
    main.SessionLocal = testing_session_local
    main.AuthSessionLocal = testing_session_local

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[main.get_db] = override_get_db
    main.app.dependency_overrides[main.get_auth_db] = override_get_db
    main.app.dependency_overrides[closures_get_db] = override_get_db
    main.app.dependency_overrides[dashboard_get_db] = override_get_db
    main.app.dependency_overrides[deliveries_get_db] = override_get_db
    main.app.dependency_overrides[reports_get_db] = override_get_db
    main.app.dependency_overrides[history_get_db] = override_get_db

    with TestClient(main.app) as test_client:
        yield test_client

    main.app.dependency_overrides.clear()
    if previous_database_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = previous_database_url
