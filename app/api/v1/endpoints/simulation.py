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
)
from app.application.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.post("/run", response_model=SimulationRunResponse)
async def run_simulation(
    body: SimulationRunRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationRunResponse:
    """Run a PyPSA grid simulation and persist the result."""
    return await service.run(body)


@router.get("", response_model=list[SimulationListItem])
async def list_simulations(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> list[SimulationListItem]:
    """List all past simulation results."""
    return await service.list()


@router.get("/{simulation_id}", response_model=SimulationRunResponse)
async def get_simulation(
    simulation_id: uuid.UUID,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationRunResponse:
    """Get a simulation result by ID."""
    result = await service.get_by_id(simulation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return result
