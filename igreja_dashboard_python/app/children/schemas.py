from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models import ChildSex


class ChildCreate(BaseModel):
    family_id: int
    name: str = Field(min_length=1, max_length=120)
    birth_date: date
    sex: ChildSex = ChildSex.NI
    notes: str | None = None


class ChildUpdate(BaseModel):
    family_id: int
    name: str = Field(min_length=1, max_length=120)
    birth_date: date
    sex: ChildSex = ChildSex.NI
    notes: str | None = None


class ChildOut(BaseModel):
    id: int
    family_id: int
    name: str
    birth_date: date
    sex: ChildSex
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True
