from __future__ import annotations

from datetime import date, timedelta
from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
import app.main as main
from app.models import (
    Equipment,
    EquipmentStatus,
    Family,
    FoodBasket,
    FoodBasketStatus,
    Loan,
    LoanStatus,
    VisitRequest,
    VisitRequestStatus,
    VulnerabilityLevel,
)



def _login_admin(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/login",
        data={"email": settings.default_admin_email, "password": settings.default_admin_password},
        follow_redirects=False,
    )
    return {"access_token": response.cookies.get("access_token")}


def _seed_minimal_data() -> None:
    with main.SessionLocal() as db:
        family = Family(
            responsible_name="Família KPI",
            responsible_cpf="39053344705",
            responsible_rg="123456789",
            phone="31999999999",
            birth_date=date(1980, 1, 1),
            vulnerability=VulnerabilityLevel.HIGH,
            is_active=True,
        )
        db.add(family)
        db.flush()

        db.add(
            FoodBasket(
                family_id=family.id,
                reference_year=date.today().year,
                reference_month=max(1, date.today().month - 4),
                status=FoodBasketStatus.DELIVERED,
            )
        )
        db.add(
            FoodBasket(
                family_id=family.id,
                reference_year=date.today().year,
                reference_month=date.today().month,
                status=FoodBasketStatus.DELIVERED,
            )
        )

        equipment = Equipment(
            code="BEN-99", description="Cadeira de rodas", status=EquipmentStatus.LOANED
        )
        db.add(equipment)
        db.flush()

        db.add(
            VisitRequest(
                family_id=family.id,
                requested_by_user_id=1,
                scheduled_date=date.today() - timedelta(days=1),
                status=VisitRequestStatus.PENDING,
                request_notes="Visita pendente",
            )
        )

        db.add(
            Loan(
                equipment_id=equipment.id,
                family_id=family.id,
                loan_date=date.today() - timedelta(days=10),
                due_date=date.today() - timedelta(days=2),
                status=LoanStatus.ACTIVE,
            )
        )
        db.commit()


def test_dashboard_and_reports_pages(client: TestClient) -> None:
    _seed_minimal_data()
    cookies = _login_admin(client)

    dashboard_response = client.get("/dashboard", cookies=cookies)
    assert dashboard_response.status_code == 200
    assert "Dashboard Gerencial" in dashboard_response.text
    assert "Visitas sociais" in dashboard_response.text
    assert "Famílias atendidas no mês atual" in dashboard_response.text
    assert "Equipamentos emprestados, atrasados e em manutenção" in dashboard_response.text

    reports_response = client.get("/relatorios?report_type=visitas", cookies=cookies)
    assert reports_response.status_code == 200
    assert "Relatórios" in reports_response.text

    heatmap_response = client.get("/dashboard/mapa-calor-bairros", cookies=cookies)
    assert heatmap_response.status_code == 200
    assert "Mapa de calor por bairro" in heatmap_response.text


def test_reports_exports(client: TestClient) -> None:
    _seed_minimal_data()
    cookies = _login_admin(client)

    csv_response = client.get("/relatorios/export.csv?report_type=familias", cookies=cookies)
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    assert "Responsável" in csv_response.text

    xlsx_response = client.get("/relatorios/export.xlsx?report_type=familias", cookies=cookies)
    assert xlsx_response.status_code == 200
    assert (
        xlsx_response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert len(xlsx_response.content) > 100


def test_reports_accepts_empty_year_and_month_filters(client: TestClient) -> None:
    _seed_minimal_data()
    cookies = _login_admin(client)

    reports_response = client.get(
        "/relatorios?report_type=familias&year=&month=", cookies=cookies
    )
    assert reports_response.status_code == 200
    assert "Relatórios" in reports_response.text

    equipment_response = client.get(
        "/relatorios?report_type=equipamentos&year=&month=", cookies=cookies
    )
    assert equipment_response.status_code == 200

    csv_response = client.get(
        "/relatorios/export.csv?report_type=familias&year=&month=", cookies=cookies
    )
    assert csv_response.status_code == 200

    xlsx_response = client.get(
        "/relatorios/export.xlsx?report_type=familias&year=&month=", cookies=cookies
    )
    assert xlsx_response.status_code == 200


def test_neighborhood_report_groups_only_active_families(client: TestClient) -> None:
    with main.SessionLocal() as db:
        db.add_all(
            [
                Family(
                    responsible_name="Família Centro 1",
                    responsible_cpf="52998224725",
                    phone="11111111111",
                    birth_date=date(1988, 1, 1),
                    neighborhood=" centro ",
                    city="Taubaté",
                    state="SP",
                    vulnerability=VulnerabilityLevel.HIGH,
                    is_active=True,
                ),
                Family(
                    responsible_name="Família Centro 2",
                    responsible_cpf="39053344705",
                    phone="22222222222",
                    birth_date=date(1989, 1, 1),
                    neighborhood="CENTRO",
                    city="Taubaté",
                    state="SP",
                    vulnerability=VulnerabilityLevel.LOW,
                    is_active=True,
                ),
                Family(
                    responsible_name="Família Inativa",
                    responsible_cpf="11144477735",
                    phone="33333333333",
                    birth_date=date(1990, 1, 1),
                    neighborhood="Centro",
                    city="Taubaté",
                    state="SP",
                    vulnerability=VulnerabilityLevel.EXTREME,
                    is_active=False,
                ),
            ]
        )
        db.commit()

    cookies = _login_admin(client)
    response = client.get("/relatorios?report_type=bairros", cookies=cookies)
    assert response.status_code == 200
    assert "Centro" in response.text
    assert "CENTRO" not in response.text
    assert "2" in response.text


def test_dashboard_shows_masked_documents_and_equipment_statuses(client: TestClient) -> None:
    _seed_minimal_data()
    cookies = _login_admin(client)

    response = client.get("/dashboard", cookies=cookies)

    assert response.status_code == 200
    assert "***.***.***-05" in response.text
    assert "12.345.678-9" in response.text
    assert "Em atraso" in response.text
    assert "Em manutenção: 0" in response.text
