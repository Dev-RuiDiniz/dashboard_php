from __future__ import annotations

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
import app.main as main
from app.models import Equipment, EquipmentStatus, Family, Loan, LoanStatus, VulnerabilityLevel



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


def _create_family(db, *, is_active: bool = True) -> Family:
    family = Family(
        responsible_name="Família Silva",
        responsible_cpf="52998224725" if is_active else "39053344705",
        responsible_rg="MG123",
        phone="31999990000",
        birth_date=main.date(1985, 4, 10),
        vulnerability=VulnerabilityLevel.LOW,
        is_active=is_active,
    )
    db.add(family)
    db.commit()
    return family


def test_equipment_code_sequence() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add_all(
            [
                Equipment(code="BEN-01", description="Item 1", status=EquipmentStatus.AVAILABLE),
                Equipment(code="BEN-03", description="Item 3", status=EquipmentStatus.AVAILABLE),
            ]
        )
        db.commit()
        assert main._generate_equipment_code(db) == "BEN-04"


def test_loan_blocked_when_equipment_unavailable(client: TestClient) -> None:
    cookies = _login_admin(client)
    with main.SessionLocal() as db:
        family = _create_family(db)
        equipment = Equipment(code="BEN-01", description="Cadeira", status=EquipmentStatus.LOANED)
        db.add(equipment)
        db.flush()
        db.add(
            Loan(
                equipment_id=equipment.id,
                family_id=family.id,
                loan_date=main.date(2025, 2, 10),
                status=LoanStatus.ACTIVE,
            )
        )
        db.commit()

    response = client.post(
        f"/equipamentos/{equipment.id}/emprestimo",
        data={
            "family_id": family.id,
            "loan_date": "2025-02-11",
            "due_date": "",
            "notes": "",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_return_blocked_when_no_active_loan(client: TestClient) -> None:
    cookies = _login_admin(client)
    with main.SessionLocal() as db:
        equipment = Equipment(code="BEN-02", description="Mesa", status=EquipmentStatus.AVAILABLE)
        db.add(equipment)
        db.commit()

    response = client.post(
        f"/equipamentos/{equipment.id}/devolver",
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_loan_blocked_for_inactive_family(client: TestClient) -> None:
    cookies = _login_admin(client)
    with main.SessionLocal() as db:
        family = _create_family(db, is_active=False)
        equipment = Equipment(code="BEN-05", description="Fogão", status=EquipmentStatus.AVAILABLE)
        db.add(equipment)
        db.commit()

    response = client.post(
        f"/equipamentos/{equipment.id}/emprestimo",
        data={
            "family_id": family.id,
            "loan_date": "2025-02-12",
            "due_date": "",
            "notes": "",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert response.status_code == 400
