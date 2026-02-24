from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Table, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.auth_base import AuthBase
from app.db.schemas import AUTH_SCHEMA, schema_kwargs, table_key

user_roles = Table(
    "user_roles",
    AuthBase.metadata,
    Column("user_id", ForeignKey(table_key(AUTH_SCHEMA, "users.id")), primary_key=True),
    Column("role_id", ForeignKey(table_key(AUTH_SCHEMA, "roles.id")), primary_key=True),
    **schema_kwargs(AUTH_SCHEMA),
)


class Role(AuthBase):
    __tablename__ = "roles"
    __table_args__ = schema_kwargs(AUTH_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    permissions: Mapped[str | None] = mapped_column(String(255))

    users: Mapped[list[User]] = relationship("User", secondary=user_roles, back_populates="roles")

    def permission_set(self) -> set[str]:
        if not self.permissions:
            return set()
        return {item.strip() for item in self.permissions.split(",") if item.strip()}


class User(AuthBase):
    __tablename__ = "users"
    __table_args__ = schema_kwargs(AUTH_SCHEMA)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, server_default="")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("1"))

    roles: Mapped[list[Role]] = relationship("Role", secondary=user_roles, back_populates="users")

    def permissions(self) -> set[str]:
        permissions: set[str] = set()
        for role in self.roles:
            permissions.update(role.permission_set())
        return permissions

    def role_names(self) -> set[str]:
        return {role.name for role in self.roles}

    def has_permissions(self, required: Iterable[str]) -> bool:
        current = self.permissions()
        return all(permission in current for permission in required)

    def has_roles(self, required: Iterable[str]) -> bool:
        current = self.role_names()
        return any(role in current for role in required)


class PasswordResetToken(AuthBase):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("ix_password_reset_tokens_user_id", "user_id"),
        Index("ix_password_reset_tokens_expires_at", "expires_at"),
        schema_kwargs(AUTH_SCHEMA),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(table_key(AUTH_SCHEMA, "users.id")), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)
    request_ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))


class LoginAttempt(AuthBase):
    __tablename__ = "login_attempts"
    __table_args__ = (
        Index("ix_login_attempts_user_id", "user_id"),
        Index("ix_login_attempts_identity_ip_attempted", "identity", "ip", "attempted_at"),
        Index("ix_login_attempts_attempted_at", "attempted_at"),
        schema_kwargs(AUTH_SCHEMA),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey(table_key(AUTH_SCHEMA, "users.id")))
    identity: Mapped[str] = mapped_column(String(120), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64))
    attempted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))


class RateLimitEvent(AuthBase):
    __tablename__ = "rate_limit_events"
    __table_args__ = (
        Index("ix_rate_limit_events_route_ip_window", "route", "ip", "window_start"),
        schema_kwargs(AUTH_SCHEMA),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    route: Mapped[str] = mapped_column(String(120), nullable=False)
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    request_count: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
