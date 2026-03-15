"""Pydantic v2 schemas for supply components."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.entities.base_component import ComponentStatus


class SupplyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    type: str
    capacity_mw: float
    efficiency: float
    status: ComponentStatus
    unit: str
    description: str
    carrier: str
    created_at: datetime
    updated_at: datetime


class SupplyCreate(BaseModel):
    """Request body for POST /api/v1/supplies."""

    name: str
    type: str                          # "wind_turbine" | "solar_panel" | "nuclear_plant"
    capacity_mw: float
    efficiency: float = 1.0
    status: ComponentStatus = ComponentStatus.ACTIVE
    unit: str = "MW"
    description: str = ""


class SupplyUpdate(BaseModel):
    """Request body for PUT /api/v1/supplies/{id} — all fields optional."""

    name: str | None = None
    capacity_mw: float | None = None
    efficiency: float | None = None
    status: ComponentStatus | None = None
    unit: str | None = None
    description: str | None = None
