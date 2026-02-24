from __future__ import annotations

from datetime import datetime, timedelta
import re

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from app.core.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (UnknownHashError, ValueError):
        if not hashed_password.startswith("$2"):
            return False

        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except ValueError:
            return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict[str, str], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, str] | None:
    payload, _reason = decode_access_token_with_reason(token)
    return payload


def decode_access_token_with_reason(token: str) -> tuple[dict[str, str] | None, str]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        return None, "expired"
    except JWTError:
        return None, "invalid_signature_or_claims"
    return payload, "ok"


def validate_password(password: str) -> list[str]:
    errors: list[str] = []
    if len(password) < settings.min_password_length:
        errors.append(f"Senha deve ter ao menos {settings.min_password_length} caracteres.")
    if not re.search(r"[A-Za-z]", password):
        errors.append("Senha deve conter ao menos uma letra.")
    if not re.search(r"\d", password):
        errors.append("Senha deve conter ao menos um número.")
    return errors
