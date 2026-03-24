"""Supply CRUD endpoints — GET, POST, PUT, DELETE /api/v1/supplies."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.api.v1.dependencies import get_supply_repository
from app.api.v1.schemas.supply_schema import SupplyCreate, SupplyResponse, SupplyUpdate
from app.domain.entities.supply.base_supply import BaseSupply
from app.infrastructure.db.repositories.supply_repository_impl import SupplyRepositoryImpl

router = APIRouter(prefix="/supplies", tags=["Supplies"])

_404 = {404: {"description": "Supply not found."}}


def _to_response(supply: BaseSupply) -> SupplyResponse:
    return SupplyResponse(
        id=supply.id,
        name=supply.name,
        type=supply.get_type(),
        capacity_mw=supply.capacity_mw,
        efficiency=supply.efficiency,
        status=supply.status,
        unit=supply.unit,
        description=supply.description or "",
        carrier=supply.get_carrier(),
        created_at=supply.created_at,
        updated_at=supply.updated_at,
    )


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[SupplyResponse],
    summary="List all supply sources",
    response_description="Array of all supply components.",
)
async def list_supplies(
    repo: Annotated[SupplyRepositoryImpl, Depends(get_supply_repository)],
) -> list[SupplyResponse]:
    """Return every supply component stored in the database."""
    return [_to_response(s) for s in await repo.get_all()]


@router.get(
    "/{supply_id}",
    response_model=SupplyResponse,
    summary="Get a supply source by ID",
    response_description="The requested supply component.",
    responses=_404,
)
async def get_supply(
    supply_id: uuid.UUID,
    repo: Annotated[SupplyRepositoryImpl, Depends(get_supply_repository)],
) -> SupplyResponse:
    """Return a single supply component identified by its UUID."""
    supply = await repo.get_by_id(str(supply_id))
    if supply is None:
        raise HTTPException(status_code=404, detail="Supply not found")
    return _to_response(supply)


@router.post(
    "",
    response_model=SupplyResponse,
    status_code=201,
    summary="Create a supply source",
    response_description="The newly created supply component.",
)
async def create_supply(
    body: SupplyCreate,
    repo: Annotated[SupplyRepositoryImpl, Depends(get_supply_repository)],
) -> SupplyResponse:
    """Create a new supply component.

    Valid `type` values: `wind_turbine`, `solar_panel`, `nuclear_plant`.
    """
    now = datetime.now(timezone.utc)
    entity = SupplyRepositoryImpl.build_entity(
        body.type,
        id=uuid.uuid4(),
        name=body.name,
        capacity_mw=body.capacity_mw,
        efficiency=body.efficiency,
        status=body.status,
        unit=body.unit,
        description=body.description,
        created_at=now,
        updated_at=now,
    )
    saved = await repo.create(entity)
    return _to_response(saved)


@router.put(
    "/{supply_id}",
    response_model=SupplyResponse,
    summary="Update a supply source",
    response_description="The updated supply component.",
    responses=_404,
)
async def update_supply(
    supply_id: uuid.UUID,
    body: SupplyUpdate,
    repo: Annotated[SupplyRepositoryImpl, Depends(get_supply_repository)],
) -> SupplyResponse:
    """Partially update a supply component — only the fields you provide are changed."""
    existing = await repo.get_by_id(str(supply_id))
    if existing is None:
        raise HTTPException(status_code=404, detail="Supply not found")

    now = datetime.now(timezone.utc)
    updated = SupplyRepositoryImpl.build_entity(
        existing.get_type(),
        id=existing.id,
        name=body.name if body.name is not None else existing.name,
        capacity_mw=body.capacity_mw if body.capacity_mw is not None else existing.capacity_mw,
        efficiency=body.efficiency if body.efficiency is not None else existing.efficiency,
        status=body.status if body.status is not None else existing.status,
        unit=body.unit if body.unit is not None else existing.unit,
        description=body.description if body.description is not None else existing.description,
        created_at=existing.created_at,
        updated_at=now,
    )

    saved = await repo.update(str(supply_id), updated)
    return _to_response(saved)  # type: ignore[arg-type]


@router.delete(
    "/{supply_id}",
    status_code=204,
    response_class=Response,
    summary="Delete a supply source",
    response_description="No content — the component was deleted.",
    responses=_404,
)
async def delete_supply(
    supply_id: uuid.UUID,
    repo: Annotated[SupplyRepositoryImpl, Depends(get_supply_repository)],
) -> Response:
    """Permanently delete a supply component by its UUID."""
    deleted = await repo.delete(str(supply_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Supply not found")
    return Response(status_code=204)
