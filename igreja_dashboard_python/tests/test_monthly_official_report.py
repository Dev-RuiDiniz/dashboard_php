from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import MonthlyClosure, Role, User


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


def _close_month(client: TestClient, cookies: dict[str, str], month: int = 3, year: int = 2026):
    return client.post(
        "/admin/fechamento/close",
        data={"month": str(month), "year": str(year)},
        cookies=cookies,
        follow_redirects=False,
    )


def _generate_official(client: TestClient, cookies: dict[str, str], month: int = 3, year: int = 2026):
    return client.post(
        f"/admin/fechamento/{year}/{month}/gerar-relatorio-oficial",
        cookies=cookies,
        follow_redirects=False,
    )


def test_official_report_requires_closed_month(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    cookies = _login_admin(client)

    response = _generate_official(client, cookies)

    assert response.status_code == 409
    assert "CLOSED" in response.text


def test_official_report_generates_pdf_and_hash(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    cookies = _login_admin(client)
    assert _close_month(client, cookies).status_code == 303

    generated = _generate_official(client, cookies)
    assert generated.status_code == 303

    with main.SessionLocal() as db:
        closure = db.execute(select(MonthlyClosure).where(MonthlyClosure.month == 3, MonthlyClosure.year == 2026)).scalar_one()
        assert closure.official_pdf_path
        assert closure.official_pdf_sha256
        assert len(closure.official_pdf_sha256) == 64
        int(closure.official_pdf_sha256, 16)
        assert (Path(settings.reports_dir) / closure.official_pdf_path).exists()

    download = client.get("/admin/fechamento/2026/3/relatorio-oficial.pdf", cookies=cookies)
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/pdf")


def test_official_report_is_immutable_by_default(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    settings.admin_override = False
    cookies = _login_admin(client)
    assert _close_month(client, cookies).status_code == 303
    assert _generate_official(client, cookies).status_code == 303

    second = _generate_official(client, cookies)
    assert second.status_code == 409
    assert "imutável" in second.text


def test_official_report_includes_previous_month_comparison_when_available(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    cookies = _login_admin(client)

    assert _close_month(client, cookies, month=2, year=2026).status_code == 303
    assert _generate_official(client, cookies, month=2, year=2026).status_code == 303
    assert _close_month(client, cookies, month=3, year=2026).status_code == 303

    generated = _generate_official(client, cookies, month=3, year=2026)
    assert generated.status_code == 303

    snapshot = client.get("/admin/fechamento/2026/3/relatorio-oficial.snapshot.json", cookies=cookies)
    assert snapshot.status_code == 200
    payload = snapshot.json()
    assert "mom" in payload
    for key in [
        "families_attended",
        "people_followed",
        "children_count",
        "deliveries_count",
        "referrals_count",
        "visits_count",
        "loans_count",
        "pending_docs_count",
        "pending_visits_count",
    ]:
        assert key in payload["mom"]

    pdf = client.get("/admin/fechamento/2026/3/relatorio-oficial.pdf", cookies=cookies)
    assert pdf.status_code == 200
    assert len(pdf.content) > 0
    assert b"Evolucao" in pdf.content or b"Evolu" in pdf.content


def test_hash_matches_pdf_bytes(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    cookies = _login_admin(client)
    assert _close_month(client, cookies).status_code == 303
    assert _generate_official(client, cookies).status_code == 303

    with main.SessionLocal() as db:
        closure = db.execute(select(MonthlyClosure).where(MonthlyClosure.month == 3, MonthlyClosure.year == 2026)).scalar_one()
        expected_hash = closure.official_pdf_sha256

    pdf = client.get("/admin/fechamento/2026/3/relatorio-oficial.pdf", cookies=cookies)
    assert pdf.status_code == 200
    local_hash = hashlib.sha256(pdf.content).hexdigest()
    assert local_hash == expected_hash
    assert pdf.headers["x-content-sha256"] == expected_hash


def test_only_admin_can_generate_official_report(client: TestClient, tmp_path: Path) -> None:
    settings.reports_dir = str(tmp_path / "reports")
    admin_cookies = _login_admin(client)

    with main.AuthSessionLocal() as db:
        leitura_role = db.execute(select(Role).where(Role.name == "Leitura")).scalar_one()
        user = User(
            name="Leitor",
            email="leitor2@example.com",
            hashed_password=get_password_hash("senha1234"),
            roles=[leitura_role],
        )
        db.add(user)
        db.commit()

    user_cookies = _login(client, "leitor2@example.com", "senha1234")

    assert _close_month(client, admin_cookies).status_code == 303
    denied = _generate_official(client, user_cookies)
    assert denied.status_code == 403
