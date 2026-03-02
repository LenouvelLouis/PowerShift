"""Network DTO — application layer."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.base_component import ComponentStatus


@dataclass
class NetworkDTO:
    id: uuid.UUID
    name: str
    type: str                          # "transformer" | "cable"
    voltage_kv: float
    capacity_mva: float
    losses_kw: float | None
    # Transformer-specific (None for cables)
    voltage_hv_kv: float | None
    voltage_lv_kv: float | None
    # Cable-specific (None for transformers)
    length_km: float | None
    resistance_ohm_per_km: float | None
    reactance_ohm_per_km: float | None
    status: ComponentStatus
    unit: str
    description: str
    created_at: datetime
    updated_at: datetime
