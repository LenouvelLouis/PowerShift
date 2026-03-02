"""Seed script — creates tables and upserts 2 supplies + 2 demands + 2 network components.

Idempotent: safe to run multiple times. Uses fixed UUIDs so re-running never
creates duplicate rows (existing rows are updated in-place via merge).

Usage (from project root, with package installed):
    python scripts/seed.py
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.entities.base_component import ComponentStatus
from app.infrastructure.db.connection import Base, get_engine
from app.infrastructure.db.models.demand_model import DemandModel  # noqa: F401 — registers table
from app.infrastructure.db.models.network_model import NetworkModel  # noqa: F401 — registers table
from app.infrastructure.db.models.supply_model import SupplyModel  # noqa: F401 — registers table
from app.infrastructure.secrets.settings import get_settings

# ── Fixed UUIDs guarantee idempotency across runs ────────────────────────────
_SUPPLY_WIND_ID  = uuid.UUID("00000000-0000-0000-0000-000000000001")
_SUPPLY_SOLAR_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
_DEMAND_HOUSE_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")
_DEMAND_EV_ID    = uuid.UUID("00000000-0000-0000-0000-000000000004")
_NET_TRANSFORMER_ID = uuid.UUID("00000000-0000-0000-0000-000000000005")
_NET_CABLE_ID       = uuid.UUID("00000000-0000-0000-0000-000000000006")


def _check_settings() -> None:
    """Abort early if DATABASE_URL is missing."""
    s = get_settings()
    if not s.DATABASE_URL:
        raise SystemExit(
            "DATABASE_URL is not set.\n"
            "Copy .env.example to .env and fill in the connection string."
        )


async def seed() -> None:
    _check_settings()

    engine = get_engine()

    # Create tables (and the pgcrypto extension for server-side UUID generation).
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)

    now = datetime.now(timezone.utc)

    supplies: list[SupplyModel] = [
        SupplyModel(
            id=_SUPPLY_WIND_ID,
            name="North Sea Wind Farm",
            type="wind_turbine",
            capacity_mw=500.0,
            efficiency=0.42,
            status=ComponentStatus.ACTIVE,
            unit="MW",
            description="Offshore wind farm, 150 turbines × 3.3 MW",
            created_at=now,
            updated_at=now,
        ),
        SupplyModel(
            id=_SUPPLY_SOLAR_ID,
            name="Provence Solar Park",
            type="solar_panel",
            capacity_mw=200.0,
            efficiency=0.22,
            status=ComponentStatus.ACTIVE,
            unit="MW",
            description="Ground-mounted PV, 800 ha, south-facing",
            created_at=now,
            updated_at=now,
        ),
    ]

    demands: list[DemandModel] = [
        DemandModel(
            id=_DEMAND_HOUSE_ID,
            name="Paris Residential Zone A",
            type="house",
            load_mw=120.0,
            status=ComponentStatus.ACTIVE,
            unit="MW",
            description="~40 000 residential households",
            created_at=now,
            updated_at=now,
        ),
        DemandModel(
            id=_DEMAND_EV_ID,
            name="EV Fleet — Paris Region",
            type="electric_vehicle",
            load_mw=45.0,
            status=ComponentStatus.ACTIVE,
            unit="MW",
            description="Managed EV charging fleet, overnight priority",
            created_at=now,
            updated_at=now,
        ),
    ]

    network_components: list[NetworkModel] = [
        NetworkModel(
            id=_NET_TRANSFORMER_ID,
            name="MV/LV Transformer - De Held",
            type="transformer",
            voltage_kv=10.0,
            voltage_hv_kv=10.0,
            voltage_lv_kv=0.4,
            capacity_mva=0.63,
            losses_kw=None,
            status=ComponentStatus.ACTIVE,
            unit="MVA",
            description="Typical Dutch residential MV/LV transformer, 630 kVA",
            created_at=now,
            updated_at=now,
        ),
        NetworkModel(
            id=_NET_CABLE_ID,
            name="LV Cable - Zone 1",
            type="cable",
            voltage_kv=0.4,
            capacity_mva=None,
            length_km=0.5,
            resistance_ohm_per_km=0.32,
            reactance_ohm_per_km=0.07,
            losses_kw=None,
            status=ComponentStatus.ACTIVE,
            unit="MVA",
            description="Typical Dutch LV underground cable, XLPE 4×150 mm²",
            created_at=now,
            updated_at=now,
        ),
    ]

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # merge() inserts if the PK is absent, updates if it already exists.
        for obj in supplies + demands + network_components:
            await session.merge(obj)
        await session.commit()

    await engine.dispose()

    print(
        f"Seeded {len(supplies)} supplies, {len(demands)} demands, "
        f"{len(network_components)} network components. (idempotent)"
    )


if __name__ == "__main__":
    asyncio.run(seed())
