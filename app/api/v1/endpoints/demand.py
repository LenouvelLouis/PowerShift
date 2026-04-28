"""Demand CRUD endpoints — GET, POST, PUT, DELETE /api/v1/demands.

Includes sub-resource endpoints for custom hourly load profiles:
  POST   /demands/{demand_id}/profile  — upload CSV
  GET    /demands/{demand_id}/profile  — retrieve stored profile
  DELETE /demands/{demand_id}/profile  — remove custom profile
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app.api.v1.dependencies import get_custom_profile_repository, get_demand_repository
from app.api.v1.schemas.demand_schema import CustomProfileResponse, DemandCreate, DemandResponse, DemandUpdate
from app.api.v1.schemas.pagination import PaginatedResponse
from app.domain.entities.demand.base_demand import BaseDemand
from app.infrastructure.db.repositories.custom_profile_repository_impl import CustomProfileRepositoryImpl
from app.infrastructure.db.repositories.demand_repository_impl import DemandRepositoryImpl

router = APIRouter(prefix="/demands", tags=["Demands"])

_404 = {404: {"description": "Demand not found."}}

# Valid profile lengths: 24h (daily), 168h (weekly), 8760h (yearly)
_VALID_PROFILE_LENGTHS = {24, 168, 8760}


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
    response_model=PaginatedResponse[DemandResponse],
    summary="List demand nodes (paginated)",
    response_description="Paginated list of demand components.",
)
async def list_demands(
    repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    size: int = Query(default=20, ge=1, le=100, description="Items per page."),
) -> PaginatedResponse[DemandResponse]:
    """Return a paginated list of demand components."""
    offset = (page - 1) * size
    items = [_to_response(d) for d in await repo.get_paginated(offset=offset, limit=size)]
    total = await repo.count()
    return PaginatedResponse[DemandResponse].build(items=items, total=total, page=page, size=size)


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
    now = datetime.now(UTC)
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

    now = datetime.now(UTC)
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


# ── Custom load profile sub-resource ────────────────────────────────────────


def _parse_csv_profile(raw_bytes: bytes) -> list[float]:
    """Parse a CSV file with columns ``hour`` and ``load_factor``.

    Returns a list of load factors (floats 0.0-1.0) ordered by hour.
    Raises ``HTTPException(422)`` on any validation error.
    """
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="CSV file must be UTF-8 encoded.")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or set(reader.fieldnames) < {"hour", "load_factor"}:
        raise HTTPException(
            status_code=422,
            detail="CSV must have columns 'hour' and 'load_factor'.",
        )

    rows: dict[int, float] = {}
    for line_no, row in enumerate(reader, start=2):
        try:
            hour = int(row["hour"])
            load_factor = float(row["load_factor"])
        except (ValueError, KeyError):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid data on line {line_no}: hour and load_factor must be numeric.",
            )
        if not 0.0 <= load_factor <= 1.0:
            raise HTTPException(
                status_code=422,
                detail=f"load_factor on line {line_no} is {load_factor}; must be between 0.0 and 1.0.",
            )
        if hour in rows:
            raise HTTPException(status_code=422, detail=f"Duplicate hour {hour} on line {line_no}.")
        rows[hour] = load_factor

    length = len(rows)
    if length not in _VALID_PROFILE_LENGTHS:
        raise HTTPException(
            status_code=422,
            detail=f"Profile has {length} rows; must be one of {sorted(_VALID_PROFILE_LENGTHS)}.",
        )

    # Verify hour values are contiguous 0..N-1
    expected_hours = set(range(length))
    if set(rows.keys()) != expected_hours:
        raise HTTPException(
            status_code=422,
            detail=f"Hour column must contain contiguous values 0..{length - 1}.",
        )

    return [rows[h] for h in range(length)]


@router.post(
    "/{demand_id}/profile",
    response_model=CustomProfileResponse,
    status_code=201,
    summary="Upload a custom hourly load profile (CSV)",
    response_description="The parsed and stored custom profile.",
    responses=_404,
)
async def upload_profile(
    demand_id: uuid.UUID,
    file: UploadFile,
    demand_repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
    profile_repo: Annotated[CustomProfileRepositoryImpl, Depends(get_custom_profile_repository)],
) -> CustomProfileResponse:
    """Upload a CSV with columns ``hour`` (0-based) and ``load_factor`` (0.0-1.0).

    The number of rows must be 24, 168, or 8760.
    Replaces any previously stored custom profile for this demand.
    """
    demand = await demand_repo.get_by_id(str(demand_id))
    if demand is None:
        raise HTTPException(status_code=404, detail="Demand not found")

    raw = await file.read()
    profile_data = _parse_csv_profile(raw)
    row = await profile_repo.upsert(demand_id, profile_data)
    return CustomProfileResponse(
        demand_id=row.demand_id,
        profile_data=row.profile_data,
        created_at=row.created_at,
    )


@router.get(
    "/{demand_id}/profile",
    response_model=CustomProfileResponse | None,
    summary="Get the custom load profile for a demand",
    response_description="The stored custom profile, or null if none exists.",
    responses=_404,
)
async def get_profile(
    demand_id: uuid.UUID,
    demand_repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
    profile_repo: Annotated[CustomProfileRepositoryImpl, Depends(get_custom_profile_repository)],
) -> CustomProfileResponse | None:
    """Return the custom hourly load profile for a demand, or null."""
    demand = await demand_repo.get_by_id(str(demand_id))
    if demand is None:
        raise HTTPException(status_code=404, detail="Demand not found")

    row = await profile_repo.get_by_demand_id(demand_id)
    if row is None:
        return None
    return CustomProfileResponse(
        demand_id=row.demand_id,
        profile_data=row.profile_data,
        created_at=row.created_at,
    )


@router.delete(
    "/{demand_id}/profile",
    status_code=204,
    response_class=Response,
    summary="Delete the custom load profile for a demand",
    response_description="No content — the custom profile was removed.",
    responses=_404,
)
async def delete_profile(
    demand_id: uuid.UUID,
    demand_repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
    profile_repo: Annotated[CustomProfileRepositoryImpl, Depends(get_custom_profile_repository)],
) -> Response:
    """Remove the custom profile, reverting to the default built-in profile."""
    demand = await demand_repo.get_by_id(str(demand_id))
    if demand is None:
        raise HTTPException(status_code=404, detail="Demand not found")

    await profile_repo.delete_by_demand_id(demand_id)
    return Response(status_code=204)
