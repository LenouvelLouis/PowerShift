"""Simulation endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_simulation_service
from app.api.v1.schemas.simulation_schema import (
    SimulationRequest,
    SimulationResponse,
)
from app.application.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.post("/run", response_model=SimulationResponse)
async def run_simulation(
    body: SimulationRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationResponse:
    """Run a PyPSA grid simulation for the given number of hours."""
    result = await service.run(snapshot_hours=body.snapshot_hours)
    return SimulationResponse(
        total_supply_mwh=result.total_supply_mwh,
        total_demand_mwh=result.total_demand_mwh,
        balance_mwh=result.balance_mwh,
        status=result.status,
    )
