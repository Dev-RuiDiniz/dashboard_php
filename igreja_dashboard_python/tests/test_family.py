from __future__ import annotations

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from app.core.config import settings
import app.main as main
from app.models import Family, VulnerabilityLevel
from app.services.viacep_client import ViaCEPAddress, ViaCEPNotFoundError, ViaCEPUnavailableError



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


def _family_payload(**overrides: str) -> dict[str, str]:
    payload = {
        "responsible_name": "Maria da Silva",
        "responsible_cpf": "52998224725",
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
    payload.update(overrides)
    return payload


def test_family_crud_flow(client: TestClient) -> None:
    cookies = _login_admin(client)
    response = client.post(
        "/familias/nova",
        data=_family_payload(),
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        family = db.execute(select(Family)).scalar_one()
        assert family.responsible_name == "Maria da Silva"

    update_payload = _family_payload(
        responsible_name="Maria Oliveira", responsible_cpf="39053344705"
    )
    response = client.post(
        f"/familias/{family.id}/editar",
        data=update_payload,
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        updated = db.get(Family, family.id)
        assert updated.responsible_name == "Maria Oliveira"
        assert updated.responsible_cpf == "39053344705"

    response = client.post(
        f"/familias/{family.id}/inativar",
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        inactive = db.get(Family, family.id)
        assert inactive.is_active is False


def test_family_validation_duplicate_cpf(client: TestClient) -> None:
    cookies = _login_admin(client)
    response = client.post(
        "/familias/nova",
        data=_family_payload(),
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    duplicate_response = client.post(
        "/familias/nova",
        data=_family_payload(responsible_rg="SP123"),
        cookies=cookies,
        follow_redirects=False,
    )
    assert duplicate_response.status_code == 400


def test_family_validation_requires_neighborhood_and_valid_state(client: TestClient) -> None:
    cookies = _login_admin(client)
    missing_neighborhood = client.post(
        "/familias/nova",
        data=_family_payload(neighborhood=""),
        cookies=cookies,
        follow_redirects=False,
    )
    assert missing_neighborhood.status_code == 400

    invalid_state = client.post(
        "/familias/nova",
        data=_family_payload(responsible_cpf="39053344705", state="Sao Paulo"),
        cookies=cookies,
        follow_redirects=False,
    )
    assert invalid_state.status_code == 400


def test_dependent_blocked_when_family_inactive(client: TestClient) -> None:
    cookies = _login_admin(client)
    inactive_payload = _family_payload()
    inactive_payload.pop("is_active", None)
    response = client.post(
        "/familias/nova",
        data=inactive_payload,
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        family = db.execute(select(Family)).scalar_one()

    response = client.post(
        f"/familias/{family.id}/dependentes/novo",
        data={
            "name": "Carlos Silva",
            "cpf": "39053344705",
            "relationship": "Filho",
            "birth_date": "2015-02-20",
            "income": "",
            "benefits": "",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 403


def test_dependent_validation_invalid_cpf(client: TestClient) -> None:
    cookies = _login_admin(client)
    response = client.post(
        "/familias/nova",
        data=_family_payload(),
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        family = db.execute(select(Family)).scalar_one()

    response = client.post(
        f"/familias/{family.id}/dependentes/novo",
        data={
            "name": "Carlos Silva",
            "cpf": "111",
            "relationship": "Filho",
            "birth_date": "2015-02-20",
            "income": "",
            "benefits": "",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_food_basket_blocks_duplicate_same_month(client: TestClient) -> None:
    cookies = _login_admin(client)
    response = client.post(
        "/familias/nova",
        data=_family_payload(),
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        family = db.execute(select(Family)).scalar_one()

    response = client.post(
        f"/familias/{family.id}/cestas",
        data={"month_year": "01/2026", "status_value": "Entregue", "notes": "Primeira"},
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    duplicate = client.post(
        f"/familias/{family.id}/cestas",
        data={"month_year": "01/2026", "status_value": "Entregue", "notes": "Duplicada"},
        cookies=cookies,
        follow_redirects=False,
    )
    assert duplicate.status_code == 400


def test_food_basket_blocked_for_inactive_family(client: TestClient) -> None:
    cookies = _login_admin(client)
    inactive_payload = _family_payload()
    inactive_payload.pop("is_active", None)
    response = client.post(
        "/familias/nova",
        data=inactive_payload,
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        family = db.execute(select(Family)).scalar_one()

    blocked = client.post(
        f"/familias/{family.id}/cestas",
        data={"month_year": "01/2026", "status_value": "Entregue", "notes": ""},
        cookies=cookies,
        follow_redirects=False,
    )
    assert blocked.status_code == 403


def test_social_visit_request_and_execution_flow(client: TestClient) -> None:
    cookies = _login_admin(client)
    response = client.post(
        "/familias/nova",
        data=_family_payload(),
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        family = db.execute(select(Family)).scalar_one()

    request_response = client.post(
        f"/familias/{family.id}/visitas",
        data={"scheduled_date": "2026-01-10", "request_notes": "Acompanhar situação"},
        cookies=cookies,
        follow_redirects=False,
    )
    assert request_response.status_code == 303

    with main.SessionLocal() as db:
        family = db.get(Family, family.id)
        visit_request = family.visit_requests[0]

    execution_response = client.post(
        f"/familias/{family.id}/visitas/{visit_request.id}/executar",
        data={
            "executed_at": "2026-01-11",
            "result_value": "Concluída",
            "notes": "Atendimento realizado",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert execution_response.status_code == 303


def test_cep_lookup_validates_format(client: TestClient) -> None:
    cookies = _login_admin(client)
    response = client.get("/api/cep/123", cookies=cookies)
    assert response.status_code == 400
    assert response.json()["detail"] == {"code": "INVALID_CEP", "message": "CEP deve conter 8 dígitos."}


def test_cep_lookup_handles_not_found(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    cookies = _login_admin(client)
    monkeypatch.setattr(
        main,
        "fetch_address_by_cep",
        lambda _cep: (_ for _ in ()).throw(ViaCEPNotFoundError("CEP não encontrado.")),
    )

    response = client.get("/api/cep/01001000", cookies=cookies)
    assert response.status_code == 404
    assert response.json()["detail"] == {"code": "CEP_NOT_FOUND", "message": "CEP não encontrado."}




def test_cep_lookup_handles_viacep_unavailable(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    cookies = _login_admin(client)
    monkeypatch.setattr(
        main,
        "fetch_address_by_cep",
        lambda _cep: (_ for _ in ()).throw(ViaCEPUnavailableError("Consulta de CEP indisponível no momento (timeout).")),
    )

    response = client.get("/api/cep/01001000", cookies=cookies)
    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "VIACEP_UNAVAILABLE",
        "message": "Consulta de CEP indisponível no momento (timeout).",
    }

def test_cep_lookup_success(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    cookies = _login_admin(client)

    monkeypatch.setattr(
        main,
        "fetch_address_by_cep",
        lambda _cep: ViaCEPAddress(
            cep="01001000",
            street="Praça da Sé",
            neighborhood="Sé",
            city="São Paulo",
            state="SP",
            complement="lado ímpar",
        ),
    )

    response = client.get("/api/cep/01001000", cookies=cookies)
    assert response.status_code == 200
    body = response.json()
    assert body["cep"] == "01001000"
    assert body["neighborhood"] == "Sé"


def test_social_visit_request_blocked_for_inactive_family(client: TestClient) -> None:
    cookies = _login_admin(client)
    inactive_payload = _family_payload()
    inactive_payload.pop("is_active", None)
    response = client.post(
        "/familias/nova",
        data=inactive_payload,
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 303

    with main.SessionLocal() as db:
        family = db.execute(select(Family)).scalar_one()

    blocked = client.post(
        f"/familias/{family.id}/visitas",
        data={"scheduled_date": "2026-01-10", "request_notes": "Teste"},
        cookies=cookies,
        follow_redirects=False,
    )
    assert blocked.status_code == 403
