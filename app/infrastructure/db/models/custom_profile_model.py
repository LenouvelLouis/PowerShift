"""SQLModel ORM model for custom hourly load profiles."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel


class CustomLoadProfileModel(SQLModel, table=True):
    __tablename__ = "custom_load_profiles"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    demand_id: uuid.UUID = Field(unique=True, foreign_key="demands.id")
    profile_data: list[float] = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
