"""Concrete wind turbine repository backed by async SQLAlchemy.

Turbine models and assets are stored in the generic ``supplies`` +
``asset_parameters`` tables. Wind measurements are read from the unified
``weather_profile`` table (30-min KNMI data, station 06280 Groningen Eelde).

type values
-----------
- ``wind_turbine_model``  → catalog entry (manufacturer specs, power curve)
- ``wind_turbine``        → deployment instance (site, quantity, active flag)
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domain.wind.entities import (
    PowerCurvePoint,
    WindMeasurement,
    WindTurbineAsset,
    WindTurbineModel,
)
from app.infrastructure.db.models.asset_parameters_model import AssetParametersModel
from app.infrastructure.db.models.supply_model import SupplyModel
from app.infrastructure.db.models.weather_profile_model import WeatherProfileModel

_log = logging.getLogger(__name__)

_TYPE_MODEL = "wind_turbine_model"
_TYPE_ASSET = "wind_turbine"


class WindTurbineRepositoryImpl:
    """Implements the WindTurbineRepository protocol using SupplyModel + AssetParametersModel."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Turbine Model (catalog) ───────────────────────────────────────────────

    async def get_turbine_model(self, model_id: uuid.UUID) -> WindTurbineModel | None:
        supply = await self._session.execute(
            select(SupplyModel).where(
                SupplyModel.id == model_id,
                SupplyModel.type == _TYPE_MODEL,
            )
        )
        supply_row = supply.scalar_one_or_none()
        if supply_row is None:
            return None
        params_row = await self._get_params(model_id, _TYPE_MODEL)
        if params_row is None:
            return None
        return self._to_turbine_model(supply_row, params_row)

    async def list_turbine_models(self) -> list[WindTurbineModel]:
        result = await self._session.execute(
            select(SupplyModel).where(SupplyModel.type == _TYPE_MODEL)
        )
        models = []
        for row in result.scalars().all():
            params_row = await self._get_params(row.id, _TYPE_MODEL)
            if params_row is not None:
                models.append(self._to_turbine_model(row, params_row))
        return models

    async def create_turbine_model(self, model: WindTurbineModel) -> WindTurbineModel:
        now = datetime.now(UTC)
        supply = SupplyModel(
            id=model.id,
            name=f"{model.manufacturer} {model.model_name}",
            type=_TYPE_MODEL,
            capacity_mw=model.rated_power_kw / 1000,
            created_at=model.created_at or now,
            updated_at=model.updated_at or now,
        )
        params = AssetParametersModel(
            asset_id=model.id,
            asset_type=_TYPE_MODEL,
            params={
                "manufacturer": model.manufacturer,
                "model_name": model.model_name,
                "rotor_diameter_m": model.rotor_diameter_m,
                "hub_height_m": model.hub_height_m,
                "cut_in_speed_ms": model.cut_in_speed_ms,
                "cut_out_speed_ms": model.cut_out_speed_ms,
                "rated_speed_ms": model.rated_speed_ms,
                "power_curve": [
                    {"wind_speed_ms": pt.wind_speed_ms, "power_kw": pt.power_kw}
                    for pt in model.power_curve
                ],
            },
            created_at=now,
            updated_at=now,
        )
        self._session.add(supply)
        self._session.add(params)
        await self._session.flush()
        _log.debug("Created turbine model '%s %s' (id=%s)", model.manufacturer, model.model_name, model.id)
        return model

    # ── Wind Turbine Asset ────────────────────────────────────────────────────

    async def get_asset(self, asset_id: uuid.UUID) -> WindTurbineAsset | None:
        supply = await self._session.execute(
            select(SupplyModel).where(
                SupplyModel.id == asset_id,
                SupplyModel.type == _TYPE_ASSET,
            )
        )
        supply_row = supply.scalar_one_or_none()
        if supply_row is None:
            return None
        params_row = await self._get_params(asset_id, _TYPE_ASSET)
        if params_row is None:
            return None
        turbine_model_id = uuid.UUID(params_row.params["turbine_model_id"])
        turbine_model = await self.get_turbine_model(turbine_model_id)
        if turbine_model is None:
            _log.warning("Asset %s references missing turbine model %s", asset_id, turbine_model_id)
            return None
        return self._to_wind_asset(supply_row, params_row, turbine_model)

    async def list_assets(self) -> list[WindTurbineAsset]:
        result = await self._session.execute(
            select(SupplyModel).where(SupplyModel.type == _TYPE_ASSET)
        )
        rows = result.scalars().all()
        model_cache: dict[uuid.UUID, WindTurbineModel] = {}
        assets = []
        for row in rows:
            params_row = await self._get_params(row.id, _TYPE_ASSET)
            if params_row is None:
                continue
            mid = uuid.UUID(params_row.params["turbine_model_id"])
            if mid not in model_cache:
                m = await self.get_turbine_model(mid)
                if m is not None:
                    model_cache[mid] = m
            if mid in model_cache:
                assets.append(self._to_wind_asset(row, params_row, model_cache[mid]))
        return assets

    async def create_asset(self, asset: WindTurbineAsset) -> WindTurbineAsset:
        now = datetime.now(UTC)
        supply = SupplyModel(
            id=asset.id,
            name=asset.name,
            type=_TYPE_ASSET,
            capacity_mw=asset.turbine_model.rated_power_kw * asset.quantity / 1000,
            status="active" if asset.is_active else "inactive",
            created_at=asset.created_at or now,
            updated_at=asset.updated_at or now,
        )
        params = AssetParametersModel(
            asset_id=asset.id,
            asset_type=_TYPE_ASSET,
            params={
                "turbine_model_id": str(asset.turbine_model.id),
                "latitude": asset.latitude,
                "longitude": asset.longitude,
                "altitude_m": asset.altitude_m,
                "quantity": asset.quantity,
                "is_active": asset.is_active,
            },
            created_at=now,
            updated_at=now,
        )
        self._session.add(supply)
        self._session.add(params)
        await self._session.flush()
        _log.debug("Created wind asset '%s' (id=%s)", asset.name, asset.id)
        return asset

    # ── Wind Measurements ─────────────────────────────────────────────────────
    # Reads from weather_profile (unified 30-min table, Groningen Eelde only).
    # station_code is accepted for interface compatibility but ignored — the table
    # is single-station by design.

    async def get_wind_measurements(
        self, station_code: str, start: datetime, end: datetime
    ) -> list[WindMeasurement]:
        result = await self._session.execute(
            select(WeatherProfileModel)
            .where(
                WeatherProfileModel.timestamp >= start,
                WeatherProfileModel.timestamp <= end,
            )
            .order_by(WeatherProfileModel.timestamp)
        )
        measurements = [self._weather_profile_to_domain(row) for row in result.scalars().all()]
        if not measurements:
            _log.warning(
                "No weather_profile data for station %s between %s and %s "
                "— wind turbine will run at rated capacity (p_nom).",
                station_code, start, end,
            )
        return measurements

    async def get_latest_measurement_timestamp(
        self, station_code: str
    ) -> datetime | None:
        result = await self._session.execute(
            select(func.max(WeatherProfileModel.timestamp))
        )
        return result.scalar_one_or_none()

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get_params(
        self, asset_id: uuid.UUID, asset_type: str
    ) -> AssetParametersModel | None:
        result = await self._session.execute(
            select(AssetParametersModel).where(
                AssetParametersModel.asset_id == asset_id,
                AssetParametersModel.asset_type == asset_type,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_turbine_model(
        supply: SupplyModel, params: AssetParametersModel
    ) -> WindTurbineModel:
        p = params.params
        power_curve = [
            PowerCurvePoint(wind_speed_ms=pt["wind_speed_ms"], power_kw=pt["power_kw"])
            for pt in (p.get("power_curve") or [])
        ]
        return WindTurbineModel(
            id=supply.id,
            manufacturer=p["manufacturer"],
            model_name=p["model_name"],
            rated_power_kw=supply.capacity_mw * 1000,
            rotor_diameter_m=p["rotor_diameter_m"],
            hub_height_m=p["hub_height_m"],
            cut_in_speed_ms=p["cut_in_speed_ms"],
            cut_out_speed_ms=p["cut_out_speed_ms"],
            rated_speed_ms=p["rated_speed_ms"],
            power_curve=power_curve,
            created_at=supply.created_at,
            updated_at=supply.updated_at,
        )

    @staticmethod
    def _to_wind_asset(
        supply: SupplyModel,
        params: AssetParametersModel,
        turbine_model: WindTurbineModel,
    ) -> WindTurbineAsset:
        p = params.params
        return WindTurbineAsset(
            id=supply.id,
            name=supply.name,
            turbine_model=turbine_model,
            latitude=p.get("latitude"),
            longitude=p.get("longitude"),
            altitude_m=p.get("altitude_m"),
            quantity=p.get("quantity", 1),
            is_active=p.get("is_active", True),
            created_at=supply.created_at,
            updated_at=supply.updated_at,
        )

    @staticmethod
    def _weather_profile_to_domain(row: WeatherProfileModel) -> WindMeasurement:
        """Map a WeatherProfileModel row to the WindMeasurement domain entity."""
        return WindMeasurement(
            station_code="06280",
            station_name="Groningen Eelde",
            timestamp=row.timestamp,
            wind_speed_ms=row.wind_speed_ms,
            wind_direction_deg=row.wind_dir_deg,
            temperature_c=row.temperature_c,
            air_pressure_hpa=row.air_pressure_hpa,
        )

