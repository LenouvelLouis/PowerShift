"""Pydantic v2 schemas for demand components."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.entities.base_component import ComponentStatus


class DemandResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    type: str
    load_mw: float
    status: ComponentStatus
    unit: str
    description: str
    created_at: datetime
    updated_at: datetime


class DemandCreate(BaseModel):
    """Request body for POST /api/v1/demands."""

    name: str
    type: str                          # "house" | "electric_vehicle"
    load_mw: float
    status: ComponentStatus = ComponentStatus.ACTIVE
    unit: str = "MW"
    description: str = ""


class DemandUpdate(BaseModel):
    """Request body for PUT /api/v1/demands/{id} — all fields optional."""

    name: str | None = None
    load_mw: float | None = None
    status: ComponentStatus | None = None
    unit: str | None = None
    description: str | None = None
