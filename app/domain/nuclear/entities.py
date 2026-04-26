# app/domain/nuclear/entities.py

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class NuclearReactor:
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