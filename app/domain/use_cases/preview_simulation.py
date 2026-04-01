"""Use case: run a PyPSA grid simulation WITHOUT persisting anything (live preview)."""

from __future__ import annotations

from app.domain.interfaces.demand_repository import IDemandRepository
from app.domain.interfaces.network_repository import INetworkRepository
from app.domain.interfaces.simulation_repository import (
    ISimulationRepository,
    SimulationRunInput,
    SimulationRunOutput,
)
from app.domain.interfaces.supply_repository import ISupplyRepository


class PreviewSimulationUseCase:
    """Run a grid simulation without writing anything to the database.

    Identical to RunSimulationUseCase except it skips both
    persistence.save_request() and persistence.save_result().
    Used by the frontend live-preview mode — safe to call on every
    parameter change without polluting the simulation history.
    """

    def __init__(
        self,
        grid_simulation: ISimulationRepository,
        supply_repo: ISupplyRepository,
        demand_repo: IDemandRepository,
        network_repo: INetworkRepository,
    ) -> None:
        self._grid_simulation = grid_simulation
        self._supply_repo = supply_repo
        self._demand_repo = demand_repo
        self._network_repo = network_repo

    async def execute(self, run_input: SimulationRunInput) -> SimulationRunOutput:
        # 1. Fetch assets by IDs (skip missing ones silently)
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

        # 2. Apply asset_overrides to entity attributes before simulation
        asset_overrides = run_input.asset_overrides or {}
        for entity in [*supplies, *demands, *networks]:
            entity_overrides = asset_overrides.get(str(entity.id), {})
            for field_name, value in entity_overrides.items():
                if hasattr(entity, field_name):
                    setattr(entity, field_name, value)

        # 3. Run PyPSA — NO persistence calls
        return await self._grid_simulation.run(run_input, supplies, demands, networks)
