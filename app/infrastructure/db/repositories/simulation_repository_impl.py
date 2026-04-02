"""Concrete simulation persistence repository backed by async SQLAlchemy."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domain.interfaces.simulation_persistence_repository import ISimulationPersistenceRepository
from app.domain.interfaces.simulation_repository import SimulationRunInput, SimulationRunOutput
from app.infrastructure.db.models.simulation_request_model import SimulationRequestModel
from app.infrastructure.db.models.simulation_result_model import SimulationResultModel


class SimulationRepositoryImpl(ISimulationPersistenceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_request(self, run_input: SimulationRunInput) -> uuid.UUID:
        row = SimulationRequestModel(
            snapshot_hours=run_input.snapshot_hours,
            solver=run_input.solver,
            name=run_input.name,
            start_date=run_input.start_date,
            end_date=run_input.end_date,
            pypsa_params=run_input.pypsa_params or None,
            asset_overrides=run_input.asset_overrides or None,
            supply_ids=[str(i) for i in run_input.supply_ids],
            demand_ids=[str(i) for i in run_input.demand_ids],
            network_ids=[str(i) for i in run_input.network_ids],
            hourly_load_overrides=run_input.hourly_load_overrides or None,
            optimization_objective=run_input.optimization_objective,
        )
        self._session.add(row)
        await self._session.flush()
        return row.id

    async def save_result(
        self, request_id: uuid.UUID, output: SimulationRunOutput
    ) -> SimulationResultModel:
        row = SimulationResultModel(
            request_id=request_id,
            status=output.status,
            total_supply_mwh=output.total_supply_mwh,
            total_demand_mwh=output.total_demand_mwh,
            balance_mwh=output.balance_mwh,
            objective_value=output.objective_value,
            result_json=output.result_json,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_result_by_id(self, result_id: uuid.UUID) -> SimulationResultModel | None:
        result = await self._session.execute(
            select(SimulationResultModel).where(SimulationResultModel.id == result_id)
        )
        return result.scalar_one_or_none()

    async def get_request_by_id(self, request_id: uuid.UUID) -> SimulationRequestModel | None:
        result = await self._session.execute(
            select(SimulationRequestModel).where(SimulationRequestModel.id == request_id)
        )
        return result.scalar_one_or_none()

    async def delete_by_result_id(self, result_id: uuid.UUID) -> bool:
        row = await self.get_result_by_id(result_id)
        if row is None:
            return False
        request_id = row.request_id
        # Delete result first to release the FK reference, then delete the request
        await self._session.delete(row)
        await self._session.flush()
        req = await self.get_request_by_id(request_id)
        if req is not None:
            await self._session.delete(req)
            await self._session.flush()
        return True

    async def update_request_name(self, request_id: uuid.UUID, name: str) -> None:
        req = await self.get_request_by_id(request_id)
        if req is not None:
            req.name = name
            self._session.add(req)
            await self._session.flush()

    async def list_results(self) -> list:
        stmt = (
            select(SimulationResultModel, SimulationRequestModel)
            .join(SimulationRequestModel,
                  SimulationResultModel.request_id == SimulationRequestModel.id)
            .order_by(SimulationResultModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]
