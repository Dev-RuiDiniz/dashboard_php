from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import MonthlyClosure, MonthlyClosureStatus, Role, SystemSettings, User


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/login", data={"email": email, "password": password}, follow_redirects=False)
    return {"access_token": response.cookies.get("access_token")}


def _login_admin(client: TestClient) -> dict[str, str]:
    return _login(client, settings.default_admin_email, settings.default_admin_password)


def _create_closure(
    *,
    month: int,
    year: int,
    status: MonthlyClosureStatus = MonthlyClosureStatus.CLOSED,
    summary: dict | None = None,
    official: dict | None = None,
    official_pdf_path: str | None = None,
):
    with main.SessionLocal() as db:
        db.add(
            MonthlyClosure(
                month=month,
                year=year,
                status=status,
                summary_snapshot_json=summary,
                official_snapshot_json=official,
                official_pdf_path=official_pdf_path,
                official_pdf_sha256="a" * 64 if official_pdf_path else None,
            )
        )
        db.commit()


def test_history_list_renders_rows(client: TestClient) -> None:
    _create_closure(
        month=1,
        year=2026,
        summary={"totals": {"families_attended": 7, "deliveries_count": 5, "children_count": 4, "referrals_count": 2}},
    )
    _create_closure(
        month=2,
        year=2026,
        summary={"totals": {"families_attended": 9, "deliveries_count": 8, "children_count": 3, "referrals_count": 1}},
    )

    response = client.get("/historico", cookies=_login_admin(client))

    assert response.status_code == 200
    html = response.text
    assert "2026-01" in html
    assert "2026-02" in html
    assert "Famílias" in html


def test_history_detail_uses_official_snapshot_when_available(client: TestClient) -> None:
    _create_closure(
        month=3,
        year=2026,
        summary={"totals": {"families_attended": 10, "deliveries_count": 10, "children_count": 10, "referrals_count": 10}},
        official={"totals": {"families_attended": 2, "deliveries_count": 3, "children_count": 4, "referrals_count": 5}},
        official_pdf_path="official/2026-03.pdf",
    )

    response = client.get("/historico/2026/3", cookies=_login_admin(client))

    assert response.status_code == 200
    html = response.text
    assert "Histórico mensal — 2026-03" in html
    assert ">2<" in html
    assert ">3<" in html
    assert ">4<" in html
    assert ">5<" in html


def test_series_api_returns_ordered_labels(client: TestClient) -> None:
    _create_closure(
        month=1,
        year=2026,
        summary={"totals": {"families_attended": 1, "deliveries_count": 1, "children_count": 1, "referrals_count": 1}},
    )
    _create_closure(
        month=2,
        year=2026,
        summary={"totals": {"families_attended": 2, "deliveries_count": 2, "children_count": 2, "referrals_count": 2}},
    )

    response = client.get("/api/historico/series?from=2026-01&to=2026-02", cookies=_login_admin(client))

    assert response.status_code == 200
    payload = response.json()
    assert payload["labels"] == ["2026-01", "2026-02"]
    assert len(payload["labels"]) == len(payload["families_attended"]) == len(payload["deliveries_count"]) == len(payload["children_count"])


def test_closed_month_snapshots_do_not_change_after_settings_update(client: TestClient) -> None:
    snapshot = {"totals": {"families_attended": 12, "deliveries_count": 11, "children_count": 10, "referrals_count": 9}}
    _create_closure(month=4, year=2026, summary=snapshot, official=snapshot, official_pdf_path="official/2026-04.pdf")

    with main.SessionLocal() as db:
        settings_row = db.execute(select(SystemSettings).limit(1)).scalar_one_or_none()
        if settings_row is None:
            settings_row = SystemSettings(eligibility_rules={"min_interval_days": 30})
            db.add(settings_row)
        settings_row.eligibility_rules = {"min_interval_days": 999, "vulnerability_weights": {"Alta": 5}}
        db.commit()

    response = client.get("/historico/2026/4", cookies=_login_admin(client))

    assert response.status_code == 200
    html = response.text
    assert ">12<" in html
    assert ">11<" in html
    assert ">10<" in html
    assert ">9<" in html


def test_non_admin_cannot_access_snapshot_json(client: TestClient) -> None:
    _create_closure(
        month=5,
        year=2026,
        summary={"totals": {"families_attended": 1, "deliveries_count": 1, "children_count": 1, "referrals_count": 1}},
    )

    with main.AuthSessionLocal() as db:
        leitura_role = db.execute(select(Role).where(Role.name == "Leitura")).scalar_one()
        db.add(
            User(
                name="Leitor Histórico",
                email="historico.leitor@example.com",
                hashed_password=get_password_hash("senha1234"),
                roles=[leitura_role],
            )
        )
        db.commit()

    leitura_cookies = _login(client, "historico.leitor@example.com", "senha1234")
    denied = client.get("/historico/2026/5/snapshot.json", cookies=leitura_cookies)

    assert denied.status_code == 403
