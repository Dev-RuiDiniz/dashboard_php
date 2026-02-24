from __future__ import annotations

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from app.core.auth import ROLE_DEFINITIONS
from app.core.config import Settings, settings
from app.core.security import get_password_hash
import app.main as main
from app.models import Role, User


def _create_user_with_role(role_name: str, email: str) -> None:
    with main.SessionLocal() as db:
        role = db.execute(select(Role).where(Role.name == role_name)).scalar_one()
        user = User(
            name=f"Usuário {role_name}",
            email=email,
            hashed_password=get_password_hash("Senha123"),
            is_active=True,
            roles=[role],
        )
        db.add(user)
        db.commit()


def _login(client: TestClient, email: str, password: str = "Senha123") -> dict[str, str]:
    login_response = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    assert login_response.status_code == 303
    token = login_response.cookies.get("access_token")
    return {"access_token": token}



def test_settings_allows_missing_secret_key_until_runtime_validation() -> None:
    cfg = Settings(app_env="production", secret_key="", database_url="postgresql://example/db")
    assert cfg.secret_key == ""

def test_login_ok(client: TestClient) -> None:
    response = client.post(
        "/login",
        data={
            "email": settings.default_admin_email,
            "password": settings.default_admin_password,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "access_token=" in response.headers.get("set-cookie", "")


def test_login_invalid(client: TestClient) -> None:
    response = client.post(
        "/login",
        data={"email": settings.default_admin_email, "password": "invalid"},
        follow_redirects=False,
    )
    assert response.status_code == 401


def test_api_login_ok(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": settings.default_admin_email,
            "password": settings.default_admin_password,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == settings.default_admin_email


def test_login_accepts_email_with_whitespace_and_case_variation(client: TestClient) -> None:
    response = client.post(
        "/login",
        data={
            "email": f"  {settings.default_admin_email.upper()}  ",
            "password": settings.default_admin_password,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303


def test_create_user_blocks_duplicate_email_case_insensitive(client: TestClient) -> None:
    cookies = _login(client, settings.default_admin_email, settings.default_admin_password)

    response = client.post(
        "/admin/users/new",
        data={
            "name": "Outro Admin",
            "email": settings.default_admin_email.upper(),
            "password": "Senha123",
            "role_ids": [1],
            "is_active": "true",
        },
        cookies=cookies,
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert "E-mail já cadastrado." in response.text


def test_protected_route_without_token(client: TestClient) -> None:
    response = client.get("/familias")
    assert response.status_code == 401


def test_rbac_matrix_is_explicit_for_all_roles() -> None:
    assert ROLE_DEFINITIONS == {
        "Admin": {
            "description": "Administrador do sistema",
            "permissions": {
                "manage_users",
                "view_users",
                "manage_families",
                "view_families",
                "manage_equipment",
                "view_equipment",
                "manage_baskets",
                "view_baskets",
                "manage_street",
                "view_street",
                "manage_visits",
                "view_visits",
            },
        },
        "Operador": {
            "description": "Operação diária de cadastros",
            "permissions": {
                "manage_families",
                "view_families",
                "manage_equipment",
                "view_equipment",
                "manage_baskets",
                "view_baskets",
                "manage_street",
                "view_street",
                "manage_visits",
                "view_visits",
            },
        },
        "Leitura": {
            "description": "Acesso somente leitura",
            "permissions": {
                "view_families",
                "view_equipment",
                "view_baskets",
                "view_street",
                "view_visits",
            },
        },
    }


@pytest.mark.parametrize(
    ("role_name", "email", "path", "method"),
    [
        ("Operador", "operador@example.com", "/admin/users", "GET"),
        ("Operador", "operador@example.com", "/admin/users/new", "GET"),
        ("Leitura", "leitura@example.com", "/admin/users", "GET"),
        ("Leitura", "leitura@example.com", "/equipamentos/novo", "GET"),
        ("Leitura", "leitura@example.com", "/rua/nova", "GET"),
        ("Leitura", "leitura@example.com", "/familias/1/visitas", "POST"),
    ],
)
def test_protected_routes_forbidden_by_role(
    client: TestClient, role_name: str, email: str, path: str, method: str
) -> None:
    _create_user_with_role(role_name=role_name, email=email)
    cookies = _login(client, email)

    response = client.request(method, path, cookies=cookies)

    assert response.status_code == 403


def test_reader_cannot_export_reports_csv(client: TestClient) -> None:
    _create_user_with_role(role_name="Leitura", email="leitura.export@example.com")
    cookies = _login(client, "leitura.export@example.com")

    response = client.get("/relatorios/export.csv?report_type=familias", cookies=cookies)

    assert response.status_code == 403


def test_on_startup_with_multiple_existing_users(client: TestClient) -> None:
    with main.SessionLocal() as db:
        admin_role = db.execute(select(Role).where(Role.name == "Admin")).scalar_one()
        db.add_all(
            [
                User(
                    name="Usuário 1",
                    email="u1@example.com",
                    hashed_password=get_password_hash("Senha123"),
                    is_active=True,
                    roles=[admin_role],
                ),
                User(
                    name="Usuário 2",
                    email="u2@example.com",
                    hashed_password=get_password_hash("Senha123"),
                    is_active=True,
                    roles=[admin_role],
                ),
            ]
        )
        db.commit()

    main.on_startup()

    with main.SessionLocal() as db:
        users = db.execute(select(User)).scalars().all()
    assert len(users) == 3


def test_admin_user_list_includes_inactive_users(client: TestClient) -> None:
    with main.SessionLocal() as db:
        admin_role = db.execute(select(Role).where(Role.name == "Admin")).scalar_one()
        inactive_user = User(
            name="Usuário Inativo",
            email="inativo@example.com",
            hashed_password=get_password_hash("Senha123"),
            is_active=False,
            roles=[admin_role],
        )
        db.add(inactive_user)
        db.commit()

    cookies = _login(client, settings.default_admin_email, settings.default_admin_password)

    response = client.get("/admin/users", cookies=cookies)

    assert response.status_code == 200
    assert "Usuário Inativo" in response.text
    assert "Inativo" in response.text


def test_login_sets_cookie_flags(client: TestClient) -> None:
    original_env = settings.app_env
    original_cookie_secure = settings.cookie_secure
    settings.app_env = "production"
    settings.cookie_secure = False
    try:
        response = client.post(
            "/login",
            data={
                "email": settings.default_admin_email,
                "password": settings.default_admin_password,
            },
            follow_redirects=False,
        )
    finally:
        settings.app_env = original_env
        settings.cookie_secure = original_cookie_secure

    set_cookie = response.headers.get("set-cookie", "")
    assert response.status_code == 303
    assert "access_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Path=/" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Max-Age=" in set_cookie
    assert "Secure" in set_cookie


def test_session_persists_after_create_user_without_overwriting_cookie(client: TestClient) -> None:
    cookies = _login(client, settings.default_admin_email, settings.default_admin_password)

    admin_before = client.get("/admin/users", cookies=cookies)
    assert admin_before.status_code == 200

    create_response = client.post(
        "/admin/users/new",
        data={
            "name": "Novo Operador",
            "email": "novo.operador@example.com",
            "password": "Senha123",
            "role_ids": [2],
            "is_active": "true",
        },
        cookies=cookies,
        follow_redirects=False,
    )
    assert create_response.status_code == 303
    set_cookie = create_response.headers.get("set-cookie", "")
    assert "access_token=" not in set_cookie

    users_response = client.get("/admin/users", cookies=cookies)
    admin_after = client.get("/admin/users", cookies=cookies)
    assert users_response.status_code == 200
    assert admin_after.status_code == 200


def test_authenticated_routes_have_anti_cache_headers(client: TestClient) -> None:
    cookies = _login(client, settings.default_admin_email, settings.default_admin_password)

    response = client.get("/admin/users", cookies=cookies)

    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "no-store"
    assert response.headers.get("Pragma") == "no-cache"
    assert response.headers.get("Vary") == "Cookie"
