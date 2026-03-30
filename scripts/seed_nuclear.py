"""Seed reference nuclear reactor specs into supplies + asset_parameters.

Idempotent: uses fixed UUIDs and updates existing rows in place.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.infrastructure.db.connection import get_session_factory
from app.infrastructure.db.models.asset_parameters_model import AssetParametersModel
from app.infrastructure.db.models.supply_model import SupplyModel

_EPR_1600_ID = uuid.UUID("30000000-0000-0000-0000-000000000001")
_PWR_900_ID = uuid.UUID("30000000-0000-0000-0000-000000000002")

NUCLEAR_REACTORS = [
    {
        "id": _EPR_1600_ID,
        "name": "EPR-1600 Reference",
        "capacity_mw": 1600.0,
        "params": {
            "reactor_type": "EPR",
            "thermal_power_mw": 4590.0,
            "electrical_efficiency": 0.348,
            "p_min_pu": 0.4,
            "ramp_rate_pu_per_hour": 0.05,
            "min_up_time_h": 8,
            "min_down_time_h": 8,
            "startup_cost": 500000.0,
            "marginal_cost_per_mwh": 12.0,
            "fuel_type": "uranium",
            "is_active": True,
        },
    },
    {
        "id": _PWR_900_ID,
        "name": "PWR-900 Reference",
        "capacity_mw": 900.0,
        "params": {
            "reactor_type": "PWR",
            "thermal_power_mw": 2785.0,
            "electrical_efficiency": 0.323,
            "p_min_pu": 0.4,
            "ramp_rate_pu_per_hour": 0.05,
            "min_up_time_h": 6,
            "min_down_time_h": 6,
            "startup_cost": 300000.0,
            "marginal_cost_per_mwh": 10.0,
            "fuel_type": "uranium",
            "is_active": True,
        },
    },
]


async def _upsert_reactor(session: AsyncSession, item: dict) -> None:
    now = datetime.now(timezone.utc)

    supply_result = await session.execute(
        select(SupplyModel).where(SupplyModel.id == item["id"])
    )
    supply = supply_result.scalar_one_or_none()

    if supply is None:
        supply = SupplyModel(
            id=item["id"],
            name=item["name"],
            type="nuclear_plant",
            capacity_mw=item["capacity_mw"],
            status="active" if item["params"].get("is_active", True) else "inactive",
            created_at=now,
            updated_at=now,
        )
        session.add(supply)
    else:
        supply.name = item["name"]
        supply.type = "nuclear_plant"
        supply.capacity_mw = item["capacity_mw"]
        supply.status = "active" if item["params"].get("is_active", True) else "inactive"
        supply.updated_at = now

    params_result = await session.execute(
        select(AssetParametersModel).where(
            AssetParametersModel.asset_id == item["id"],
            AssetParametersModel.asset_type == "nuclear_plant",
        )
    )
    asset_params = params_result.scalar_one_or_none()

    if asset_params is None:
        asset_params = AssetParametersModel(
            asset_id=item["id"],
            asset_type="nuclear_plant",
            params=item["params"],
            created_at=now,
            updated_at=now,
        )
        session.add(asset_params)
    else:
        asset_params.params = item["params"]
        asset_params.updated_at = now


async def seed() -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        for item in NUCLEAR_REACTORS:
            await _upsert_reactor(session, item)
        await session.commit()
    print("Nuclear reactors seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed())

