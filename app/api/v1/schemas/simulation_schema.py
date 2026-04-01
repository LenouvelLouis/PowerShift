"""Pydantic v2 schemas for simulation endpoint."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class SimulationRunRequest(BaseModel):
    snapshot_hours: int = Field(default=8760, ge=1, le=8760)
    solver: str = "highs"
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    supply_ids: list[str] = Field(default_factory=list)
    demand_ids: list[str] = Field(default_factory=list)
    network_ids: list[str] = Field(default_factory=list)
    pypsa_params: Optional[dict] = None
    asset_overrides: Optional[dict] = None
    hourly_load_overrides: Optional[dict[str, list[float]]] = None
    optimization_objective: Literal["min_cost", "min_emissions", "max_renewable"] = "min_cost"

    @model_validator(mode="after")
    def validate_hourly_load_overrides(self) -> SimulationRunRequest:
        if not self.hourly_load_overrides:
            return self
        for demand_id, profile in self.hourly_load_overrides.items():
            if demand_id not in self.demand_ids:
                raise ValueError(f"hourly_load_overrides key '{demand_id}' not in demand_ids")
            if len(profile) != self.snapshot_hours:
                raise ValueError(
                    f"Profile for '{demand_id}' has {len(profile)} values, expected {self.snapshot_hours}"
                )
        return self

    @model_validator(mode="after")
    def validate_date_range_vs_snapshot_hours(self) -> SimulationRunRequest:
        """Validate that date range matches snapshot_hours (assuming 24 hourly snapshots per day)."""
        if self.start_date is None or self.end_date is None:
            return self
        if self.start_date > self.end_date:
            raise ValueError("start_date must be <= end_date")
        days_covered = (self.end_date - self.start_date).days + 1  # inclusive
        expected_hours = days_covered * 24
        if expected_hours != self.snapshot_hours:
            raise ValueError(
                f"Date range ({self.start_date} to {self.end_date}) covers {expected_hours} hours, "
                f"but snapshot_hours={self.snapshot_hours}. They must match."
            )
        return self


class SimulationRunResponse(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    status: str
    solver: str
    name: Optional[str] = None
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
    solver: str
    name: Optional[str] = None
    supply_ids: list[str]
    demand_ids: list[str]
    network_ids: list[str]
    total_supply_mwh: Optional[float]
    total_demand_mwh: Optional[float]
    created_at: datetime


class SimulationRenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


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
    asset_overrides: Optional[dict] = None
    pypsa_params: Optional[dict] = None
    hourly_load_overrides: Optional[dict[str, list[float]]] = None
    optimization_objective: Literal["min_cost", "min_emissions", "max_renewable"] = "min_cost"


class SimulationSolverInfo(BaseModel):
    name: str
    available: bool
    reason: Optional[str] = None
