"""Pydantic v2 schemas for simulation endpoint."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class SimulationRunRequest(BaseModel):
    snapshot_hours: int = Field(default=8760, ge=1, le=8760)
    solver: str = "highs"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    supply_ids: list[str] = Field(default_factory=list)
    demand_ids: list[str] = Field(default_factory=list)
    network_ids: list[str] = Field(default_factory=list)
    pypsa_params: Optional[dict] = None
    asset_overrides: Optional[dict] = None


class SimulationRunResponse(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    status: str
    total_supply_mwh: Optional[float]
    total_demand_mwh: Optional[float]
    balance_mwh: Optional[float]
    objective_value: Optional[float]
    result_json: Optional[dict]
    created_at: datetime


class SimulationListItem(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    status: str
    supply_ids: list[str]
    demand_ids: list[str]
    network_ids: list[str]
    total_supply_mwh: Optional[float]
    total_demand_mwh: Optional[float]
    created_at: datetime
