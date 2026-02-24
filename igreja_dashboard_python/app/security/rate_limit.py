from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select

from app.models import LoginAttempt, RateLimitEvent


def enforce_login_rate_limit(
    db,
    ip: str,
    route: str = "/login",
    *,
    limit: int = 30,
    window_minutes: int = 5,
) -> None:
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)

    stmt = (
        select(RateLimitEvent)
        .where(
            RateLimitEvent.route == route,
            RateLimitEvent.ip == ip,
            RateLimitEvent.window_start >= window_start,
        )
        .order_by(RateLimitEvent.window_start.desc())
    )
    entries = db.execute(stmt).scalars().all()
    used = sum(item.request_count for item in entries)
    if used >= limit:
        raise HTTPException(status_code=429, detail="Muitas tentativas. Tente novamente em instantes.")

    bucket = entries[0] if entries else None
    if bucket:
        bucket.request_count += 1
    else:
        db.add(RateLimitEvent(route=route, ip=ip, window_start=now, request_count=1))
    db.commit()


def ensure_login_not_locked(
    db,
    identity: str,
    ip: str,
    *,
    user_id: int | None = None,
    max_failures: int = 5,
    window_minutes: int = 15,
) -> None:
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)
    stmt = select(LoginAttempt).where(LoginAttempt.attempted_at >= window_start, LoginAttempt.success.is_(False))
    attempts = db.execute(stmt).scalars().all()

    by_identity_ip = [item for item in attempts if item.identity == identity and (item.ip or "") == ip]
    by_user = [item for item in attempts if user_id is not None and item.user_id == user_id]
    if len(by_identity_ip) >= max_failures or len(by_user) >= max_failures:
        raise HTTPException(status_code=429, detail="Acesso temporariamente bloqueado. Aguarde 15 minutos.")


def register_login_attempt(db, *, identity: str, ip: str, success: bool, user_id: int | None = None) -> None:
    db.add(
        LoginAttempt(
            user_id=user_id,
            identity=identity,
            ip=ip,
            attempted_at=datetime.utcnow(),
            success=success,
        )
    )
    db.commit()
