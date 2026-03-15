"""Demand CRUD endpoints — GET, POST, PUT, DELETE /api/v1/demands."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.api.v1.dependencies import get_demand_repository
from app.api.v1.schemas.demand_schema import DemandCreate, DemandResponse, DemandUpdate
from app.domain.entities.demand.base_demand import BaseDemand
from app.infrastructure.db.repositories.demand_repository_impl import DemandRepositoryImpl

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


# ── Endpoints ────────────────────────────────────────────────────────────────

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


@router.post("", response_model=DemandResponse, status_code=201)
async def create_demand(
    body: DemandCreate,
    repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
) -> DemandResponse:
    """Create a new demand component."""
    now = datetime.now(timezone.utc)
    entity = DemandRepositoryImpl.build_entity(
        body.type,
        id=uuid.uuid4(),
        name=body.name,
        load_mw=body.load_mw,
        status=body.status,
        unit=body.unit,
        description=body.description,
        created_at=now,
        updated_at=now,
    )
    saved = await repo.create(entity)
    return _to_response(saved)


@router.put("/{demand_id}", response_model=DemandResponse)
async def update_demand(
    demand_id: str,
    body: DemandUpdate,
    repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
) -> DemandResponse:
    """Update an existing demand component (partial update — only provided fields change)."""
    existing = await repo.get_by_id(demand_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Demand not found")

    now = datetime.now(timezone.utc)
    updated = DemandRepositoryImpl.build_entity(
        existing.get_type(),
        id=existing.id,
        name=body.name if body.name is not None else existing.name,
        load_mw=body.load_mw if body.load_mw is not None else existing.load_mw,
        status=body.status if body.status is not None else existing.status,
        unit=body.unit if body.unit is not None else existing.unit,
        description=body.description if body.description is not None else existing.description,
        created_at=existing.created_at,
        updated_at=now,
    )

    saved = await repo.update(demand_id, updated)
    return _to_response(saved)  # type: ignore[arg-type]


@router.delete("/{demand_id}", status_code=204, response_class=Response)
async def delete_demand(
    demand_id: str,
    repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
) -> Response:
    """Delete a demand component by UUID."""
    deleted = await repo.delete(demand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Demand not found")
    return Response(status_code=204)
