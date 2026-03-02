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
