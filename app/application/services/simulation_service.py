"""Simulation service — orchestrates the run and preview simulation use cases."""

from __future__ import annotations

import importlib.util
import shutil
import uuid
from datetime import datetime, timezone

from app.api.v1.schemas.simulation_schema import (
    SimulationListItem,
    SimulationSolverInfo,
    SimulationRunRequest,
    SimulationRunResponse,
    SimulationScenarioExport,
)
from app.domain.interfaces.simulation_persistence_repository import ISimulationPersistenceRepository
from app.domain.interfaces.simulation_repository import SimulationRunInput
from app.domain.use_cases.preview_simulation import PreviewSimulationUseCase
from app.domain.use_cases.run_simulation import RunSimulationUseCase
from app.infrastructure.db.models.simulation_request_model import SimulationRequestModel
from app.infrastructure.db.models.simulation_result_model import SimulationResultModel


class SimulationService:
    _SUPPORTED_SOLVERS = (
        "highs",
        "glpk",
        "cbc",
        "scip",
        "gurobi",
        "cplex",
        "xpress",
    )

    def __init__(
        self,
        use_case: RunSimulationUseCase,
        persistence: ISimulationPersistenceRepository,
        preview_use_case: PreviewSimulationUseCase | None = None,
    ) -> None:
        self._use_case = use_case
        self._persistence = persistence
        self._preview_use_case = preview_use_case

    # ── Helpers ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _to_run_input(body: SimulationRunRequest) -> SimulationRunInput:
        return SimulationRunInput(
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

    # ── Public methods ────────────────────────────────────────────────────────────

    async def run(self, body: SimulationRunRequest) -> SimulationRunResponse:
        run_input = self._to_run_input(body)
        result_id, output = await self._use_case.execute(run_input)
        row = await self._persistence.get_result_by_id(result_id)
        req = await self._persistence.get_request_by_id(row.request_id)
        return self._to_response(row, req)

    async def save(self, body: SimulationRunRequest) -> SimulationRunResponse:
        """Run PyPSA via the preview code path (LP, no nuclear unit-commitment) and persist the result.

        Identical to preview() but writes request + result to the database.
        """
        if self._preview_use_case is None:
            raise RuntimeError("PreviewSimulationUseCase not wired — check dependencies.py")
        run_input = self._to_run_input(body)
        output = await self._preview_use_case.execute(run_input)
        request_id = await self._persistence.save_request(run_input)
        result_row = await self._persistence.save_result(request_id, output)
        row = await self._persistence.get_result_by_id(result_row.id)
        req = await self._persistence.get_request_by_id(row.request_id)
        return self._to_response(row, req)

    async def preview(self, body: SimulationRunRequest) -> SimulationRunResponse:
        """Run PyPSA without any database writes — for live frontend preview.

        Returns the same SimulationRunResponse schema as /run but with
        generated (non-persisted) id, request_id and created_at values.
        """
        if self._preview_use_case is None:
            raise RuntimeError("PreviewSimulationUseCase not wired — check dependencies.py")
        run_input = self._to_run_input(body)
        output = await self._preview_use_case.execute(run_input)
        return SimulationRunResponse(
            id=uuid.uuid4(),
            request_id=uuid.uuid4(),
            status=output.status,
            solver=body.solver,
            start_date=body.start_date,
            end_date=body.end_date,
            total_supply_mwh=output.total_supply_mwh,
            total_demand_mwh=output.total_demand_mwh,
            balance_mwh=output.balance_mwh,
            objective_value=output.objective_value,
            result_json=output.result_json,
            created_at=datetime.now(timezone.utc),
        )

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

    async def list_solvers(self) -> list[SimulationSolverInfo]:
        return [self._solver_info(name) for name in self._SUPPORTED_SOLVERS]

    @staticmethod
    def _has_python_module(module_name: str) -> bool:
        return importlib.util.find_spec(module_name) is not None

    @classmethod
    def _solver_info(cls, solver_name: str) -> SimulationSolverInfo:
        if solver_name == "highs":
            if cls._has_python_module("highspy") or shutil.which("highs"):
                return SimulationSolverInfo(name=solver_name, available=True)
            return SimulationSolverInfo(
                name=solver_name,
                available=False,
                reason="Install highspy or highs executable.",
            )

        if solver_name == "glpk":
            if shutil.which("glpsol"):
                return SimulationSolverInfo(name=solver_name, available=True)
            return SimulationSolverInfo(
                name=solver_name,
                available=False,
                reason="Install glpsol (GLPK).",
            )

        if solver_name == "cbc":
            if shutil.which("cbc"):
                return SimulationSolverInfo(name=solver_name, available=True)
            return SimulationSolverInfo(
                name=solver_name,
                available=False,
                reason="Install CBC executable.",
            )

        if solver_name == "scip":
            if shutil.which("scip"):
                return SimulationSolverInfo(name=solver_name, available=True)
            return SimulationSolverInfo(
                name=solver_name,
                available=False,
                reason="Install SCIP executable.",
            )

        if solver_name == "gurobi":
            if cls._has_python_module("gurobipy") or shutil.which("gurobi_cl"):
                return SimulationSolverInfo(name=solver_name, available=True)
            return SimulationSolverInfo(
                name=solver_name,
                available=False,
                reason="Install gurobipy or gurobi_cl and configure license.",
            )

        if solver_name == "cplex":
            if cls._has_python_module("cplex"):
                return SimulationSolverInfo(name=solver_name, available=True)
            return SimulationSolverInfo(
                name=solver_name,
                available=False,
                reason="Install cplex Python package and configure license.",
            )

        if solver_name == "xpress":
            if cls._has_python_module("xpress"):
                return SimulationSolverInfo(name=solver_name, available=True)
            return SimulationSolverInfo(
                name=solver_name,
                available=False,
                reason="Install xpress Python package and configure license.",
            )

        return SimulationSolverInfo(name=solver_name, available=False, reason="Unsupported solver.")

    @staticmethod
    def _to_response(row: SimulationResultModel, req: SimulationRequestModel | None = None) -> SimulationRunResponse:
        return SimulationRunResponse(
            id=row.id,
            request_id=row.request_id,
            status=row.status,
            solver=req.solver if req is not None else "highs",
            name=req.name if req is not None else None,
            start_date=req.start_date if req is not None else None,
            end_date=req.end_date if req is not None else None,
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
            solver=req.solver,
            name=req.name,
            supply_ids=req.supply_ids or [],
            demand_ids=req.demand_ids or [],
            network_ids=req.network_ids or [],
            total_supply_mwh=row.total_supply_mwh,
            total_demand_mwh=row.total_demand_mwh,
            created_at=row.created_at,
        )
