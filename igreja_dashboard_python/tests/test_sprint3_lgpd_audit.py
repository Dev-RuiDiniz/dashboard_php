from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import AuditLog, Equipment, EquipmentStatus, Family, Role, User, VulnerabilityLevel


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/login", data={"email": email, "password": password}, follow_redirects=False)
    return {"access_token": response.cookies.get("access_token")}


def _login_admin(client: TestClient) -> dict[str, str]:
    return _login(client, settings.default_admin_email, settings.default_admin_password)


def _family_payload(cpf: str = "52998224725") -> dict[str, str]:
    return {
        "responsible_name": "Maria da Silva",
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
        "vulnerability": VulnerabilityLevel.LOW.value,
        "is_active": "on",
        "consent_accepted": "on",
    }


def test_family_requires_consent(client: TestClient) -> None:
    cookies = _login_admin(client)
    payload = _family_payload()
    payload.pop("consent_accepted", None)
    response = client.post("/familias/nova", data=payload, cookies=cookies, follow_redirects=False)
    assert response.status_code == 400
    assert "consentimento" in response.text.lower()


def test_family_creation_generates_audit_log(client: TestClient) -> None:
    cookies = _login_admin(client)
    response = client.post(
        "/familias/nova",
        data=_family_payload("39053344705"),
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        log = db.execute(
            select(AuditLog).where(AuditLog.entity == "family", AuditLog.action == "CREATE")
        ).scalar_one()
        assert log.after_json is not None


def test_family_edit_generates_audit_log(client: TestClient) -> None:
    cookies = _login_admin(client)
    create_response = client.post(
        "/familias/nova",
        data=_family_payload("11144477735"),
        cookies=cookies,
        follow_redirects=False,
    )
    assert create_response.status_code == 303
    with main.SessionLocal() as db:
        family = db.execute(select(Family).where(Family.responsible_cpf == "11144477735")).scalar_one()

    response = client.post(
        f"/familias/{family.id}/editar",
        data=_family_payload("11144477735") | {"responsible_name": "Novo Nome"},
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        log = db.execute(
            select(AuditLog)
            .where(AuditLog.entity == "family", AuditLog.entity_id == family.id, AuditLog.action == "UPDATE")
            .order_by(AuditLog.id.desc())
        ).scalar_one()
        assert log.before_json is not None
        assert log.after_json is not None


def test_withdrawal_generates_audit_log(client: TestClient) -> None:
    cookies = _login_admin(client)
    family_response = client.post(
        "/familias/nova",
        data=_family_payload("16899535009"),
        cookies=cookies,
        follow_redirects=False,
    )
    assert family_response.status_code == 303

    with main.SessionLocal() as db:
        family = db.execute(select(Family).where(Family.responsible_cpf == "16899535009")).scalar_one()

    event = client.post(
        "/entregas/eventos",
        json={"title": "Evento", "description": "Teste", "event_date": "2026-04-10"},
        cookies=cookies,
    )
    event_id = event.json()["id"]
    client.post(
        f"/entregas/eventos/{event_id}/convidar",
        json={"mode": "manual", "family_ids": [family.id]},
        cookies=cookies,
    )
    response = client.post(
        f"/entregas/eventos/{event_id}/retirada/{family.id}",
        json={"signature_name": "Assinatura", "signature_accepted": True},
        cookies=cookies,
    )
    assert response.status_code == 200

    with main.SessionLocal() as db:
        log = db.execute(
            select(AuditLog).where(AuditLog.entity == "delivery_withdrawal", AuditLog.action == "CONFIRM_WITHDRAWAL")
        ).scalar_one()
        assert log.after_json is not None


def test_equipment_loan_generates_audit_log(client: TestClient) -> None:
    cookies = _login_admin(client)
    family_response = client.post(
        "/familias/nova",
        data=_family_payload("28625587887"),
        cookies=cookies,
        follow_redirects=False,
    )
    assert family_response.status_code == 303

    with main.SessionLocal() as db:
        family = db.execute(select(Family).where(Family.responsible_cpf == "28625587887")).scalar_one()
        equipment = Equipment(code="BEN-90", description="Cadeira", status=EquipmentStatus.AVAILABLE)
        db.add(equipment)
        db.commit()

    response = client.post(
        f"/equipamentos/{equipment.id}/emprestimo",
        data={"family_id": family.id, "loan_date": "2026-02-10", "due_date": "", "notes": ""},
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        log = db.execute(
            select(AuditLog).where(AuditLog.entity == "equipment_loan", AuditLog.action == "LOAN")
        ).scalar_one()
        assert log.after_json is not None


def test_audit_query_admin_only(client: TestClient) -> None:
    with main.SessionLocal() as db:
        role = db.execute(select(Role).where(Role.name == "Leitura")).scalar_one()
        db.add(
            User(
                name="Leitor",
                email="leitor.audit@example.com",
                hashed_password=get_password_hash("Senha123"),
                is_active=True,
                roles=[role],
            )
        )
        db.commit()

    user_cookies = _login(client, "leitor.audit@example.com", "Senha123")
    denied = client.get("/admin/audit", cookies=user_cookies)
    assert denied.status_code == 403

    admin = _login_admin(client)
    allowed = client.get("/admin/audit", cookies=admin)
    assert allowed.status_code == 200
