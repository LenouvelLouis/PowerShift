"""SQLModel ORM model for simulation_results table."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, SQLModel


class SimulationResultModel(SQLModel, table=True):
    __tablename__ = "simulation_results"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    request_id: uuid.UUID = Field(
        sa_column=Column(
            sa.UUID(as_uuid=True),
            sa.ForeignKey("simulation_requests.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    status: str
    total_supply_mwh: Optional[float] = None
    total_demand_mwh: Optional[float] = None
    balance_mwh: Optional[float] = None
    objective_value: Optional[float] = None
    result_json: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
