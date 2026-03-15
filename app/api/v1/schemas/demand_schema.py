"""Pydantic v2 schemas for demand components."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities.base_component import ComponentStatus


class DemandResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID = Field(description="Unique identifier of the demand component.")
    name: str = Field(description="Human-readable name.")
    type: str = Field(description="Component type: `house` or `electric_vehicle`.")
    load_mw: float = Field(description="Nominal power consumption in megawatts.")
    status: ComponentStatus = Field(description="Operational status.")
    unit: str = Field(description="Unit of the load field (typically `MW`).")
    description: str = Field(description="Free-text description.")
    created_at: datetime = Field(description="UTC timestamp of creation.")
    updated_at: datetime = Field(description="UTC timestamp of the last update.")


class DemandCreate(BaseModel):
    """Request body for POST /api/v1/demands."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Groningen Residential Zone A",
                "type": "house",
                "load_mw": 120.0,
                "status": "active",
                "unit": "MW",
                "description": "~40 000 residential households in Groningen",
            }
        }
    }

    name: str = Field(description="Human-readable name.")
    type: str = Field(description="Component type: `house` or `electric_vehicle`.")
    load_mw: float = Field(description="Nominal power consumption in megawatts.")
    status: ComponentStatus = Field(default=ComponentStatus.ACTIVE, description="Operational status.")
    unit: str = Field(default="MW", description="Unit of the load field.")
    description: str = Field(default="", description="Free-text description.")


class DemandUpdate(BaseModel):
    """Request body for PUT /api/v1/demands/{id} — all fields optional."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "load_mw": 150.0,
                "status": "inactive",
            }
        }
    }

    name: str | None = Field(default=None, description="New name (omit to keep current value).")
    load_mw: float | None = Field(default=None, description="New load in MW.")
    status: ComponentStatus | None = Field(default=None, description="New operational status.")
    unit: str | None = Field(default=None, description="New unit.")
    description: str | None = Field(default=None, description="New description.")
