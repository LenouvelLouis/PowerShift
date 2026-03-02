"""Abstract simulation repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SimulationRequest:
    snapshot_hours: int = 24


@dataclass
class SimulationResult:
    total_supply_mwh: float
    total_demand_mwh: float
    balance_mwh: float
    status: str


class ISimulationRepository(ABC):
    @abstractmethod
    async def run(self, request: SimulationRequest) -> SimulationResult:
        """Execute a grid simulation and return the result."""
