from __future__ import annotations

from pathlib import Path
import tempfile

from app.core.config import settings


def _reports_dir() -> Path:
    configured = settings.reports_dir.strip()
    base_path = Path(configured).expanduser()
    if not base_path.is_absolute():
        base_path = Path.cwd() / base_path
    return base_path


def ensure_reports_dir() -> Path:
    reports_dir = _reports_dir()
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def build_monthly_pdf_path(year: int, month: int) -> str:
    return f"monthly/{year}-{month:02d}-fechamento.pdf"


def build_monthly_official_pdf_path(year: int, month: int) -> str:
    return f"monthly_official/{year}-{month:02d}-relatorio-oficial.pdf"


def save_pdf_bytes(path: str, content: bytes, *, overwrite: bool = True) -> str:
    reports_dir = ensure_reports_dir()
    relative_path = Path(path)
    final_path = reports_dir / relative_path
    final_path.parent.mkdir(parents=True, exist_ok=True)

    if final_path.exists() and not overwrite:
        raise FileExistsError(f"Arquivo já existe: {final_path}")

    with tempfile.NamedTemporaryFile(dir=final_path.parent, delete=False, suffix=".tmp") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    tmp_path.replace(final_path)
    return str(relative_path.as_posix())
