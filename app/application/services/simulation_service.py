"""Simulation service — orchestrates the run simulation use case."""

from __future__ import annotations

import uuid

from app.api.v1.schemas.simulation_schema import (
    SimulationListItem,
    SimulationRunRequest,
    SimulationRunResponse,
)
from app.domain.interfaces.simulation_persistence_repository import ISimulationPersistenceRepository
from app.domain.interfaces.simulation_repository import SimulationRunInput
from app.domain.use_cases.run_simulation import RunSimulationUseCase
from app.infrastructure.db.models.simulation_result_model import SimulationResultModel


class SimulationService:
    def __init__(
        self,
        use_case: RunSimulationUseCase,
        persistence: ISimulationPersistenceRepository,
    ) -> None:
        self._use_case = use_case
        self._persistence = persistence

    async def run(self, body: SimulationRunRequest) -> SimulationRunResponse:
        run_input = SimulationRunInput(
            snapshot_hours=body.snapshot_hours,
            solver=body.solver,
            supply_ids=body.supply_ids,
            demand_ids=body.demand_ids,
            network_ids=body.network_ids,
            pypsa_params=body.pypsa_params or {},
        )
        result_id, output = await self._use_case.execute(run_input)
        # Fetch the stored row to get created_at and request_id
        row = await self._persistence.get_result_by_id(result_id)
        return self._to_response(row)

    async def list(self) -> list[SimulationListItem]:
        rows = await self._persistence.list_results()
        return [self._to_list_item(row) for row in rows]

    async def get_by_id(self, simulation_id: uuid.UUID) -> SimulationRunResponse | None:
        row = await self._persistence.get_result_by_id(simulation_id)
        if row is None:
            return None
        return self._to_response(row)

    @staticmethod
    def _to_response(row: SimulationResultModel) -> SimulationRunResponse:
        return SimulationRunResponse(
            id=row.id,
            request_id=row.request_id,
            status=row.status,
            total_supply_mwh=row.total_supply_mwh,
            total_demand_mwh=row.total_demand_mwh,
            balance_mwh=row.balance_mwh,
            objective_value=row.objective_value,
            result_json=row.result_json,
            created_at=row.created_at,
        )

    @staticmethod
    def _to_list_item(row: SimulationResultModel) -> SimulationListItem:
        return SimulationListItem(
            id=row.id,
            request_id=row.request_id,
            status=row.status,
            total_supply_mwh=row.total_supply_mwh,
            total_demand_mwh=row.total_demand_mwh,
            created_at=row.created_at,
        )
