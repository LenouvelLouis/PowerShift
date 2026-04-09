"""Abstract base network domain entity — shared by Transformer and Cable."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass

from app.domain.entities.base_component import BaseComponent


@dataclass
class BaseNetwork(BaseComponent):
    """Abstract base for all network-side components (MV/LV distribution)."""

    voltage_kv: float       # operating voltage or HV-side reference
    capacity_mva: float     # rated capacity (MVA); use 0.0 for cable
    losses_kw: float | None  # optional no-load or resistive losses

    @abstractmethod
    def get_network_type(self) -> str:
        """Return the component sub-type string: 'transformer' or 'cable'."""

    def get_type(self) -> str:
        """Implement BaseComponent.get_type() by delegating to get_network_type()."""
        return self.get_network_type()

    @abstractmethod
    def to_pypsa_params(self) -> dict:
        """Return keyword arguments for pypsa.Network.add(type, name, **params).

        Bus assignment (bus0/bus1) is determined at simulation time by the
        network builder from the topology — not stored in the domain entity.
        """
