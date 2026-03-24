"""Network component CRUD endpoints — GET, POST, PUT, DELETE /api/v1/network."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.api.v1.dependencies import get_network_repository
from app.api.v1.schemas.network_schema import NetworkCreate, NetworkResponse, NetworkUpdate
from app.domain.entities.base_component import ComponentStatus
from app.domain.entities.network.base_network import BaseNetwork
from app.domain.entities.network.cable import Cable
from app.domain.entities.network.transformer import Transformer
from app.infrastructure.db.repositories.network_repository_impl import NetworkRepositoryImpl

router = APIRouter(prefix="/network", tags=["Network"])

_404 = {404: {"description": "Network component not found."}}


def _to_response(component: BaseNetwork) -> NetworkResponse:
    voltage_hv_kv = component.voltage_hv_kv if isinstance(component, Transformer) else None
    voltage_lv_kv = component.voltage_lv_kv if isinstance(component, Transformer) else None
    length_km = component.length_km if isinstance(component, Cable) else None
    resistance_ohm_per_km = component.resistance_ohm_per_km if isinstance(component, Cable) else None
    reactance_ohm_per_km = component.reactance_ohm_per_km if isinstance(component, Cable) else None

    return NetworkResponse(
        id=component.id,
        name=component.name,
        type=component.get_network_type(),
        voltage_kv=component.voltage_kv,
        capacity_mva=component.capacity_mva,
        losses_kw=component.losses_kw,
        voltage_hv_kv=voltage_hv_kv,
        voltage_lv_kv=voltage_lv_kv,
        length_km=length_km,
        resistance_ohm_per_km=resistance_ohm_per_km,
        reactance_ohm_per_km=reactance_ohm_per_km,
        status=component.status,
        unit=component.unit,
        description=component.description or "",
        created_at=component.created_at,
        updated_at=component.updated_at,
    )


def _create_body_to_entity(body: NetworkCreate) -> BaseNetwork:
    """Map a NetworkCreate schema to the appropriate domain entity."""
    now = datetime.now(timezone.utc)
    common = dict(
        id=uuid.uuid4(),
        name=body.name,
        voltage_kv=body.voltage_kv,
        capacity_mva=body.capacity_mva,
        losses_kw=body.losses_kw,
        status=body.status,
        unit=body.unit,
        description=body.description,
        created_at=now,
        updated_at=now,
    )
    if body.type == "transformer":
        return Transformer(
            **common,
            voltage_hv_kv=body.voltage_hv_kv or body.voltage_kv,
            voltage_lv_kv=body.voltage_lv_kv or 0.4,
        )
    return Cable(
        **common,
        length_km=body.length_km or 0.0,
        resistance_ohm_per_km=body.resistance_ohm_per_km or 0.0,
        reactance_ohm_per_km=body.reactance_ohm_per_km or 0.0,
    )


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[NetworkResponse],
    summary="List all network components",
    response_description="Array of all network components (transformers and cables).",
)
async def list_network(
    repo: Annotated[NetworkRepositoryImpl, Depends(get_network_repository)],
) -> list[NetworkResponse]:
    """Return every network component stored in the database."""
    return [_to_response(c) for c in await repo.get_all()]


@router.get(
    "/{component_id}",
    response_model=NetworkResponse,
    summary="Get a network component by ID",
    response_description="The requested network component.",
    responses=_404,
)
async def get_network_component(
    component_id: uuid.UUID,
    repo: Annotated[NetworkRepositoryImpl, Depends(get_network_repository)],
) -> NetworkResponse:
    """Return a single network component identified by its UUID."""
    component = await repo.get_by_id(str(component_id))
    if component is None:
        raise HTTPException(status_code=404, detail="Network component not found")
    return _to_response(component)


@router.post(
    "",
    response_model=NetworkResponse,
    status_code=201,
    summary="Create a network component",
    response_description="The newly created network component.",
)
async def create_network_component(
    body: NetworkCreate,
    repo: Annotated[NetworkRepositoryImpl, Depends(get_network_repository)],
) -> NetworkResponse:
    """Create a new network component.

    Valid `type` values: `transformer`, `cable`.

    - **transformer** — requires `voltage_hv_kv`, `voltage_lv_kv`, `capacity_mva`.
    - **cable** — requires `length_km`, `resistance_ohm_per_km`, `reactance_ohm_per_km`.
    """
    entity = _create_body_to_entity(body)
    saved = await repo.create(entity)
    return _to_response(saved)


@router.put(
    "/{component_id}",
    response_model=NetworkResponse,
    summary="Update a network component",
    response_description="The updated network component.",
    responses=_404,
)
async def update_network_component(
    component_id: uuid.UUID,
    body: NetworkUpdate,
    repo: Annotated[NetworkRepositoryImpl, Depends(get_network_repository)],
) -> NetworkResponse:
    """Partially update a network component — only the fields you provide are changed."""
    existing = await repo.get_by_id(str(component_id))
    if existing is None:
        raise HTTPException(status_code=404, detail="Network component not found")

    # Build an updated entity by merging existing values with the patch
    now = datetime.now(timezone.utc)
    common = dict(
        id=existing.id,
        name=body.name if body.name is not None else existing.name,
        voltage_kv=body.voltage_kv if body.voltage_kv is not None else existing.voltage_kv,
        capacity_mva=body.capacity_mva if body.capacity_mva is not None else existing.capacity_mva,
        losses_kw=body.losses_kw if body.losses_kw is not None else existing.losses_kw,
        status=body.status if body.status is not None else existing.status,
        unit=body.unit if body.unit is not None else existing.unit,
        description=body.description if body.description is not None else existing.description,
        created_at=existing.created_at,
        updated_at=now,
    )

    if isinstance(existing, Transformer):
        updated: BaseNetwork = Transformer(
            **common,
            voltage_hv_kv=body.voltage_hv_kv if body.voltage_hv_kv is not None else existing.voltage_hv_kv,
            voltage_lv_kv=body.voltage_lv_kv if body.voltage_lv_kv is not None else existing.voltage_lv_kv,
        )
    else:
        assert isinstance(existing, Cable)
        updated = Cable(
            **common,
            length_km=body.length_km if body.length_km is not None else existing.length_km,
            resistance_ohm_per_km=body.resistance_ohm_per_km if body.resistance_ohm_per_km is not None else existing.resistance_ohm_per_km,
            reactance_ohm_per_km=body.reactance_ohm_per_km if body.reactance_ohm_per_km is not None else existing.reactance_ohm_per_km,
        )

    saved = await repo.update(str(component_id), updated)
    return _to_response(saved)  # type: ignore[arg-type]


@router.delete(
    "/{component_id}",
    status_code=204,
    response_class=Response,
    summary="Delete a network component",
    response_description="No content — the component was deleted.",
    responses=_404,
)
async def delete_network_component(
    component_id: uuid.UUID,
    repo: Annotated[NetworkRepositoryImpl, Depends(get_network_repository)],
) -> Response:
    """Permanently delete a network component by its UUID."""
    deleted = await repo.delete(str(component_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Network component not found")
    return Response(status_code=204)
