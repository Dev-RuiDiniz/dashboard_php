from __future__ import annotations

from collections.abc import Iterable

from fastapi import Depends, HTTPException, Request, status

from app.models import User

ROLE_DEFINITIONS: dict[str, dict[str, object]] = {
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


def get_current_user(request: Request) -> User:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_permissions(*permissions: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if permissions and not user.has_permissions(permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return dependency


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if roles and not user.has_roles(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return dependency


def has_permissions(user: User | None, permissions: Iterable[str]) -> bool:
    if not user:
        return False
    return user.has_permissions(permissions)
