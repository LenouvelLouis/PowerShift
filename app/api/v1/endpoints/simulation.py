"""Simulation endpoint."""

from __future__ import annotations

import io
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse

from app.api.v1.dependencies import get_simulation_service
from app.api.v1.schemas.pagination import PaginatedResponse
from app.api.v1.schemas.simulation_schema import (
    SimulationListItem,
    SimulationRenameRequest,
    SimulationRunRequest,
    SimulationRunResponse,
    SimulationScenarioExport,
    SimulationSolverInfo,
)
from app.application.services.export_service import ExportService
from app.application.services.simulation_service import SimulationService
from app.domain.simulation.exceptions import WeatherDataEmptyError

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
    try:
        return await service.save(body)
    except WeatherDataEmptyError as exc:
        raise HTTPException(
            status_code=422,
            detail={"detail": str(exc), "code": "ERR_WEATHER_DATA_EMPTY"},
        ) from exc


@router.get(
    "",
    response_model=PaginatedResponse[SimulationListItem],
    summary="List past simulations (paginated)",
    response_description="Paginated list of simulation summaries ordered by creation date.",
)
async def list_simulations(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    size: int = Query(default=20, ge=1, le=100, description="Items per page."),
) -> PaginatedResponse[SimulationListItem]:
    """Return a paginated list of simulation summaries."""
    offset = (page - 1) * size
    items, total = await service.list_paginated(offset=offset, limit=size)
    return PaginatedResponse[SimulationListItem].build(items=items, total=total, page=page, size=size)


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
    try:
        return await service.preview(body)
    except WeatherDataEmptyError as exc:
        raise HTTPException(
            status_code=422,
            detail={"detail": str(exc), "code": "ERR_WEATHER_DATA_EMPTY"},
        ) from exc


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
        optimization_objective=body.optimization_objective,
        start_date=body.start_date,
        end_date=body.end_date,
        supply_ids=body.supply_ids,
        demand_ids=body.demand_ids,
        network_ids=body.network_ids,
        pypsa_params=body.pypsa_params,
        hourly_load_overrides=body.hourly_load_overrides,
    )
    try:
        return await service.save(run_request)
    except WeatherDataEmptyError as exc:
        raise HTTPException(
            status_code=422,
            detail={"detail": str(exc), "code": "ERR_WEATHER_DATA_EMPTY"},
        ) from exc


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
    "/{simulation_id}/export/csv",
    summary="Export simulation results as CSV",
    response_description="CSV file with time-series data and KPI summary.",
    responses={404: {"description": "Simulation not found."}},
)
async def export_csv(
    simulation_id: uuid.UUID,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> StreamingResponse:
    """Return a downloadable CSV file containing the simulation time-series data."""
    result = await service.get_by_id(simulation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    csv_text = ExportService.build_csv(
        simulation_id=result.id,
        status=result.status,
        solver=result.solver,
        total_supply_mwh=result.total_supply_mwh,
        total_demand_mwh=result.total_demand_mwh,
        balance_mwh=result.balance_mwh,
        result_json=result.result_json,
        created_at=result.created_at,
        start_date=str(result.start_date) if result.start_date else None,
        end_date=str(result.end_date) if result.end_date else None,
    )
    return StreamingResponse(
        io.StringIO(csv_text),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="simulation_{simulation_id}.csv"'},
    )


@router.get(
    "/{simulation_id}/export/pdf",
    summary="Export simulation results as PDF",
    response_description="PDF report with simulation metadata and KPI summary.",
    responses={404: {"description": "Simulation not found."}},
)
async def export_pdf(
    simulation_id: uuid.UUID,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> StreamingResponse:
    """Return a downloadable PDF report with simulation metadata and KPI tables."""
    result = await service.get_by_id(simulation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    pdf_bytes = ExportService.build_pdf(
        simulation_id=result.id,
        status=result.status,
        solver=result.solver,
        total_supply_mwh=result.total_supply_mwh,
        total_demand_mwh=result.total_demand_mwh,
        balance_mwh=result.balance_mwh,
        objective_value=result.objective_value,
        result_json=result.result_json,
        created_at=result.created_at,
        start_date=str(result.start_date) if result.start_date else None,
        end_date=str(result.end_date) if result.end_date else None,
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="simulation_{simulation_id}.pdf"'},
    )


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
