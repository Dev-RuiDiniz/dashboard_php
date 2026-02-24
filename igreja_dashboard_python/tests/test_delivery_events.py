from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.core.config import settings
from app.models import (
    AuditLog,
    DeliveryEvent,
    DeliveryEventStatus,
    DeliveryInvite,
    DeliveryInviteStatus,
    DeliveryWithdrawal,
    Family,
    FoodBasket,
    FoodBasketStatus,
    VulnerabilityLevel,
)


def _login_admin(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/login",
        data={
            "email": settings.default_admin_email,
            "password": settings.default_admin_password,
        },
        follow_redirects=False,
    )
    token = response.cookies.get("access_token")
    return {"access_token": token}


def _family_payload(cpf: str, vulnerability: VulnerabilityLevel = VulnerabilityLevel.HIGH, active: bool = True) -> dict[str, str]:
    payload = {
        "responsible_name": f"Família {cpf[-3:]}",
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
        "vulnerability": vulnerability.value,
    }
    if active:
        payload["is_active"] = "on"
    payload["consent_accepted"] = "on"
    return payload


def _create_family(client: TestClient, cookies: dict[str, str], cpf: str, vulnerability: VulnerabilityLevel = VulnerabilityLevel.HIGH, active: bool = True) -> int:
    response = client.post(
        "/familias/nova",
        data=_family_payload(cpf=cpf, vulnerability=vulnerability, active=active),
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303
    with main.SessionLocal() as db:
        family = db.execute(select(Family).where(Family.responsible_cpf == cpf)).scalar_one()
        return family.id


def _create_event(client: TestClient, cookies: dict[str, str]) -> int:
    response = client.post(
        "/entregas/eventos",
        json={"title": "Entrega Março", "description": "Evento piloto", "event_date": "2026-03-20"},
        cookies=cookies,
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_event_creation(client: TestClient) -> None:
    cookies = _login_admin(client)
    response = client.post(
        "/entregas/eventos",
        json={"title": "Mutirão Abril", "description": "Ação social", "event_date": "2026-04-10"},
        cookies=cookies,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "OPEN"

    with main.SessionLocal() as db:
        event = db.get(DeliveryEvent, body["id"])
        assert event is not None
        assert event.status == DeliveryEventStatus.OPEN


def test_invite_manual(client: TestClient) -> None:
    cookies = _login_admin(client)
    family_id = _create_family(client, cookies, cpf="52998224725")
    event_id = _create_event(client, cookies)

    response = client.post(
        f"/entregas/eventos/{event_id}/convidar",
        json={"mode": "manual", "family_ids": [family_id]},
        cookies=cookies,
    )
    assert response.status_code == 200
    assert response.json()["invited"] == 1


def test_invite_auto_by_vulnerability(client: TestClient) -> None:
    cookies = _login_admin(client)
    old_family_id = _create_family(client, cookies, cpf="39053344705", vulnerability=VulnerabilityLevel.HIGH)
    _create_family(client, cookies, cpf="11144477735", vulnerability=VulnerabilityLevel.LOW)

    with main.SessionLocal() as db:
        db.add(
            FoodBasket(
                family_id=old_family_id,
                reference_year=2020,
                reference_month=1,
                status=FoodBasketStatus.DELIVERED,
            )
        )
        db.commit()

    event_id = _create_event(client, cookies)
    response = client.post(
        f"/entregas/eventos/{event_id}/convidar",
        json={"mode": "automatic", "family_ids": []},
        cookies=cookies,
    )
    assert response.status_code == 200
    assert old_family_id in response.json()["family_ids"]


def test_withdrawal_success(client: TestClient) -> None:
    cookies = _login_admin(client)
    family_id = _create_family(client, cookies, cpf="16899535009")
    event_id = _create_event(client, cookies)
    client.post(
        f"/entregas/eventos/{event_id}/convidar",
        json={"mode": "manual", "family_ids": [family_id]},
        cookies=cookies,
    )

    response = client.post(
        f"/entregas/eventos/{event_id}/retirada/{family_id}",
        json={"signature_name": "Maria", "signature_accepted": True, "notes": "Retirada ok"},
        cookies=cookies,
    )
    assert response.status_code == 200

    with main.SessionLocal() as db:
        invite = db.execute(
            select(DeliveryInvite).where(
                DeliveryInvite.event_id == event_id,
                DeliveryInvite.family_id == family_id,
            )
        ).scalar_one()
        assert invite.status == DeliveryInviteStatus.WITHDRAWN


def test_withdrawal_duplicate_block(client: TestClient) -> None:
    cookies = _login_admin(client)
    family_id = _create_family(client, cookies, cpf="28625587887")
    event_id = _create_event(client, cookies)
    client.post(
        f"/entregas/eventos/{event_id}/convidar",
        json={"mode": "manual", "family_ids": [family_id]},
        cookies=cookies,
    )

    first = client.post(
        f"/entregas/eventos/{event_id}/retirada/{family_id}",
        json={"signature_name": "Maria", "signature_accepted": True},
        cookies=cookies,
    )
    assert first.status_code == 200

    duplicate = client.post(
        f"/entregas/eventos/{event_id}/retirada/{family_id}",
        json={"signature_name": "Maria", "signature_accepted": True},
        cookies=cookies,
    )
    assert duplicate.status_code == 409


def test_invite_inactive_family_block(client: TestClient) -> None:
    cookies = _login_admin(client)
    inactive_family_id = _create_family(client, cookies, cpf="86288366757", active=False)
    event_id = _create_event(client, cookies)

    response = client.post(
        f"/entregas/eventos/{event_id}/convidar",
        json={"mode": "manual", "family_ids": [inactive_family_id]},
        cookies=cookies,
    )
    assert response.status_code == 400


def test_unique_withdrawal_code_per_event(client: TestClient) -> None:
    cookies = _login_admin(client)
    family_a = _create_family(client, cookies, cpf="15350946056")
    family_b = _create_family(client, cookies, cpf="01234567890")
    event_id = _create_event(client, cookies)

    response = client.post(
        f"/entregas/eventos/{event_id}/convidar",
        json={"mode": "manual", "family_ids": [family_a, family_b]},
        cookies=cookies,
    )
    assert response.status_code == 200

    with main.SessionLocal() as db:
        invites = db.execute(select(DeliveryInvite).where(DeliveryInvite.event_id == event_id)).scalars().all()
        codes = [invite.withdrawal_code for invite in invites]
        assert len(codes) == len(set(codes))


def test_audit_log_created_on_withdrawal(client: TestClient) -> None:
    cookies = _login_admin(client)
    family_id = _create_family(client, cookies, cpf="98765432100")
    event_id = _create_event(client, cookies)
    client.post(
        f"/entregas/eventos/{event_id}/convidar",
        json={"mode": "manual", "family_ids": [family_id]},
        cookies=cookies,
    )

    withdrawal = client.post(
        f"/entregas/eventos/{event_id}/retirada/{family_id}",
        json={"signature_name": "Maria", "signature_accepted": True},
        cookies=cookies,
    )
    assert withdrawal.status_code == 200

    with main.SessionLocal() as db:
        created = db.execute(
            select(AuditLog).where(
                AuditLog.action == "CONFIRM_WITHDRAWAL",
                AuditLog.entity == "delivery_withdrawal",
            )
        ).scalar_one_or_none()
        assert created is not None
        saved_withdrawal = db.execute(
            select(DeliveryWithdrawal).where(
                DeliveryWithdrawal.event_id == event_id,
                DeliveryWithdrawal.family_id == family_id,
            )
        ).scalar_one()
        assert created.entity_id == saved_withdrawal.id


def test_list_events_and_close_event(client: TestClient) -> None:
    cookies = _login_admin(client)
    event_id = _create_event(client, cookies)

    list_response = client.get("/entregas/eventos", cookies=cookies)
    assert list_response.status_code == 200
    ids = [item["id"] for item in list_response.json()]
    assert event_id in ids

    close_response = client.post(
        f"/entregas/eventos/{event_id}/close",
        json={"notes": "Encerramento de teste"},
        cookies=cookies,
    )
    assert close_response.status_code == 200
    assert close_response.json()["status"] == "CLOSED"


def test_timeline_family_endpoint(client: TestClient) -> None:
    cookies = _login_admin(client)
    with main.SessionLocal() as db:
        family = Family(
            responsible_name="Família Timeline",
            responsible_cpf="70460238006",
            responsible_rg="RG123",
            phone="31999990000",
            birth_date=date(1980, 1, 1),
            cep="30000000",
            street="Rua Timeline",
            number="100",
            complement=None,
            neighborhood="Centro",
            city="Belo Horizonte",
            state="MG",
            vulnerability=VulnerabilityLevel.HIGH,
            documentation_status="OK",
            consent_accepted=True,
        )
        db.add(family)
        db.commit()
        db.refresh(family)
        family_id = family.id
    with main.SessionLocal() as db:
        db.add(
            FoodBasket(
                family_id=family_id,
                reference_year=2026,
                reference_month=2,
                status=FoodBasketStatus.DELIVERED,
            )
        )
        db.commit()

    response = client.get(f"/timeline?family_id={family_id}", cookies=cookies)
    assert response.status_code == 200
    body = response.json()
    assert body["family_id"] == family_id
    assert body["total"] >= 1


def test_people_and_admin_aliases(client: TestClient) -> None:
    cookies = _login_admin(client)

    people = client.get("/pessoas", cookies=cookies, follow_redirects=False)
    assert people.status_code == 307
    assert people.headers["location"] == "/rua"

    users_alias = client.get("/admin/usuarios", cookies=cookies, follow_redirects=False)
    assert users_alias.status_code == 307
    assert users_alias.headers["location"] == "/admin/users"
