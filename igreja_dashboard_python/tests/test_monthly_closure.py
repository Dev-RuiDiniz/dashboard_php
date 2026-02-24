from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import (
    MonthlyClosure,
    MonthlyClosureStatus,
    Role,
    SystemSettings,
    User,
)


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    token = response.cookies.get("access_token")
    return {"access_token": token}


def _login_admin(client: TestClient) -> dict[str, str]:
    return _login(client, settings.default_admin_email, settings.default_admin_password)


def _create_family(client: TestClient, cookies: dict[str, str], cpf: str = "52998224725") -> int:
    payload = {
        "responsible_name": "Família Fechamento",
        "responsible_cpf": cpf,
        "responsible_rg": "MG123",
        "phone": "31999990000",
        "birth_date": "1985-04-10",
        "cep": "30000000",
        "street": "Rua A",
        "number": "123",
        "complement": "Apto 1",
        "neighborhood": "Centro",
        "city": "Belo Horizonte",
        "state": "MG",
        "latitude": "-19.90",
        "longitude": "-43.94",
        "socioeconomic_profile": "Perfil",
        "documentation_status": "Documentação ok",
        "vulnerability": "Alta",
        "is_active": "on",
        "consent_accepted": "on",
    }
    response = client.post("/familias/nova", data=payload, cookies=cookies, follow_redirects=False)
    assert response.status_code == 303
    with main.SessionLocal() as db:
        return db.execute(select(main.Family).where(main.Family.responsible_cpf == cpf)).scalar_one().id


def _create_event_and_invite(client: TestClient, cookies: dict[str, str], family_id: int) -> int:
    event = client.post(
        "/entregas/eventos",
        json={"title": "Entrega Março", "description": "Evento", "event_date": "2026-03-20"},
        cookies=cookies,
    )
    assert event.status_code == 200
    event_id = event.json()["id"]
    invited = client.post(
        f"/entregas/eventos/{event_id}/convidar",
        json={"mode": "manual", "family_ids": [family_id]},
        cookies=cookies,
    )
    assert invited.status_code == 200
    return event_id


def _close_month(client: TestClient, cookies: dict[str, str], month: int = 3, year: int = 2026):
    return client.post(
        "/admin/fechamento/close",
        data={"month": str(month), "year": str(year)},
        cookies=cookies,
        follow_redirects=False,
    )


def test_close_month_creates_row_snapshot_and_pdf_path(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    cookies = _login_admin(client)

    response = _close_month(client, cookies)
    assert response.status_code == 303

    with main.SessionLocal() as db:
        closure = db.execute(select(MonthlyClosure).where(MonthlyClosure.month == 3, MonthlyClosure.year == 2026)).scalar_one()
        assert closure.status == MonthlyClosureStatus.CLOSED
        assert closure.summary_snapshot_json is not None
        assert closure.pdf_report_path
        assert (Path(settings.reports_dir) / closure.pdf_report_path).exists()


def test_close_month_is_idempotent_or_blocked(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    cookies = _login_admin(client)
    first = _close_month(client, cookies)
    assert first.status_code == 303

    second = _close_month(client, cookies)
    assert second.status_code == 409
    assert "já está fechado" in second.text


def test_month_lock_blocks_withdrawal_edit(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    cookies = _login_admin(client)
    family_id = _create_family(client, cookies)
    event_id = _create_event_and_invite(client, cookies, family_id)
    _close_month(client, cookies)

    blocked = client.post(
        f"/entregas/eventos/{event_id}/retirada/{family_id}",
        json={"signature_name": "Maria", "signature_accepted": True},
        cookies=cookies,
    )
    assert blocked.status_code == 409
    assert "Mês fechado" in blocked.text


def test_month_lock_allows_read_and_pdf_download(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    cookies = _login_admin(client)
    _close_month(client, cookies)

    page = client.get("/admin/fechamento?month=3&year=2026", cookies=cookies)
    assert page.status_code == 200

    pdf = client.get("/admin/fechamento/2026/3/pdf", cookies=cookies)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")


def test_only_admin_can_close_month(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    admin_cookies = _login_admin(client)

    with main.AuthSessionLocal() as db:
        leitura_role = db.execute(select(Role).where(Role.name == "Leitura")).scalar_one()
        user = User(
            name="Leitor",
            email="leitor@example.com",
            hashed_password=get_password_hash("senha1234"),
            roles=[leitura_role],
        )
        db.add(user)
        db.commit()

    user_cookies = _login(client, "leitor@example.com", "senha1234")

    page = client.get("/admin/fechamento", cookies=user_cookies)
    assert page.status_code == 403

    close = _close_month(client, user_cookies)
    assert close.status_code == 403

    # sanity
    assert _close_month(client, admin_cookies).status_code == 303


def test_snapshot_is_stable(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    cookies = _login_admin(client)
    _close_month(client, cookies)

    with main.SessionLocal() as db:
        closure = db.execute(select(MonthlyClosure).where(MonthlyClosure.month == 3, MonthlyClosure.year == 2026)).scalar_one()
        original_snapshot = closure.summary_snapshot_json

        cfg = db.get(SystemSettings, 1)
        cfg.delivery_month_limit = 99
        db.commit()

        same_closure = db.execute(select(MonthlyClosure).where(MonthlyClosure.id == closure.id)).scalar_one()
        assert same_closure.summary_snapshot_json == original_snapshot
