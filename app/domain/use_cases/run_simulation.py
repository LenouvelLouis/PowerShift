"""Use case: run a PyPSA grid simulation."""

from __future__ import annotations

import uuid

from app.domain.interfaces.demand_repository import IDemandRepository
from app.domain.interfaces.network_repository import INetworkRepository
from app.domain.interfaces.simulation_persistence_repository import ISimulationPersistenceRepository
from app.domain.interfaces.simulation_repository import (
    ISimulationRepository,
    SimulationRunInput,
    SimulationRunOutput,
)
from app.domain.interfaces.supply_repository import ISupplyRepository


class RunSimulationUseCase:
    def __init__(
        self,
        grid_simulation: ISimulationRepository,
        persistence: ISimulationPersistenceRepository,
        supply_repo: ISupplyRepository,
        demand_repo: IDemandRepository,
        network_repo: INetworkRepository,
    ) -> None:
        self._grid_simulation = grid_simulation
        self._persistence = persistence
        self._supply_repo = supply_repo
        self._demand_repo = demand_repo
        self._network_repo = network_repo

    async def execute(self, run_input: SimulationRunInput) -> tuple[uuid.UUID, SimulationRunOutput]:
        # 1. Save request to DB → get request_id
        request_id = await self._persistence.save_request(run_input)

        # 2. Fetch assets by IDs (skip missing ones silently)
        supplies = [
            s
            for sid in run_input.supply_ids
            if (s := await self._supply_repo.get_by_id(sid)) is not None
        ]
        demands = [
            d
            for did in run_input.demand_ids
            if (d := await self._demand_repo.get_by_id(did)) is not None
        ]
        networks = [
            n
            for nid in run_input.network_ids
            if (n := await self._network_repo.get_by_id(nid)) is not None
        ]

        # 3. Apply overrides to entity attributes before simulation
        overrides = run_input.overrides or {}
        for entity in [*supplies, *demands, *networks]:
            entity_overrides = overrides.get(str(entity.id), {})
            for field_name, value in entity_overrides.items():
                if hasattr(entity, field_name):
                    setattr(entity, field_name, value)

        # 4. Run PyPSA
        output = await self._grid_simulation.run(run_input, supplies, demands, networks)

        # 5. Persist result
        result_row = await self._persistence.save_result(request_id, output)

        return result_row.id, output
