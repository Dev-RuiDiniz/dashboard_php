from __future__ import annotations

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from app.core.security import get_password_hash
import app.main as main
from app.models import Referral, ReferralStatus, Role, StreetPerson, StreetService, User



def _create_user_with_role(role_name: str, email: str) -> None:
    with main.SessionLocal() as db:
        role = db.execute(select(Role).where(Role.name == role_name)).scalar_one()
        db.add(
            User(
                name=f"Usuário {role_name}",
                email=email,
                hashed_password=get_password_hash("Senha123"),
                is_active=True,
                roles=[role],
            )
        )
        db.commit()


def _login(client: TestClient, email: str, password: str = "Senha123") -> dict[str, str]:
    response = client.post(
        "/login", data={"email": email, "password": password}, follow_redirects=False
    )
    return {"access_token": response.cookies.get("access_token")}


def test_street_person_workflow_and_reports(client: TestClient) -> None:
    _create_user_with_role("Operador", "operador.street@example.com")
    cookies = _login(client, "operador.street@example.com")

    create_response = client.post(
        "/rua/nova",
        data={
            "full_name": "Carlos Souza",
            "cpf": "39053344705",
            "reference_location": "Praça Sete",
            "benefit_notes": "Auxílio emergencial",
            "consent_accepted": "on",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert create_response.status_code == 303
    detail_path = create_response.headers["location"]

    service_response = client.post(
        f"{detail_path}/atendimentos",
        data={
            "service_type": "Banho",
            "service_date": "2026-01-10",
            "responsible_name": "Equipe A",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert service_response.status_code == 303

    referral_response = client.post(
        f"{detail_path}/encaminhamentos",
        data={
            "recovery_home": "Casa Esperança",
            "referral_date": "2026-01-12",
            "status_value": ReferralStatus.FOLLOW_UP.value,
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert referral_response.status_code == 303

    detail_response = client.get(detail_path, cookies=cookies)
    assert detail_response.status_code == 200
    assert "Histórico de atendimentos" in detail_response.text
    assert "Casa Esperança" in detail_response.text

    report_response = client.get("/relatorios?report_type=rua", cookies=cookies)
    assert report_response.status_code == 200
    assert "Pessoas em situação de rua" in report_response.text

    with main.SessionLocal() as db:
        assert db.execute(select(StreetPerson)).scalars().all()
        assert db.execute(select(StreetService)).scalars().all()
        assert db.execute(select(Referral)).scalars().all()
