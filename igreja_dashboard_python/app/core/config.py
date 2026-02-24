from __future__ import annotations

import os
from pathlib import Path
import tempfile

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


def _resolve_data_dir() -> Path:
    configured_data_dir = os.getenv("DATA_DIR")
    if configured_data_dir:
        return Path(configured_data_dir).expanduser().resolve()

    default_data_dir = (BASE_DIR / "data").resolve()
    try:
        default_data_dir.mkdir(parents=True, exist_ok=True)
        probe_file = default_data_dir / ".write_check"
        probe_file.touch(exist_ok=True)
        probe_file.unlink(missing_ok=True)
        return default_data_dir
    except OSError:
        # Em plataformas serverless o diretório do código geralmente é read-only.
        fallback = Path(tempfile.gettempdir()) / "igreja_dashboard" / "data"
        return fallback.resolve()


DATA_DIR = _resolve_data_dir()


class Settings(BaseSettings):
    app_name: str = "Igreja Dashboard"
    client_name: str = "Primeira Igreja Batista de Taubaté"
    client_department: str = "Ação Social"
    app_env: str = "development"
    database_url: str = f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"
    secret_key: str = ""
    access_token_expire_minutes: int = 60 * 24
    log_level: str = "INFO"
    log_json: bool = True
    cookie_secure: bool = False
    default_admin_name: str = Field(
        default="Administrador",
        validation_alias=AliasChoices("DEFAULT_ADMIN_NAME", "ADMIN_NAME"),
    )
    default_admin_email: str = Field(
        default="admin@example.com",
        validation_alias=AliasChoices("DEFAULT_ADMIN_EMAIL", "ADMIN_EMAIL"),
    )
    default_admin_password: str = Field(
        default="admin123",
        validation_alias=AliasChoices("DEFAULT_ADMIN_PASSWORD", "ADMIN_PASSWORD"),
    )
    min_password_length: int = 8
    password_reset_token_ttl_minutes: int = 30
    login_rate_limit_max_requests: int = 30
    login_rate_limit_window_minutes: int = 5
    login_lockout_max_failures: int = 5
    login_lockout_window_minutes: int = 15
    feature_event_delivery: bool = False
    event_delivery_monthly_limit: int | None = None
    reports_dir: str = "data/reports"
    admin_override: bool = False

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
    )


    @property
    def auth_cookie_secure(self) -> bool:
        return self.app_env.lower() == "production" or self.cookie_secure


settings = Settings()

DATA_DIR.mkdir(parents=True, exist_ok=True)
