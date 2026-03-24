"""Pydantic v2 schemas for supply components."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities.base_component import ComponentStatus


class SupplyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID = Field(description="Unique identifier of the supply component.")
    name: str = Field(description="Human-readable name.")
    type: str = Field(description="Component type: `wind_turbine`, `solar_panel`, or `nuclear_plant`.")
    capacity_mw: float = Field(description="Nominal installed capacity in megawatts.")
    efficiency: float = Field(description="Conversion efficiency, between 0.0 and 1.0.")
    status: ComponentStatus = Field(description="Operational status.")
    unit: str = Field(description="Unit of the capacity field (typically `MW`).")
    description: str = Field(default="", description="Free-text description.")
    carrier: str = Field(description="Energy carrier used by PyPSA: `wind`, `solar`, or `nuclear`.")
    created_at: datetime = Field(description="UTC timestamp of creation.")
    updated_at: datetime = Field(description="UTC timestamp of the last update.")


class SupplyCreate(BaseModel):
    """Request body for POST /api/v1/supplies."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "North Sea Wind Farm",
                "type": "wind_turbine",
                "capacity_mw": 500.0,
                "efficiency": 0.42,
                "status": "active",
                "unit": "MW",
                "description": "Offshore wind farm, 150 turbines × 3.3 MW",
            }
        }
    }

    name: str = Field(description="Human-readable name.")
    type: str = Field(description="Component type: `wind_turbine`, `solar_panel`, or `nuclear_plant`.")
    capacity_mw: float = Field(description="Nominal installed capacity in megawatts.")
    efficiency: float = Field(default=1.0, description="Conversion efficiency, between 0.0 and 1.0.")
    status: ComponentStatus = Field(default=ComponentStatus.ACTIVE, description="Operational status.")
    unit: str = Field(default="MW", description="Unit of the capacity field.")
    description: str = Field(default="", description="Free-text description.")


class SupplyUpdate(BaseModel):
    """Request body for PUT /api/v1/supplies/{id} — all fields optional."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "capacity_mw": 600.0,
                "status": "maintenance",
            }
        }
    }

    name: str | None = Field(default=None, description="New name (omit to keep current value).")
    capacity_mw: float | None = Field(default=None, description="New capacity in MW.")
    efficiency: float | None = Field(default=None, description="New efficiency (0.0–1.0).")
    status: ComponentStatus | None = Field(default=None, description="New operational status.")
    unit: str | None = Field(default=None, description="New unit.")
    description: str | None = Field(default=None, description="New description.")
