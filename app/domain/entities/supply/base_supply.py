"""Base supply domain entity."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass

from app.domain.entities.base_component import BaseComponent


@dataclass
class BaseSupply(BaseComponent):
    """Abstract base for all supply-side components."""

    capacity_mw: float
    efficiency: float  # 0.0 – 1.0

    @abstractmethod
    def get_carrier(self) -> str:
        """Return the energy carrier (e.g. 'wind', 'solar', 'nuclear')."""

    def to_pypsa_params(self) -> dict:
        """Return keyword arguments for pypsa.Network.add('Generator', name, **params).

        All supply types connect to the single shared bus 'main_bus' (Sprint 1 POC).
        """
        return {
            "bus": "main_bus",
            "carrier": self.get_carrier(),
            "p_nom": self.capacity_mw,
            "marginal_cost": 1.0,
        }
