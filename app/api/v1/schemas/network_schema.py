"""Pydantic v2 schemas for network components (transformers and cables)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities.base_component import ComponentStatus


class NetworkResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    type: str                          # "transformer" | "cable"
    voltage_kv: float
    capacity_mva: float
    losses_kw: float | None
    # Transformer-specific
    voltage_hv_kv: float | None
    voltage_lv_kv: float | None
    # Cable-specific
    length_km: float | None
    resistance_ohm_per_km: float | None
    reactance_ohm_per_km: float | None
    status: ComponentStatus
    unit: str
    description: str = Field(default="", description="Free-text description.")
    created_at: datetime
    updated_at: datetime


class NetworkCreate(BaseModel):
    """Request body for POST /api/v1/network."""

    name: str
    type: str                          # "transformer" | "cable"
    voltage_kv: float
    capacity_mva: float = 0.0
    losses_kw: float | None = None
    # Transformer-specific
    voltage_hv_kv: float | None = None
    voltage_lv_kv: float | None = None
    # Cable-specific
    length_km: float | None = None
    resistance_ohm_per_km: float | None = None
    reactance_ohm_per_km: float | None = None
    status: ComponentStatus = ComponentStatus.ACTIVE
    unit: str = "MVA"
    description: str = ""


class NetworkUpdate(BaseModel):
    """Request body for PUT /api/v1/network/{id} — all fields optional."""

    name: str | None = None
    voltage_kv: float | None = None
    capacity_mva: float | None = None
    losses_kw: float | None = None
    voltage_hv_kv: float | None = None
    voltage_lv_kv: float | None = None
    length_km: float | None = None
    resistance_ohm_per_km: float | None = None
    reactance_ohm_per_km: float | None = None
    status: ComponentStatus | None = None
    unit: str | None = None
    description: str | None = None
