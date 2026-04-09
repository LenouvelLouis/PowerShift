"""SQLModel ORM model for supply components."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class SupplyModel(SQLModel, table=True):
    __tablename__ = "supplies"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    type: str
    capacity_mw: float
    efficiency: float = 1.0
    status: str = "active"
    unit: str = "MW"
    description: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
