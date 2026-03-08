"""SQLModel ORM model for asset_parameters table."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, SQLModel


class AssetParametersModel(SQLModel, table=True):
    __tablename__ = "asset_parameters"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    asset_id: uuid.UUID
    asset_type: str
    params: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
