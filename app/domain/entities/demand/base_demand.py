"""Base demand domain entity."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Sequence

from app.domain.entities.base_component import BaseComponent


@dataclass
class BaseDemand(BaseComponent):
    """Abstract base for all demand-side components."""

    load_mw: float

    @abstractmethod
    def get_load_profile(self) -> Sequence[float]:
        """Return a normalized hourly load profile (24 values, 0.0–1.0)."""

    def to_pypsa_params(self) -> dict:
        """Return keyword arguments for pypsa.Network.add('Load', name, **params).

        All demand types connect to the single shared bus 'main_bus' (Sprint 1 POC).
        """
        return {
            "bus": "main_bus",
            "p_set": self.load_mw,
        }
