"""PyPSA simulation adapter — ABC + data classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SimulationConfig:
    """Input configuration for a PyPSA network simulation.

    Supplies, demands, and network_components are lists of domain entities.
    Each entity provides its own PyPSA parameters via to_pypsa_params().
    """

    snapshot_hours: int = 24
    supplies: list = field(default_factory=list)           # list[BaseSupply]
    demands: list = field(default_factory=list)            # list[BaseDemand]
    network_components: list = field(default_factory=list)  # list[BaseNetwork]


@dataclass
class SimulationResult:
    """Output of a PyPSA network simulation."""

    total_supply_mwh: float
    total_demand_mwh: float
    balance_mwh: float
    status: str


class AbstractGridSimulation(ABC):
    """Strategy interface for grid simulation backends."""

    @abstractmethod
    def run_sync(self, config: SimulationConfig) -> SimulationResult:
        """Execute the simulation synchronously (called inside an executor)."""
