"""SQLModel ORM model for simulation_requests table."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, JSON
from sqlmodel import Field, SQLModel


class SimulationRequestModel(SQLModel, table=True):
    __tablename__ = "simulation_requests"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    name: Optional[str] = Field(default=None)
    snapshot_hours: int = 8760
    solver: str = "highs"
    start_date: Optional[date] = Field(default=None, sa_column=Column(Date, nullable=True))
    end_date: Optional[date] = Field(default=None, sa_column=Column(Date, nullable=True))
    pypsa_params: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    asset_overrides: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    supply_ids: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    demand_ids: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    network_ids: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    hourly_load_overrides: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    optimization_objective: str = "pf"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
