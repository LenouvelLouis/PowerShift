"""Solar panel domain entity."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.supply.base_supply import BaseSupply


@dataclass
class SolarPanel(BaseSupply):
    def get_type(self) -> str:
        return "solar_panel"

    def get_carrier(self) -> str:
        return "solar"

    def to_pypsa_params(self) -> dict:
        params = super().to_pypsa_params()
        params["marginal_cost"] = 0.001
        return params
