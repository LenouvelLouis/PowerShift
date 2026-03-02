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
