from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models to register them with SQLAlchemy metadata.
from app import models  # noqa: E402,F401
