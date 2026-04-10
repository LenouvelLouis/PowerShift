"""Battery storage domain entity."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.supply.base_supply import BaseSupply


@dataclass
class BatteryStorage(BaseSupply):
    """Lithium-ion battery energy storage system.

    capacity_mw  — rated power (MW) for charge and discharge
    efficiency   — one-way efficiency (e.g. 0.95); round-trip = efficiency²
    max_hours    — hours of storage at rated power; energy = capacity_mw × max_hours
    """

    max_hours: float = 4.0

    def get_type(self) -> str:
        return "battery_storage"

    def get_carrier(self) -> str:
        return "battery"

    def to_pypsa_params(self) -> dict:
        """Return keyword arguments for pypsa.Network.add('StorageUnit', name, **params)."""
        return {
            "bus": "main_bus",
            "carrier": "battery",
            "p_nom": self.capacity_mw,
            "max_hours": self.max_hours,
            "efficiency_store": self.efficiency,
            "efficiency_dispatch": self.efficiency,
            "marginal_cost": 0.0,
            "cyclic_state_of_charge": True,
        }
