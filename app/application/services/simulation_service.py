"""Simulation service — orchestrates the run simulation use case."""

from __future__ import annotations

import uuid

from app.api.v1.schemas.simulation_schema import (
    SimulationListItem,
    SimulationRunRequest,
    SimulationRunResponse,
    SimulationScenarioExport,
)
from app.domain.interfaces.simulation_persistence_repository import ISimulationPersistenceRepository
from app.domain.interfaces.simulation_repository import SimulationRunInput
from app.domain.use_cases.run_simulation import RunSimulationUseCase
from app.infrastructure.db.models.simulation_request_model import SimulationRequestModel
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
            name=body.name,
            start_date=body.start_date,
            end_date=body.end_date,
            supply_ids=body.supply_ids,
            demand_ids=body.demand_ids,
            network_ids=body.network_ids,
            pypsa_params=body.pypsa_params or {},
            asset_overrides=body.asset_overrides or {},
            hourly_load_overrides=body.hourly_load_overrides or {},
            optimization_objective=body.optimization_objective,
        )
        result_id, output = await self._use_case.execute(run_input)
        row = await self._persistence.get_result_by_id(result_id)
        req = await self._persistence.get_request_by_id(row.request_id)
        return self._to_response(row, req)

    async def list(self) -> list[SimulationListItem]:
        pairs = await self._persistence.list_results()
        return [self._to_list_item(result, request) for result, request in pairs]

    async def get_by_id(self, simulation_id: uuid.UUID) -> SimulationRunResponse | None:
        row = await self._persistence.get_result_by_id(simulation_id)
        if row is None:
            return None
        req = await self._persistence.get_request_by_id(row.request_id)
        return self._to_response(row, req)

    async def delete(self, simulation_id: uuid.UUID) -> bool:
        return await self._persistence.delete_by_result_id(simulation_id)

    async def rename(self, simulation_id: uuid.UUID, name: str) -> SimulationRunResponse | None:
        row = await self._persistence.get_result_by_id(simulation_id)
        if row is None:
            return None
        req = await self._persistence.get_request_by_id(row.request_id)
        if req is None:
            return None
        await self._persistence.update_request_name(row.request_id, name)
        req.name = name
        return self._to_response(row, req)

    async def export_scenario(self, simulation_id: uuid.UUID) -> SimulationScenarioExport | None:
        result_row = await self._persistence.get_result_by_id(simulation_id)
        if result_row is None:
            return None
        request_row = await self._persistence.get_request_by_id(result_row.request_id)
        if request_row is None:
            return None
        return SimulationScenarioExport(
            snapshot_hours=request_row.snapshot_hours,
            solver=request_row.solver,
            start_date=request_row.start_date,
            end_date=request_row.end_date,
            supply_ids=request_row.supply_ids or [],
            demand_ids=request_row.demand_ids or [],
            network_ids=request_row.network_ids or [],
            asset_overrides=request_row.asset_overrides,
            pypsa_params=request_row.pypsa_params,
            hourly_load_overrides=request_row.hourly_load_overrides,
            optimization_objective=request_row.optimization_objective,
        )

    @staticmethod
    def _to_response(row: SimulationResultModel, req: SimulationRequestModel | None = None) -> SimulationRunResponse:
        return SimulationRunResponse(
            id=row.id,
            request_id=row.request_id,
            status=row.status,
            name=req.name if req is not None else None,
            total_supply_mwh=row.total_supply_mwh,
            total_demand_mwh=row.total_demand_mwh,
            balance_mwh=row.balance_mwh,
            objective_value=row.objective_value,
            result_json=row.result_json,
            created_at=row.created_at,
        )

    @staticmethod
    def _to_list_item(row: SimulationResultModel, req: SimulationRequestModel) -> SimulationListItem:
        return SimulationListItem(
            id=row.id,
            request_id=row.request_id,
            status=row.status,
            name=req.name,
            supply_ids=req.supply_ids or [],
            demand_ids=req.demand_ids or [],
            network_ids=req.network_ids or [],
            total_supply_mwh=row.total_supply_mwh,
            total_demand_mwh=row.total_demand_mwh,
            created_at=row.created_at,
        )
