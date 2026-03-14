"""Abstract simulation repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class SimulationRunInput:
    snapshot_hours: int = 8760
    solver: str = "highs"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    supply_ids: list[str] = field(default_factory=list)
    demand_ids: list[str] = field(default_factory=list)
    network_ids: list[str] = field(default_factory=list)
    pypsa_params: dict = field(default_factory=dict)


@dataclass
class SimulationRunOutput:
    total_supply_mwh: float
    total_demand_mwh: float
    balance_mwh: float
    status: str
    objective_value: float = 0.0
    result_json: dict = field(default_factory=dict)


class ISimulationRepository(ABC):
    @abstractmethod
    async def run(
        self,
        run_input: SimulationRunInput,
        supplies: list,
        demands: list,
        network_components: list,
    ) -> SimulationRunOutput:
        """Execute a grid simulation and return the result."""
