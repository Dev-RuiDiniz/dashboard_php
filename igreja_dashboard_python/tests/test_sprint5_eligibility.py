from __future__ import annotations

from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.core.config import settings
from app.core.security import get_password_hash
from app.eligibility.engine import get_system_settings, list_eligible_families
from app.models import (
    DeliveryEvent,
    DeliveryInvite,
    DeliveryWithdrawal,
    Family,
    FoodBasket,
    FoodBasketStatus,
    Role,
    User,
    VulnerabilityLevel,
)


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return {"access_token": response.cookies.get("access_token")}


def _login_admin(client: TestClient) -> dict[str, str]:
    return _login(client, settings.default_admin_email, settings.default_admin_password)


def _create_family(
    *,
    cpf: str,
    vulnerability: VulnerabilityLevel,
    documentation_status: str = "OK",
    neighborhood: str = "Centro",
) -> int:
    with main.SessionLocal() as db:
        family = Family(
            responsible_name=f"Família {cpf[-3:]}",
            responsible_cpf=cpf,
            phone="11999999999",
            birth_date=date(1985, 1, 1),
            vulnerability=vulnerability,
            documentation_status=documentation_status,
            neighborhood=neighborhood,
            is_active=True,
        )
        db.add(family)
        db.commit()
        db.refresh(family)
        return family.id


def _set_settings(**kwargs) -> None:
    with main.SessionLocal() as db:
        config = get_system_settings(db)
        for key, value in kwargs.items():
            setattr(config, key, value)
        db.add(config)
        db.commit()


def test_settings_change_affects_eligibility_list(client: TestClient) -> None:
    _create_family(cpf="39053344705", vulnerability=VulnerabilityLevel.HIGH)
    _create_family(cpf="52998224725", vulnerability=VulnerabilityLevel.MEDIUM)

    _set_settings(
        min_vulnerability_level=3,
        require_documentation_complete=True,
        min_months_since_last_delivery=0,
        delivery_month_limit=0,
    )

    with main.SessionLocal() as db:
        config = get_system_settings(db)
        high_only = list_eligible_families(db, config, limit=20)
        assert len(high_only) == 1

    _set_settings(min_vulnerability_level=2)

    with main.SessionLocal() as db:
        config = get_system_settings(db)
        expanded = list_eligible_families(db, config, limit=20)
        assert len(expanded) == 2


def test_family_with_pending_docs_not_eligible_when_required(client: TestClient) -> None:
    _create_family(
        cpf="11144477735",
        vulnerability=VulnerabilityLevel.HIGH,
        documentation_status="PENDING",
    )

    _set_settings(
        require_documentation_complete=True,
        min_vulnerability_level=0,
        min_months_since_last_delivery=0,
        delivery_month_limit=0,
    )

    with main.SessionLocal() as db:
        config = get_system_settings(db)
        rows = list_eligible_families(db, config, limit=20)
        assert rows == []


def test_recent_delivery_blocks_eligibility_by_months_rule(client: TestClient) -> None:
    family_id = _create_family(cpf="11144477786", vulnerability=VulnerabilityLevel.HIGH)

    with main.SessionLocal() as db:
        event = DeliveryEvent(
            title="Entrega teste",
            event_date=date.today(),
            created_by_user_id=1,
        )
        db.add(event)
        db.flush()
        db.add(
            DeliveryInvite(
                event_id=event.id,
                family_id=family_id,
                withdrawal_code="ABC123",
            )
        )
        db.add(
            DeliveryWithdrawal(
                event_id=event.id,
                family_id=family_id,
                confirmed_by_user_id=1,
                confirmed_at=datetime.utcnow(),
                signature_name="Responsável",
                signature_accepted=True,
            )
        )
        db.commit()

    _set_settings(
        min_months_since_last_delivery=2,
        min_vulnerability_level=0,
        require_documentation_complete=False,
        delivery_month_limit=0,
    )

    with main.SessionLocal() as db:
        config = get_system_settings(db)
        rows = list_eligible_families(db, config, limit=20)
        assert rows == []


def test_month_limit_blocks_eligibility(client: TestClient) -> None:
    family_id = _create_family(cpf="12312312387", vulnerability=VulnerabilityLevel.HIGH)

    with main.SessionLocal() as db:
        db.add(
            FoodBasket(
                family_id=family_id,
                reference_month=date.today().month,
                reference_year=date.today().year,
                status=FoodBasketStatus.DELIVERED,
            )
        )
        db.commit()

    _set_settings(
        delivery_month_limit=1,
        min_months_since_last_delivery=0,
        min_vulnerability_level=0,
        require_documentation_complete=False,
    )

    with main.SessionLocal() as db:
        config = get_system_settings(db)
        rows = list_eligible_families(db, config, limit=20)
        assert rows == []


def test_admin_config_requires_admin(client: TestClient) -> None:
    with main.SessionLocal() as db:
        operador_role = db.execute(select(Role).where(Role.name == "Operador")).scalar_one()
        operador = User(
            name="Operador",
            email="operador@example.com",
            hashed_password=get_password_hash("senha123"),
            roles=[operador_role],
            is_active=True,
        )
        db.add(operador)
        db.commit()

    cookies = _login(client, "operador@example.com", "senha123")
    blocked = client.get("/admin/config", cookies=cookies)
    assert blocked.status_code == 403
