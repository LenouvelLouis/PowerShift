"""Wind turbine domain entity."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.supply.base_supply import BaseSupply


@dataclass
class WindTurbine(BaseSupply):
    def get_type(self) -> str:
        return "wind_turbine"

    def get_carrier(self) -> str:
        return "wind"
