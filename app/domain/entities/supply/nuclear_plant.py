"""Nuclear plant domain entity."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.supply.base_supply import BaseSupply


@dataclass
class NuclearPlant(BaseSupply):
    def get_type(self) -> str:
        return "nuclear_plant"

    def get_carrier(self) -> str:
        return "nuclear"
