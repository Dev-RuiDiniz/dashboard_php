from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
from urllib.parse import urlparse

from app.core.config import DATA_DIR, settings


def resolve_sqlite_path(database_url: str | None = None) -> Path:
    url = database_url or settings.database_url
    if not url.startswith("sqlite"):
        raise ValueError("Backup automático suporta apenas SQLite.")

    if url.startswith("sqlite:///"):
        db_path = Path(url.replace("sqlite:///", "", 1))
    else:
        parsed = urlparse(url)
        db_path = Path(parsed.path)

    return db_path if db_path.is_absolute() else (Path.cwd() / db_path).resolve()


def create_backup(destination_dir: Path, database_url: str | None = None) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    source = resolve_sqlite_path(database_url)
    if not source.exists():
        raise FileNotFoundError(f"Banco de dados não encontrado: {source}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = destination_dir / f"app_backup_{timestamp}.sqlite3"
    shutil.copy2(source, backup_path)
    return backup_path


def restore_backup(backup_path: Path, database_url: str | None = None) -> Path:
    source = backup_path.resolve()
    if not source.exists():
        raise FileNotFoundError(f"Arquivo de backup não encontrado: {source}")

    target = resolve_sqlite_path(database_url)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def default_backup_dir() -> Path:
    return DATA_DIR / "backups"
