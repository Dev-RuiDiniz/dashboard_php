from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import Response

from app.core.config import settings

AUTH_COOKIE_NAME = "access_token"
logger = logging.getLogger("app.audit")


def set_auth_cookie(response: Response, token: str) -> None:
    max_age = settings.access_token_expire_minutes * 60
    response.set_cookie(
        AUTH_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.auth_cookie_secure,
        path="/",
        max_age=max_age,
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        AUTH_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.auth_cookie_secure,
    )


def debug_auth(request: Request) -> dict[str, str | bool]:
    has_cookie = AUTH_COOKIE_NAME in request.cookies
    reason = "cookie_present" if has_cookie else "cookie_missing"
    logger.info(
        "debug_auth",
        extra={
            "path": request.url.path,
            "has_cookie_auth": has_cookie,
            "cookie_name": AUTH_COOKIE_NAME,
            "auth_reason": reason,
        },
    )
    return {"has_cookie": has_cookie, "reason": reason}
