"""SQLModel ORM model for simulation_requests table."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import JSON, Column, Date, DateTime
from sqlmodel import Field, SQLModel


class SimulationRequestModel(SQLModel, table=True):
    __tablename__ = "simulation_requests"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    name: str | None = Field(default=None)
    snapshot_hours: int = 8760
    solver: str = "highs"
    start_date: date | None = Field(default=None, sa_column=Column(Date, nullable=True))
    end_date: date | None = Field(default=None, sa_column=Column(Date, nullable=True))
    pypsa_params: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    asset_overrides: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    supply_ids: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    demand_ids: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    network_ids: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    hourly_load_overrides: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    optimization_objective: str = "pf"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
