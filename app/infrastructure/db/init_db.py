"""Database initialisation — creates all tables on startup (idempotent)."""

from __future__ import annotations


async def init_db() -> None:
    # Import every model so SQLModel.metadata registers their tables
    import app.infrastructure.db.models.supply_model  # noqa: F401
    import app.infrastructure.db.models.demand_model  # noqa: F401
    import app.infrastructure.db.models.network_model  # noqa: F401
    import app.infrastructure.db.models.asset_parameters_model  # noqa: F401
    import app.infrastructure.db.models.simulation_request_model  # noqa: F401
    import app.infrastructure.db.models.simulation_result_model  # noqa: F401
    import app.infrastructure.db.models.pv_hourly_model  # noqa: F401
    import app.infrastructure.db.models.weather_snapshot_model  # noqa: F401

    from sqlmodel import SQLModel
    from sqlalchemy import text
    from app.infrastructure.db.connection import get_engine

    async with get_engine().begin() as conn:
        # Create all tables that don't exist yet
        await conn.run_sync(SQLModel.metadata.create_all)

        # Idempotent migrations: add columns introduced after initial schema
        await conn.execute(
            text("ALTER TABLE simulation_requests ADD COLUMN IF NOT EXISTS asset_overrides JSONB")
        )
