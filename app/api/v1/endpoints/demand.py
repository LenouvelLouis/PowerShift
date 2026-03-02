"""Demand endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.dependencies import get_demand_repository
from app.api.v1.schemas.demand_schema import DemandResponse
from app.domain.entities.demand.base_demand import BaseDemand
from app.infrastructure.db.repositories.demand_repository_impl import (
    DemandRepositoryImpl,
)

router = APIRouter(prefix="/demands", tags=["Demands"])


def _to_response(demand: BaseDemand) -> DemandResponse:
    return DemandResponse(
        id=demand.id,
        name=demand.name,
        type=demand.get_type(),
        load_mw=demand.load_mw,
        status=demand.status,
        unit=demand.unit,
        description=demand.description,
        created_at=demand.created_at,
        updated_at=demand.updated_at,
    )


@router.get("", response_model=list[DemandResponse])
async def list_demands(
    repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
) -> list[DemandResponse]:
    return [_to_response(d) for d in await repo.get_all()]


@router.get("/{demand_id}", response_model=DemandResponse)
async def get_demand(
    demand_id: str,
    repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
) -> DemandResponse:
    demand = await repo.get_by_id(demand_id)
    if demand is None:
        raise HTTPException(status_code=404, detail="Demand not found")
    return _to_response(demand)
