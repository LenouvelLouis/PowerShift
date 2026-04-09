"""MV/LV transformer network entity."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.network.base_network import BaseNetwork


@dataclass
class Transformer(BaseNetwork):
    """Two-winding transformer between MV and LV bus."""

    voltage_hv_kv: float   # high-voltage side (e.g. 10.0 kV MV)
    voltage_lv_kv: float   # low-voltage side  (e.g.  0.4 kV LV)

    def get_network_type(self) -> str:
        return "transformer"

    def to_pypsa_params(self) -> dict:
        # bus0/bus1 are injected by network_builder based on voltage levels
        return {
            "s_nom": self.capacity_mva,
        }
