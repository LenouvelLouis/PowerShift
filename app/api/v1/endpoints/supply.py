"""Supply endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.dependencies import get_supply_repository
from app.api.v1.schemas.supply_schema import SupplyResponse
from app.domain.entities.supply.base_supply import BaseSupply
from app.infrastructure.db.repositories.supply_repository_impl import (
    SupplyRepositoryImpl,
)

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
