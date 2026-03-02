"""Seed script — creates tables and inserts 2 supplies + 2 demands.

Usage:
    python seed.py
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.domain.entities.base_component import ComponentStatus
from app.infrastructure.db.connection import Base, get_engine
from app.infrastructure.db.models.demand_model import DemandModel  # noqa: F401
from app.infrastructure.db.models.supply_model import SupplyModel  # noqa: F401
from app.infrastructure.secrets.settings import get_settings


def _check_settings() -> None:
    s = get_settings()
    if not s.DATABASE_URL:
        raise SystemExit(
            "DATABASE_URL is not set.\n"
            "Copy .env.example to .env and fill in the connection string."
        )


async def seed() -> None:
    _check_settings()

    engine = get_engine()

    async with engine.begin() as conn:
        # Enable pgcrypto extension for gen_random_uuid() if not already present
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)

    now = datetime.now(timezone.utc)

    supplies = [
        SupplyModel(
            id=uuid.uuid4(),
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
            id=uuid.uuid4(),
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

    demands = [
        DemandModel(
            id=uuid.uuid4(),
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
            id=uuid.uuid4(),
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

    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        session.add_all(supplies + demands)
        await session.commit()

    await engine.dispose()

    print(f"Seeded {len(supplies)} supplies and {len(demands)} demands.")


if __name__ == "__main__":
    asyncio.run(seed())
