from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
import app.main as main
from app.models import Child, DeliveryEvent, Family


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


def _family_payload(cpf: str) -> dict[str, str]:
    return {
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
        "vulnerability": "Alta",
        "is_active": "on",
        "consent_accepted": "on",
    }


def _create_family(client: TestClient, cookies: dict[str, str], cpf: str) -> int:
    response = client.post(
        "/familias/nova", data=_family_payload(cpf), cookies=cookies, follow_redirects=False
    )
    assert response.status_code == 303
    with main.SessionLocal() as db:
        family = db.execute(select(Family).where(Family.responsible_cpf == cpf)).scalar_one()
        return family.id


def _create_event(
    client: TestClient, cookies: dict[str, str], has_children_list: bool = True
) -> int:
    response = client.post(
        "/entregas/eventos",
        json={
            "title": "Entrega Crianças",
            "description": "Evento infantil",
            "event_date": "2026-03-20",
            "has_children_list": has_children_list,
        },
        cookies=cookies,
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_child_requires_family(client: TestClient) -> None:
    cookies = _login_admin(client)
    response = client.post(
        "/criancas",
        data={"name": "Ana", "birth_date": "2018-01-10", "sex": "F"},
        cookies=cookies,
    )
    assert response.status_code == 422


def test_child_crud_happy_path(client: TestClient) -> None:
    cookies = _login_admin(client)
    family_id = _create_family(client, cookies, cpf="52998224725")

    create_response = client.post(
        "/criancas",
        data={
            "family_id": str(family_id),
            "name": "Ana Clara",
            "birth_date": "2018-01-10",
            "sex": "F",
            "notes": "Teste",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert create_response.status_code == 303
    child_url = create_response.headers["location"]

    child_detail = client.get(child_url, cookies=cookies)
    assert child_detail.status_code == 200
    assert "Ana Clara" in child_detail.text

    with main.SessionLocal() as db:
        child = db.execute(select(Child).where(Child.name == "Ana Clara")).scalar_one()
        child_id = child.id

    update_response = client.post(
        f"/criancas/{child_id}",
        data={
            "family_id": str(family_id),
            "name": "Ana Clara Silva",
            "birth_date": "2018-01-10",
            "sex": "F",
            "notes": "Atualizado",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert update_response.status_code == 303

    list_response = client.get(f"/criancas?family_id={family_id}", cookies=cookies)
    assert list_response.status_code == 200
    assert "Ana Clara Silva" in list_response.text

    delete_response = client.post(
        f"/criancas/{child_id}/delete", cookies=cookies, follow_redirects=False
    )
    assert delete_response.status_code == 303

    with main.SessionLocal() as db:
        deleted = db.get(Child, child_id)
        assert deleted is None


def test_event_children_list_only_confirmed_families(client: TestClient) -> None:
    cookies = _login_admin(client)
    family_confirmed = _create_family(client, cookies, cpf="39053344705")
    family_not_confirmed = _create_family(client, cookies, cpf="11144477735")
    event_id = _create_event(client, cookies, has_children_list=True)

    invite_response = client.post(
        f"/entregas/eventos/{event_id}/convidar",
        json={"mode": "manual", "family_ids": [family_confirmed, family_not_confirmed]},
        cookies=cookies,
    )
    assert invite_response.status_code == 200

    confirm_response = client.post(
        f"/entregas/eventos/{event_id}/retirada/{family_confirmed}",
        json={"signature_name": "Maria", "signature_accepted": True},
        cookies=cookies,
    )
    assert confirm_response.status_code == 200

    child_a = client.post(
        "/criancas",
        data={
            "family_id": str(family_confirmed),
            "name": "Criança Confirmada",
            "birth_date": "2017-06-01",
            "sex": "M",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert child_a.status_code == 303

    child_b = client.post(
        "/criancas",
        data={
            "family_id": str(family_not_confirmed),
            "name": "Criança Não Confirmada",
            "birth_date": "2016-05-01",
            "sex": "F",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert child_b.status_code == 303

    response = client.get(f"/entregas/eventos/{event_id}/criancas", cookies=cookies)
    assert response.status_code == 200
    assert "Criança Confirmada" in response.text
    assert "Criança Não Confirmada" not in response.text


def test_children_export_xlsx(client: TestClient) -> None:
    cookies = _login_admin(client)
    family_id = _create_family(client, cookies, cpf="16899535009")
    event_id = _create_event(client, cookies, has_children_list=True)

    client.post(
        f"/entregas/eventos/{event_id}/convidar",
        json={"mode": "manual", "family_ids": [family_id]},
        cookies=cookies,
    )
    client.post(
        f"/entregas/eventos/{event_id}/retirada/{family_id}",
        json={"signature_name": "Maria", "signature_accepted": True},
        cookies=cookies,
    )
    client.post(
        "/criancas",
        data={
            "family_id": str(family_id),
            "name": "Exportável",
            "birth_date": "2015-09-10",
            "sex": "O",
        },
        cookies=cookies,
        follow_redirects=False,
    )

    response = client.get(f"/entregas/eventos/{event_id}/criancas/export.xlsx", cookies=cookies)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    with ZipFile(BytesIO(response.content)) as xlsx:
        sheet_xml = xlsx.read("xl/worksheets/sheet1.xml").decode("utf-8")

    assert "Nome criança" in sheet_xml
    assert "Idade" in sheet_xml
    assert "Família" in sheet_xml


def test_children_export_pdf(client: TestClient) -> None:
    cookies = _login_admin(client)
    event_id = _create_event(client, cookies, has_children_list=True)

    response = client.get(f"/entregas/eventos/{event_id}/criancas/export.pdf", cookies=cookies)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert len(response.content) > 0

    with main.SessionLocal() as db:
        event = db.get(DeliveryEvent, event_id)
        assert event is not None
        assert event.has_children_list is True
