"""Base demand domain entity."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.entities.base_component import BaseComponent


@dataclass
class BaseDemand(BaseComponent):
    """Abstract base for all demand-side components."""

    load_mw: float

    @abstractmethod
    def get_load_profile(self) -> Sequence[float]:
        """Return a normalized hourly load profile (24 values, 0.0–1.0)."""

    def to_pypsa_params(self, profile: list[float] | None = None) -> dict:
        """Return keyword arguments for pypsa.Network.add('Load', name, **params).

        If `profile` is provided (normalized values 0.0–1.0), p_set becomes a
        time-series list of length len(profile). Otherwise a flat scalar is used.
        """
        p_set = [self.load_mw * f for f in profile] if profile is not None else self.load_mw
        return {
            "bus": "main_bus",
            "p_set": p_set,
        }
