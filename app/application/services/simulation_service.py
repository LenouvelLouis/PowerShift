"""Simulation service — orchestrates the run simulation use case."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.use_cases.run_simulation import RunSimulationUseCase


@dataclass
class SimulationResultDTO:
    total_supply_mwh: float
    total_demand_mwh: float
    balance_mwh: float
    status: str


class SimulationService:
    def __init__(self, use_case: RunSimulationUseCase) -> None:
        self._use_case = use_case

    async def run(self, snapshot_hours: int = 24) -> SimulationResultDTO:
        result = await self._use_case.execute(snapshot_hours=snapshot_hours)
        return SimulationResultDTO(
            total_supply_mwh=result.total_supply_mwh,
            total_demand_mwh=result.total_demand_mwh,
            balance_mwh=result.balance_mwh,
            status=result.status,
        )
