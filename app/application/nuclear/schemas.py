from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class NuclearReactorCreate(BaseModel):
    name: str
    reactor_type: str = Field(..., examples=["PWR", "BWR", "EPR"])
    capacity_mw: float
    thermal_power_mw: float
    electrical_efficiency: float = Field(..., ge=0.0, le=1.0)
    p_min_pu: float = Field(..., ge=0.0, le=1.0)
    ramp_rate_pu_per_hour: float = Field(..., ge=0.0, le=1.0)
    min_up_time_h: int = Field(..., ge=0)
    min_down_time_h: int = Field(..., ge=0)
    startup_cost: float = Field(..., ge=0.0)
    marginal_cost_per_mwh: float = Field(..., ge=0.0)
    fuel_type: str = Field(..., examples=["uranium", "mox"])
    is_active: bool = True


class NuclearReactorResponse(BaseModel):
    id: uuid.UUID
    name: str
    reactor_type: str
    capacity_mw: float
    thermal_power_mw: float
    electrical_efficiency: float
    p_min_pu: float
    ramp_rate_pu_per_hour: float
    min_up_time_h: int
    min_down_time_h: int
    startup_cost: float
    marginal_cost_per_mwh: float
    fuel_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

