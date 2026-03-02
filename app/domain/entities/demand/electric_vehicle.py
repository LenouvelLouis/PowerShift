"""Electric vehicle demand entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.domain.entities.demand.base_demand import BaseDemand

# Typical EV charging load profile (24 h, normalised)
_EV_PROFILE: list[float] = [
    0.8, 0.9, 1.0, 0.95, 0.7, 0.4,
    0.2, 0.1, 0.1, 0.1, 0.15, 0.2,
    0.2, 0.2, 0.15, 0.1, 0.15, 0.3,
    0.5, 0.6, 0.7, 0.75, 0.8, 0.85,
]


@dataclass
class ElectricVehicle(BaseDemand):
    def get_type(self) -> str:
        return "electric_vehicle"

    def get_load_profile(self) -> Sequence[float]:
        return _EV_PROFILE
