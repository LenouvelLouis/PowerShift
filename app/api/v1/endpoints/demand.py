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

_404 = {404: {"description": "Demand not found."}}


def _to_response(demand: BaseDemand) -> DemandResponse:
    return DemandResponse(
        id=demand.id,
        name=demand.name,
        type=demand.get_type(),
        load_mw=demand.load_mw,
        status=demand.status,
        unit=demand.unit,
        description=demand.description or "",
        created_at=demand.created_at,
        updated_at=demand.updated_at,
    )


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[DemandResponse],
    summary="List all demand nodes",
    response_description="Array of all demand components.",
)
async def list_demands(
    repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
) -> list[DemandResponse]:
    """Return every demand component stored in the database."""
    return [_to_response(d) for d in await repo.get_all()]


@router.get(
    "/{demand_id}",
    response_model=DemandResponse,
    summary="Get a demand node by ID",
    response_description="The requested demand component.",
    responses=_404,
)
async def get_demand(
    demand_id: uuid.UUID,
    repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
) -> DemandResponse:
    """Return a single demand component identified by its UUID."""
    demand = await repo.get_by_id(str(demand_id))
    if demand is None:
        raise HTTPException(status_code=404, detail="Demand not found")
    return _to_response(demand)


@router.post(
    "",
    response_model=DemandResponse,
    status_code=201,
    summary="Create a demand node",
    response_description="The newly created demand component.",
)
async def create_demand(
    body: DemandCreate,
    repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
) -> DemandResponse:
    """Create a new demand component.

    Valid `type` values: `house`, `electric_vehicle`.
    """
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


@router.put(
    "/{demand_id}",
    response_model=DemandResponse,
    summary="Update a demand node",
    response_description="The updated demand component.",
    responses=_404,
)
async def update_demand(
    demand_id: uuid.UUID,
    body: DemandUpdate,
    repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
) -> DemandResponse:
    """Partially update a demand component — only the fields you provide are changed."""
    existing = await repo.get_by_id(str(demand_id))
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

    saved = await repo.update(str(demand_id), updated)
    return _to_response(saved)  # type: ignore[arg-type]


@router.delete(
    "/{demand_id}",
    status_code=204,
    response_class=Response,
    summary="Delete a demand node",
    response_description="No content — the component was deleted.",
    responses=_404,
)
async def delete_demand(
    demand_id: uuid.UUID,
    repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
) -> Response:
    """Permanently delete a demand component by its UUID."""
    deleted = await repo.delete(str(demand_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Demand not found")
    return Response(status_code=204)
