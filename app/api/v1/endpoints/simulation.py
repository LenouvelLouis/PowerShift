"""Simulation endpoint."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.api.v1.dependencies import get_simulation_service
from app.api.v1.schemas.simulation_schema import (
    SimulationListItem,
    SimulationRenameRequest,
    SimulationRunRequest,
    SimulationRunResponse,
    SimulationScenarioExport,
    SimulationSolverInfo,
)
from app.application.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.post(
    "/save",
    response_model=SimulationRunResponse,
    summary="Run and save a grid simulation",
    response_description="Simulation result with energy balance and objective value.",
)
async def save_simulation(
    body: SimulationRunRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationRunResponse:
    """Run a PyPSA AC power flow simulation and persist the result.

    Uses the same PyPSA execution path as POST /preview (LP, no unit-commitment),
    then writes the request and result to the database.
    """
    return await service.save(body)


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


@router.get(
    "/solvers",
    response_model=list[SimulationSolverInfo],
    summary="List supported solvers and availability",
    response_description="Array of solver names with availability and optional reason.",
)
async def list_solvers(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> list[SimulationSolverInfo]:
    """Return supported solver names and whether they are available on the backend."""
    return await service.list_solvers()


@router.post(
    "/preview",
    response_model=SimulationRunResponse,
    summary="Preview a simulation without saving",
    response_description="Simulation result — NOT persisted to the database.",
)
async def preview_simulation(
    body: SimulationRunRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationRunResponse:
    """Run a PyPSA AC power flow simulation without persisting the result.

    Identical request body to POST /run.
    The response has the same format but the result is NOT stored in the database
    (id and request_id are generated on the fly and discarded after the response).

    Used by the frontend live-preview mode — safe to call on every parameter change.
    """
    return await service.preview(body)


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
    )
    return await service.save(run_request)


@router.delete(
    "/{simulation_id}",
    status_code=204,
    response_class=Response,
    summary="Delete a simulation",
    responses={404: {"description": "Simulation not found."}},
)
async def delete_simulation(
    simulation_id: uuid.UUID,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> Response:
    """Permanently delete a simulation and its associated request."""
    deleted = await service.delete(simulation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return Response(status_code=204)


@router.patch(
    "/{simulation_id}/rename",
    response_model=SimulationRunResponse,
    summary="Rename a simulation scenario",
    responses={404: {"description": "Simulation not found."}},
)
async def rename_simulation(
    simulation_id: uuid.UUID,
    body: SimulationRenameRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationRunResponse:
    """Set or update the display name of a past simulation."""
    result = await service.rename(simulation_id, body.name)
    if result is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return result


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
