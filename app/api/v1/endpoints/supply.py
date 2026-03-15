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


def _to_response(supply: BaseSupply) -> SupplyResponse:
    return SupplyResponse(
        id=supply.id,
        name=supply.name,
        type=supply.get_type(),
        capacity_mw=supply.capacity_mw,
        efficiency=supply.efficiency,
        status=supply.status,
        unit=supply.unit,
        description=supply.description,
        carrier=supply.get_carrier(),
        created_at=supply.created_at,
        updated_at=supply.updated_at,
    )


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("", response_model=list[SupplyResponse])
async def list_supplies(
    repo: Annotated[SupplyRepositoryImpl, Depends(get_supply_repository)],
) -> list[SupplyResponse]:
    return [_to_response(s) for s in await repo.get_all()]


@router.get("/{supply_id}", response_model=SupplyResponse)
async def get_supply(
    supply_id: str,
    repo: Annotated[SupplyRepositoryImpl, Depends(get_supply_repository)],
) -> SupplyResponse:
    supply = await repo.get_by_id(supply_id)
    if supply is None:
        raise HTTPException(status_code=404, detail="Supply not found")
    return _to_response(supply)


@router.post("", response_model=SupplyResponse, status_code=201)
async def create_supply(
    body: SupplyCreate,
    repo: Annotated[SupplyRepositoryImpl, Depends(get_supply_repository)],
) -> SupplyResponse:
    """Create a new supply component."""
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


@router.put("/{supply_id}", response_model=SupplyResponse)
async def update_supply(
    supply_id: str,
    body: SupplyUpdate,
    repo: Annotated[SupplyRepositoryImpl, Depends(get_supply_repository)],
) -> SupplyResponse:
    """Update an existing supply component (partial update — only provided fields change)."""
    existing = await repo.get_by_id(supply_id)
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

    saved = await repo.update(supply_id, updated)
    return _to_response(saved)  # type: ignore[arg-type]


@router.delete("/{supply_id}", status_code=204, response_class=Response)
async def delete_supply(
    supply_id: str,
    repo: Annotated[SupplyRepositoryImpl, Depends(get_supply_repository)],
) -> Response:
    """Delete a supply component by UUID."""
    deleted = await repo.delete(supply_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Supply not found")
    return Response(status_code=204)
