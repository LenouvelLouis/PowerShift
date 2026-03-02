"""Residential house demand entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.domain.entities.demand.base_demand import BaseDemand

# Typical residential load profile (24 h, normalised)
_RESIDENTIAL_PROFILE: list[float] = [
    0.4, 0.35, 0.3, 0.3, 0.3, 0.35,
    0.5, 0.7, 0.8, 0.75, 0.7, 0.65,
    0.7, 0.65, 0.6, 0.65, 0.75, 0.9,
    1.0, 0.95, 0.85, 0.75, 0.6, 0.5,
]


@dataclass
class House(BaseDemand):
    def get_type(self) -> str:
        return "house"

    def get_load_profile(self) -> Sequence[float]:
        return _RESIDENTIAL_PROFILE
