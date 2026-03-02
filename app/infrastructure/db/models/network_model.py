"""SQLAlchemy ORM model for network components (transformers and cables)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.base_component import ComponentStatus
from app.infrastructure.db.connection import Base


class NetworkModel(Base):
    __tablename__ = "network_components"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # "transformer" | "cable"

    # ── Common fields ────────────────────────────────────────────────────────
    voltage_kv: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_mva: Mapped[float | None] = mapped_column(Float, nullable=True)
    losses_kw: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Transformer-specific (nullable for cables) ───────────────────────────
    voltage_hv_kv: Mapped[float | None] = mapped_column(Float, nullable=True)
    voltage_lv_kv: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Cable-specific (nullable for transformers) ───────────────────────────
    length_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    resistance_ohm_per_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    reactance_ohm_per_km: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Metadata ─────────────────────────────────────────────────────────────
    status: Mapped[ComponentStatus] = mapped_column(
        Enum(ComponentStatus, name="component_status"),
        nullable=False,
        default=ComponentStatus.ACTIVE,
    )
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="MVA")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
