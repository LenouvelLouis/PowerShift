"""PyPSA simulation adapter — ABC + data classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.infrastructure.simulation.objectives.base import OptimizationStrategy


@dataclass
class SimulationConfig:
    """Input configuration for a PyPSA network simulation.

    Supplies, demands, and network_components are lists of domain entities.
    Each entity provides its own PyPSA parameters via to_pypsa_params().

    load_profiles maps demand.name → normalized hourly profile (0.0–1.0).
    When present, p_set becomes a time-series instead of a flat scalar.
    """

    snapshot_hours: int = 24
    solver: str = "highs"
    supplies: list = field(default_factory=list)            # list[BaseSupply]
    demands: list = field(default_factory=list)             # list[BaseDemand]
    network_components: list = field(default_factory=list)  # list[BaseNetwork]
    load_profiles: dict = field(default_factory=dict)       # demand.name -> list[float]
    solar_profiles: dict = field(default_factory=dict)      # supply.name -> list[float] (p_max_pu)
    wind_profiles: dict = field(default_factory=dict)       # supply.name -> list[float] (p_max_pu)
    nuclear_constraints: dict = field(default_factory=dict)  # supply.name -> PyPSA param overrides
    pypsa_params: dict = field(default_factory=dict)        # asset.name -> param overrides
    optimization_strategy: OptimizationStrategy | None = None  # objective strategy (default: MinCostStrategy)


@dataclass
class AdapterOutput:
    """Output of a PyPSA network simulation."""

    total_supply_mwh: float
    total_demand_mwh: float
    balance_mwh: float
    status: str
    objective_value: float = 0.0
    result_json: dict = field(default_factory=dict)


class AbstractGridSimulation(ABC):
    """Strategy interface for grid simulation backends."""

    @abstractmethod
    def run_sync(self, config: SimulationConfig) -> AdapterOutput:
        """Execute the simulation synchronously (called inside an executor)."""
