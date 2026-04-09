"""LV underground cable network entity."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.network.base_network import BaseNetwork


@dataclass
class Cable(BaseNetwork):
    """Underground or overhead distribution cable."""

    length_km: float               # physical length in kilometres
    resistance_ohm_per_km: float   # AC resistance per km
    reactance_ohm_per_km: float    # reactance per km

    def get_network_type(self) -> str:
        return "cable"

    def to_pypsa_params(self) -> dict:
        # bus0/bus1 are injected by network_builder based on topology
        return {
            "length": self.length_km,
            "r": self.resistance_ohm_per_km,
            "x": self.reactance_ohm_per_km,
        }
