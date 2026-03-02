"""Use case: run a PyPSA grid simulation."""

from __future__ import annotations

from app.domain.interfaces.simulation_repository import (
    ISimulationRepository,
    SimulationRequest,
    SimulationResult,
)


class RunSimulationUseCase:
    def __init__(self, simulation_repo: ISimulationRepository) -> None:
        self._repo = simulation_repo

    async def execute(self, snapshot_hours: int = 24) -> SimulationResult:
        request = SimulationRequest(snapshot_hours=snapshot_hours)
        return await self._repo.run(request)
