"""SQLModel ORM model for network components (transformers and cables)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
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
    capacity_mva: float | None = None
    losses_kw: float | None = None

    # ── Transformer-specific (nullable for cables) ───────────────────────────
    voltage_hv_kv: float | None = None
    voltage_lv_kv: float | None = None

    # ── Cable-specific (nullable for transformers) ───────────────────────────
    length_km: float | None = None
    resistance_ohm_per_km: float | None = None
    reactance_ohm_per_km: float | None = None

    # ── Metadata ─────────────────────────────────────────────────────────────
    status: str = "active"
    unit: str = "MVA"
    description: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
