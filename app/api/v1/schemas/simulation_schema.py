"""Pydantic v2 schemas for simulation endpoint."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


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
    custom_load_profiles: Optional[dict[str, list[float]]] = None
    optimization_objective: Literal["min_cost", "min_emissions", "max_renewable"] = "min_cost"

    @model_validator(mode="after")
    def validate_custom_profiles(self) -> SimulationRunRequest:
        if not self.custom_load_profiles:
            return self
        for demand_id, profile in self.custom_load_profiles.items():
            if demand_id not in self.demand_ids:
                raise ValueError(f"custom_load_profiles key '{demand_id}' not in demand_ids")
            if len(profile) != self.snapshot_hours:
                raise ValueError(
                    f"Profile for '{demand_id}' has {len(profile)} values, expected {self.snapshot_hours}"
                )
        return self


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


class SimulationScenarioExport(BaseModel):
    """Serializable snapshot of a simulation configuration (save/load)."""

    scenario_version: str = "1.0"
    snapshot_hours: int
    solver: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    supply_ids: list[str]
    demand_ids: list[str]
    network_ids: list[str]
    pypsa_params: Optional[dict] = None
    custom_load_profiles: Optional[dict[str, list[float]]] = None
    optimization_objective: Literal["min_cost", "min_emissions", "max_renewable"] = "min_cost"
