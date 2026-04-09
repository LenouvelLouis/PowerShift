"""Port (interface) for the wind turbine repository — dependency inversion."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.domain.wind.entities import WindMeasurement, WindTurbineAsset, WindTurbineModel


@runtime_checkable
class WindTurbineRepository(Protocol):
    """Abstract repository interface for wind turbine persistence.

    Infrastructure implementations must satisfy this protocol.
    Domain and application layers depend only on this interface.
    """

    async def get_turbine_model(self, model_id: uuid.UUID) -> WindTurbineModel | None:
        """Fetch a turbine model by UUID; returns None if not found."""
        ...

    async def list_turbine_models(self) -> list[WindTurbineModel]:
        """Return all stored turbine models."""
        ...

    async def create_turbine_model(self, model: WindTurbineModel) -> WindTurbineModel:
        """Persist a new turbine model and return it (with any DB-assigned fields)."""
        ...

    async def get_asset(self, asset_id: uuid.UUID) -> WindTurbineAsset | None:
        """Fetch a wind turbine asset by UUID; returns None if not found."""
        ...

    async def list_assets(self) -> list[WindTurbineAsset]:
        """Return all stored wind turbine assets."""
        ...

    async def create_asset(self, asset: WindTurbineAsset) -> WindTurbineAsset:
        """Persist a new wind turbine asset and return it."""
        ...

    async def get_wind_measurements(
        self, station_code: str, start: datetime, end: datetime
    ) -> list[WindMeasurement]:
        """Return measurements ordered by timestamp ASC within the given range."""
        ...

    async def get_latest_measurement_timestamp(
        self, station_code: str
    ) -> datetime | None:
        """Return the most recent timestamp stored for this station, or None."""
        ...
