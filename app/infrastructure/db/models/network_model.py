"""SQLModel ORM model for network components (transformers and cables)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class NetworkModel(SQLModel, table=True):
    __tablename__ = "network_components"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    type: str  # "transformer" | "cable"

    # ── Common fields ────────────────────────────────────────────────────────
    voltage_kv: float
    capacity_mva: Optional[float] = None
    losses_kw: Optional[float] = None

    # ── Transformer-specific (nullable for cables) ───────────────────────────
    voltage_hv_kv: Optional[float] = None
    voltage_lv_kv: Optional[float] = None

    # ── Cable-specific (nullable for transformers) ───────────────────────────
    length_km: Optional[float] = None
    resistance_ohm_per_km: Optional[float] = None
    reactance_ohm_per_km: Optional[float] = None

    # ── Metadata ─────────────────────────────────────────────────────────────
    status: str = "active"
    unit: str = "MVA"
    description: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
