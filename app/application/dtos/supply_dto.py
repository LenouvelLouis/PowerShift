"""Supply DTO — application layer."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.base_component import ComponentStatus


@dataclass
class SupplyDTO:
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
