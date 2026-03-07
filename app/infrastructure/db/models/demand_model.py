"""SQLModel ORM model for demand components."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class DemandModel(SQLModel, table=True):
    __tablename__ = "demands"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    type: str
    load_mw: float
    status: str = "active"
    unit: str = "MW"
    description: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
