from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

import app.main as main
from app.core.config import settings
from app.models import (
    Child,
    ChildSex,
    DeliveryEvent,
    DeliveryInvite,
    DeliveryInviteStatus,
    Family,
    Referral,
    ReferralStatus,
    StreetPerson,
    VulnerabilityLevel,
)
from app.pdf import generate_report_pdf


def _login_admin(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/login",
        data={"email": settings.default_admin_email, "password": settings.default_admin_password},
        follow_redirects=False,
    )
    return {"access_token": response.cookies.get("access_token")}


def _seed_pdf_entities() -> tuple[int, int, int]:
    with main.SessionLocal() as db:
        family = Family(
            responsible_name="Família PDF Sprint",
            responsible_cpf="52998224725",
            phone="11988887777",
            birth_date=date(1982, 6, 10),
            neighborhood="Centro",
            vulnerability=VulnerabilityLevel.HIGH,
            is_active=True,
        )
        db.add(family)
        db.flush()

        child = Child(
            family_id=family.id,
            name="Criança PDF",
            birth_date=date(2017, 3, 15),
            sex=ChildSex.F,
        )
        db.add(child)

        person = StreetPerson(
            full_name="Pessoa PDF",
            reference_location="Praça Central",
            is_active=True,
            consent_accepted=False,
        )
        db.add(person)
        db.flush()

        db.add(
            Referral(
                person_id=person.id,
                recovery_home="Casa Esperança",
                referral_date=date.today(),
                status=ReferralStatus.REFERRED,
            )
        )

        event = DeliveryEvent(
            title="Evento PDF Sprint",
            event_date=date.today(),
            has_children_list=True,
            created_by_user_id=1,
        )
        db.add(event)
        db.flush()

        db.add(
            DeliveryInvite(
                event_id=event.id,
                family_id=family.id,
                withdrawal_code="ABC123",
                status=DeliveryInviteStatus.WITHDRAWN,
            )
        )

        db.commit()
        return family.id, person.id, event.id


def test_all_report_endpoints_return_pdf(client: TestClient) -> None:
    family_id, person_id, event_id = _seed_pdf_entities()
    cookies = _login_admin(client)

    endpoints = [
        "/relatorios/familias.pdf",
        "/relatorios/cestas.pdf",
        "/relatorios/criancas.pdf",
        "/relatorios/encaminhamentos.pdf",
        "/relatorios/equipamentos.pdf",
        "/relatorios/pendencias.pdf",
        f"/entregas/eventos/{event_id}/export.pdf",
        f"/entregas/eventos/{event_id}/criancas/export.pdf",
        f"/familias/{family_id}/export.pdf",
        f"/pessoas/{person_id}/export.pdf",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint, cookies=cookies)
        assert response.status_code == 200, endpoint
        assert response.headers["content-type"].startswith("application/pdf"), endpoint
        assert len(response.content) > 0, endpoint


def test_pdf_contains_title() -> None:
    pdf_content = generate_report_pdf(
        title="Título de Teste PDF",
        month=1,
        year=2026,
        sections=[{"type": "text", "title": "Resumo", "content": "Conteúdo"}],
        metadata={
            "generated_by": "Teste",
            "generated_at": "01/01/2026 10:00",
            "institution": "Primeira Igreja Batista de Taubaté",
        },
    )
    decoded = pdf_content.decode("latin-1", errors="ignore")
    assert "Título de Teste PDF" in decoded


def test_pdf_generation_not_break_existing_csv(client: TestClient) -> None:
    _seed_pdf_entities()
    cookies = _login_admin(client)

    csv_response = client.get("/relatorios/export.csv?report_type=familias", cookies=cookies)
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")

    xlsx_response = client.get("/relatorios/export.xlsx?report_type=familias", cookies=cookies)
    assert xlsx_response.status_code == 200
    assert (
        xlsx_response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_pdf_respects_user_metadata(client: TestClient) -> None:
    _seed_pdf_entities()
    cookies = _login_admin(client)

    response = client.get("/relatorios/familias.pdf", cookies=cookies)
    assert response.status_code == 200

    decoded = response.content.decode("latin-1", errors="ignore")
    assert "Gerado por: Administrador" in decoded
