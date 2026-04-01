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

    def to_pypsa_params(self) -> dict:
        params = super().to_pypsa_params()
        params["marginal_cost"] = 0.0
        return params
