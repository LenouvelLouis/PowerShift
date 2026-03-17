"""Seed script — inserts 3 real wind turbine models into supplies + asset_parameters.

Follows the existing project pattern: turbine catalog entries are stored as
``SupplyModel`` rows (type="wind_turbine_model") with their specs in the
``AssetParametersModel`` JSON params field.

Idempotent: uses fixed UUIDs so re-running never creates duplicates
(existing rows are updated in-place via session.merge()).

Usage (from project root):
    python scripts/seed_wind.py
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from app.infrastructure.db.connection import get_engine
# Import all models so SQLModel.metadata is fully populated
from app.infrastructure.db.models.asset_parameters_model import AssetParametersModel  # noqa: F401
from app.infrastructure.db.models.demand_model import DemandModel  # noqa: F401
from app.infrastructure.db.models.network_model import NetworkModel  # noqa: F401
from app.infrastructure.db.models.simulation_request_model import SimulationRequestModel  # noqa: F401
from app.infrastructure.db.models.simulation_result_model import SimulationResultModel  # noqa: F401
from app.infrastructure.db.models.supply_model import SupplyModel  # noqa: F401
from app.infrastructure.wind.models import WindMeasurementORM  # noqa: F401
from app.infrastructure.secrets.settings import get_settings

# ── Fixed UUIDs for idempotency ───────────────────────────────────────────────

_VESTAS_V110_ID   = uuid.UUID("10000000-0000-0000-0000-000000000001")
_ENERCON_E126_ID  = uuid.UUID("10000000-0000-0000-0000-000000000002")
_SG_3_4_132_ID    = uuid.UUID("10000000-0000-0000-0000-000000000003")

# ── Realistic power curves ────────────────────────────────────────────────────

_VESTAS_V110_CURVE = [
    {"wind_speed_ms": 3.0,  "power_kw":  44.0},
    {"wind_speed_ms": 4.0,  "power_kw": 136.0},
    {"wind_speed_ms": 5.0,  "power_kw": 272.0},
    {"wind_speed_ms": 6.0,  "power_kw": 476.0},
    {"wind_speed_ms": 7.0,  "power_kw": 748.0},
    {"wind_speed_ms": 8.0,  "power_kw": 1070.0},
    {"wind_speed_ms": 9.0,  "power_kw": 1418.0},
    {"wind_speed_ms": 10.0, "power_kw": 1736.0},
    {"wind_speed_ms": 11.0, "power_kw": 1948.0},
    {"wind_speed_ms": 11.5, "power_kw": 2000.0},
    {"wind_speed_ms": 14.0, "power_kw": 2000.0},
    {"wind_speed_ms": 20.0, "power_kw": 2000.0},
    {"wind_speed_ms": 25.0, "power_kw": 2000.0},
]

_ENERCON_E126_CURVE = [
    {"wind_speed_ms": 2.5,  "power_kw":    0.0},
    {"wind_speed_ms": 3.0,  "power_kw":   57.0},
    {"wind_speed_ms": 4.0,  "power_kw":  225.0},
    {"wind_speed_ms": 5.0,  "power_kw":  522.0},
    {"wind_speed_ms": 6.0,  "power_kw":  960.0},
    {"wind_speed_ms": 7.0,  "power_kw": 1582.0},
    {"wind_speed_ms": 8.0,  "power_kw": 2340.0},
    {"wind_speed_ms": 9.0,  "power_kw": 3200.0},
    {"wind_speed_ms": 10.0, "power_kw": 4200.0},
    {"wind_speed_ms": 12.0, "power_kw": 5900.0},
    {"wind_speed_ms": 14.0, "power_kw": 7000.0},
    {"wind_speed_ms": 16.0, "power_kw": 7580.0},
    {"wind_speed_ms": 20.0, "power_kw": 7580.0},
    {"wind_speed_ms": 28.0, "power_kw": 7580.0},
]

_SG_3_4_132_CURVE = [
    {"wind_speed_ms": 3.0,  "power_kw":   60.0},
    {"wind_speed_ms": 4.0,  "power_kw":  195.0},
    {"wind_speed_ms": 5.0,  "power_kw":  396.0},
    {"wind_speed_ms": 6.0,  "power_kw":  672.0},
    {"wind_speed_ms": 7.0,  "power_kw": 1053.0},
    {"wind_speed_ms": 8.0,  "power_kw": 1530.0},
    {"wind_speed_ms": 9.0,  "power_kw": 2100.0},
    {"wind_speed_ms": 10.0, "power_kw": 2700.0},
    {"wind_speed_ms": 11.0, "power_kw": 3200.0},
    {"wind_speed_ms": 12.0, "power_kw": 3400.0},
    {"wind_speed_ms": 15.0, "power_kw": 3400.0},
    {"wind_speed_ms": 25.0, "power_kw": 3400.0},
]

# ── Turbine definitions ───────────────────────────────────────────────────────

_TURBINES = [
    {
        "id": _VESTAS_V110_ID,
        "manufacturer": "Vestas",
        "model_name": "V110-2.0",
        "rated_power_kw": 2_000.0,
        "rotor_diameter_m": 110.0,
        "hub_height_m": 95.0,
        "cut_in_speed_ms": 3.0,
        "cut_out_speed_ms": 25.0,
        "rated_speed_ms": 11.5,
        "power_curve": _VESTAS_V110_CURVE,
    },
    {
        "id": _ENERCON_E126_ID,
        "manufacturer": "Enercon",
        "model_name": "E-126",
        "rated_power_kw": 7_580.0,
        "rotor_diameter_m": 127.0,
        "hub_height_m": 135.0,
        "cut_in_speed_ms": 2.5,
        "cut_out_speed_ms": 28.0,
        "rated_speed_ms": 16.0,
        "power_curve": _ENERCON_E126_CURVE,
    },
    {
        "id": _SG_3_4_132_ID,
        "manufacturer": "Siemens Gamesa",
        "model_name": "SG 3.4-132",
        "rated_power_kw": 3_400.0,
        "rotor_diameter_m": 132.0,
        "hub_height_m": 110.0,
        "cut_in_speed_ms": 3.0,
        "cut_out_speed_ms": 25.0,
        "rated_speed_ms": 12.0,
        "power_curve": _SG_3_4_132_CURVE,
    },
]


def _check_settings() -> None:
    s = get_settings()
    if not s.DATABASE_URL:
        raise SystemExit(
            "DATABASE_URL is not set.\n"
            "Copy .env.example to .env and fill in the connection string."
        )


async def seed_wind() -> None:
    _check_settings()

    engine = get_engine()

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(SQLModel.metadata.create_all)

    now = datetime.now(timezone.utc)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        for t in _TURBINES:
            supply = SupplyModel(
                id=t["id"],
                name=f"{t['manufacturer']} {t['model_name']}",
                type="wind_turbine_model",
                capacity_mw=t["rated_power_kw"] / 1000,
                created_at=now,
                updated_at=now,
            )
            params = AssetParametersModel(
                asset_id=t["id"],
                asset_type="wind_turbine_model",
                params={
                    "manufacturer": t["manufacturer"],
                    "model_name": t["model_name"],
                    "rotor_diameter_m": t["rotor_diameter_m"],
                    "hub_height_m": t["hub_height_m"],
                    "cut_in_speed_ms": t["cut_in_speed_ms"],
                    "cut_out_speed_ms": t["cut_out_speed_ms"],
                    "rated_speed_ms": t["rated_speed_ms"],
                    "power_curve": t["power_curve"],
                },
                created_at=now,
                updated_at=now,
            )
            await session.merge(supply)
            await session.merge(params)

        await session.commit()

    await engine.dispose()

    print(f"Seeded {len(_TURBINES)} wind turbine models into supplies + asset_parameters. (idempotent)")
    for t in _TURBINES:
        print(f"  • {t['manufacturer']} {t['model_name']} — {t['rated_power_kw'] / 1000:.2f} MW  (id={t['id']})")


if __name__ == "__main__":
    asyncio.run(seed_wind())
