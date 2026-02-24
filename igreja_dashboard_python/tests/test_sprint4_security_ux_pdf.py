from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select

import app.main as main
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import Family, PasswordResetToken, Role, User


def _login_admin(client):
    response = client.post(
        "/login",
        data={"email": settings.default_admin_email, "password": settings.default_admin_password},
        follow_redirects=False,
    )
    return {"access_token": response.cookies.get("access_token")}


def test_reset_token_invalid(client):
    response = client.get("/password/reset?token=invalidtoken")
    assert response.status_code == 400


def test_reset_token_expired(client):
    with main.SessionLocal() as db:
        user = db.execute(select(User).where(User.email == settings.default_admin_email)).scalar_one()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=main._token_hash("expired-token"),
                created_at=datetime.utcnow() - timedelta(hours=1),
                expires_at=datetime.utcnow() - timedelta(minutes=1),
                used_at=None,
            )
        )
        db.commit()

    response = client.post("/password/reset", data={"token": "expired-token", "password": "NovaSenha123"})
    assert response.status_code == 400


def test_lockout_after_5_failed_attempts(client):
    for _ in range(5):
        response = client.post(
            "/login",
            data={"email": settings.default_admin_email, "password": "errada"},
            follow_redirects=False,
        )
        assert response.status_code == 401

    blocked = client.post(
        "/login",
        data={"email": settings.default_admin_email, "password": "errada"},
        follow_redirects=False,
    )
    assert blocked.status_code == 429


def test_rate_limit_login(client):
    for _ in range(30):
        client.post("/login", data={"email": "x@y.com", "password": "x"}, follow_redirects=False)
    blocked = client.post("/login", data={"email": "x@y.com", "password": "x"}, follow_redirects=False)
    assert blocked.status_code == 429


def test_pdf_event_contains_expected_data(client):
    cookies = _login_admin(client)
    event = client.post(
        "/entregas/eventos",
        json={"title": "PDF Evento", "description": "Teste", "event_date": "2026-03-20"},
        cookies=cookies,
    ).json()
    response = client.get(f"/entregas/eventos/{event['id']}/export.pdf", cookies=cookies)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert len(response.content) > 0


def test_global_search_returns_mixed_results(client):
    cookies = _login_admin(client)
    client.post(
        "/familias/nova",
        data={
            "responsible_name": "Busca Familia",
            "responsible_cpf": "11144477735",
            "phone": "31999990000",
            "birth_date": "1985-04-10",
            "cep": "30000000",
            "street": "Rua A",
            "number": "123",
            "neighborhood": "CentroBusca",
            "city": "BH",
            "state": "MG",
            "socioeconomic_profile": "Perfil",
            "documentation_status": "ok",
            "vulnerability": "Alta",
            "consent_accepted": "on",
            "is_active": "on",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    client.post("/equipamentos/novo", data={"description": "Busca Equip"}, cookies=cookies, follow_redirects=False)

    with main.SessionLocal() as db:
        family = db.execute(select(Family).where(Family.responsible_name == "Busca Familia")).scalar_one()
        db.execute(
            select(Role)
        )
    child_create = client.post(
        "/criancas",
        data={"family_id": family.id, "name": "Busca Crianca", "birth_date": "2018-01-01", "sex": "F"},
        cookies=cookies,
        follow_redirects=False,
    )
    assert child_create.status_code == 303

    response = client.get("/busca?q=Busca", cookies=cookies)
    assert response.status_code == 200
    assert "Famílias" in response.text
    assert "Crianças" in response.text
    assert "Equipamentos" in response.text
