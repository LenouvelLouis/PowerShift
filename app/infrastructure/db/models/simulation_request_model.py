"""SQLModel ORM model for simulation_requests table."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, SQLModel


class SimulationRequestModel(SQLModel, table=True):
    __tablename__ = "simulation_requests"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_hours: int = 8760
    solver: str = "highs"
    pypsa_params: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    overrides: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    supply_ids: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    demand_ids: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    network_ids: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
