"""GET /api/v1/referential endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_referential_service
from app.api.v1.schemas.demand_schema import DemandResponse
from app.api.v1.schemas.network_schema import NetworkResponse
from app.api.v1.schemas.referential_schema import ReferentialResponse
from app.api.v1.schemas.supply_schema import SupplyResponse
from app.application.dtos.demand_dto import DemandDTO
from app.application.dtos.network_dto import NetworkDTO
from app.application.dtos.supply_dto import SupplyDTO
from app.application.services.referential_service import ReferentialService

router = APIRouter(prefix="/referential", tags=["Referential"])


def _supply_dto_to_response(dto: SupplyDTO) -> SupplyResponse:
    return SupplyResponse(
        id=dto.id,
        name=dto.name,
        type=dto.type,
        capacity_mw=dto.capacity_mw,
        efficiency=dto.efficiency,
        status=dto.status,
        unit=dto.unit,
        description=dto.description,
        carrier=dto.carrier,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


def _demand_dto_to_response(dto: DemandDTO) -> DemandResponse:
    return DemandResponse(
        id=dto.id,
        name=dto.name,
        type=dto.type,
        load_mw=dto.load_mw,
        status=dto.status,
        unit=dto.unit,
        description=dto.description,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


def _network_dto_to_response(dto: NetworkDTO) -> NetworkResponse:
    return NetworkResponse(
        id=dto.id,
        name=dto.name,
        type=dto.type,
        voltage_kv=dto.voltage_kv,
        capacity_mva=dto.capacity_mva,
        losses_kw=dto.losses_kw,
        voltage_hv_kv=dto.voltage_hv_kv,
        voltage_lv_kv=dto.voltage_lv_kv,
        length_km=dto.length_km,
        resistance_ohm_per_km=dto.resistance_ohm_per_km,
        reactance_ohm_per_km=dto.reactance_ohm_per_km,
        status=dto.status,
        unit=dto.unit,
        description=dto.description,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.get(
    "",
    response_model=ReferentialResponse,
    summary="Get full referential",
    response_description="All supplies, demands, and network components in one response.",
)
async def get_referential(
    service: Annotated[ReferentialService, Depends(get_referential_service)],
) -> ReferentialResponse:
    """Return all supply, demand, and network components in a single call.

    Useful to populate a simulation request with available asset IDs.
    """
    dto = await service.get_referential()
    return ReferentialResponse(
        supplies=[_supply_dto_to_response(s) for s in dto.supplies],
        demands=[_demand_dto_to_response(d) for d in dto.demands],
        network=[_network_dto_to_response(n) for n in dto.network],
    )
