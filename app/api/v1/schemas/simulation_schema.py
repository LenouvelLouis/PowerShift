"""Pydantic v2 schemas for simulation endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    snapshot_hours: int = Field(default=24, ge=1, le=8760)


class SimulationResponse(BaseModel):
    total_supply_mwh: float
    total_demand_mwh: float
    balance_mwh: float
    status: str
