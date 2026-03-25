"""Simulation endpoint."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.dependencies import get_simulation_service
from app.api.v1.schemas.simulation_schema import (
    SimulationListItem,
    SimulationRunRequest,
    SimulationRunResponse,
    SimulationScenarioExport,
)
from app.application.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.post(
    "/run",
    response_model=SimulationRunResponse,
    summary="Run a grid simulation",
    response_description="Simulation result with energy balance and objective value.",
)
async def run_simulation(
    body: SimulationRunRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationRunResponse:
    """Run a PyPSA optimal power flow simulation and persist the result.

    Pass the UUIDs of the supply, demand, and network components to include.
    Use `GET /api/v1/referential` to retrieve available asset IDs.
    """
    return await service.run(body)


@router.get(
    "",
    response_model=list[SimulationListItem],
    summary="List past simulations",
    response_description="Array of simulation summaries ordered by creation date.",
)
async def list_simulations(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> list[SimulationListItem]:
    """Return a summary list of all previously run simulations."""
    return await service.list()


@router.post(
    "/import",
    response_model=SimulationRunResponse,
    summary="Load a scenario and run a simulation",
    response_description="Simulation result from the imported scenario.",
)
async def import_scenario(
    body: SimulationScenarioExport,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationRunResponse:
    """Accept a previously exported scenario JSON and run it as a new simulation."""
    run_request = SimulationRunRequest(
        snapshot_hours=body.snapshot_hours,
        solver=body.solver,
        start_date=body.start_date,
        end_date=body.end_date,
        supply_ids=body.supply_ids,
        demand_ids=body.demand_ids,
        network_ids=body.network_ids,
        pypsa_params=body.pypsa_params,
        hourly_load_overrides=body.hourly_load_overrides,
        optimization_objective=body.optimization_objective,
    )
    return await service.run(run_request)


@router.get(
    "/{simulation_id}/export",
    response_model=SimulationScenarioExport,
    summary="Export a simulation scenario",
    response_description="JSON configuration that can be reimported to replay the simulation.",
    responses={404: {"description": "Simulation not found."}},
)
async def export_scenario(
    simulation_id: uuid.UUID,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationScenarioExport:
    """Return the configuration of a past simulation as a portable JSON scenario."""
    scenario = await service.export_scenario(simulation_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return scenario


@router.get(
    "/{simulation_id}",
    response_model=SimulationRunResponse,
    summary="Get a simulation result",
    response_description="Full simulation result including energy balance.",
    responses={404: {"description": "Simulation not found."}},
)
async def get_simulation(
    simulation_id: uuid.UUID,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationRunResponse:
    """Return the full result of a simulation identified by its UUID."""
    result = await service.get_by_id(simulation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return result
