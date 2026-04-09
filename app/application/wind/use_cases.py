"""Application-layer use cases for the wind turbine module.

Each use case encapsulates a single application flow, coordinates the domain
service and repository, and translates between Pydantic schemas and domain
entities.  They contain no HTTP or ORM knowledge.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from app.application.wind.schemas import (
    CalculatePowerRequest,
    CalculatePowerResponse,
    PowerSeriesPoint,
    TurbineModelCreate,
    TurbineModelResponse,
    WindAssetCreate,
    WindAssetResponse,
    WindMeasurementResponse,
    WindMeasurementStatsResponse,
)
from app.domain.wind.entities import (
    PowerCurvePoint,
    WindDataPoint,
    WindTurbineAsset,
    WindTurbineModel,
)
from app.domain.wind.exceptions import (
    InvalidPowerCurveError,
    InvalidTurbineModelError,
    TurbineModelNotFoundError,
    WindAssetNotFoundError,
)
from app.domain.wind.services import WindPowerCalculator
from app.infrastructure.wind.repository import WindTurbineRepositoryImpl

_log = logging.getLogger(__name__)


# ── Helper mappers ────────────────────────────────────────────────────────────

def _model_entity_to_schema(model: WindTurbineModel) -> TurbineModelResponse:
    from app.application.wind.schemas import PowerCurvePointSchema  # local to avoid circular
    return TurbineModelResponse(
        id=model.id,
        manufacturer=model.manufacturer,
        model_name=model.model_name,
        rated_power_kw=model.rated_power_kw,
        rotor_diameter_m=model.rotor_diameter_m,
        hub_height_m=model.hub_height_m,
        cut_in_speed_ms=model.cut_in_speed_ms,
        cut_out_speed_ms=model.cut_out_speed_ms,
        rated_speed_ms=model.rated_speed_ms,
        power_curve=[
            PowerCurvePointSchema(wind_speed_ms=pt.wind_speed_ms, power_kw=pt.power_kw)
            for pt in model.power_curve
        ],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _asset_entity_to_schema(asset: WindTurbineAsset) -> WindAssetResponse:
    return WindAssetResponse(
        id=asset.id,
        name=asset.name,
        turbine_model=_model_entity_to_schema(asset.turbine_model),
        latitude=asset.latitude,
        longitude=asset.longitude,
        altitude_m=asset.altitude_m,
        quantity=asset.quantity,
        is_active=asset.is_active,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


# ── Use cases ─────────────────────────────────────────────────────────────────

class CreateTurbineModelUseCase:
    """Validate and persist a new turbine model (catalog entry)."""

    def __init__(self, repo: WindTurbineRepositoryImpl) -> None:
        self._repo = repo

    async def execute(self, body: TurbineModelCreate) -> TurbineModelResponse:
        """Validate business rules then persist.

        Raises:
            InvalidTurbineModelError: If speed thresholds are inconsistent.
            InvalidPowerCurveError: If the power curve is not monotonically
                non-decreasing up to rated speed.
        """
        # Validate speed relationships
        if body.cut_in_speed_ms >= body.cut_out_speed_ms:
            raise InvalidTurbineModelError(
                f"cut_in_speed_ms ({body.cut_in_speed_ms}) must be less than "
                f"cut_out_speed_ms ({body.cut_out_speed_ms})"
            )

        # Validate power curve if provided
        if body.power_curve:
            self._validate_power_curve(body)

        now = datetime.now(UTC)
        model = WindTurbineModel(
            id=uuid.uuid4(),
            manufacturer=body.manufacturer,
            model_name=body.model_name,
            rated_power_kw=body.rated_power_kw,
            rotor_diameter_m=body.rotor_diameter_m,
            hub_height_m=body.hub_height_m,
            cut_in_speed_ms=body.cut_in_speed_ms,
            cut_out_speed_ms=body.cut_out_speed_ms,
            rated_speed_ms=body.rated_speed_ms,
            power_curve=[
                PowerCurvePoint(wind_speed_ms=pt.wind_speed_ms, power_kw=pt.power_kw)
                for pt in body.power_curve
            ],
            created_at=now,
            updated_at=now,
        )
        saved = await self._repo.create_turbine_model(model)
        _log.info("Created turbine model '%s %s'", saved.manufacturer, saved.model_name)
        return _model_entity_to_schema(saved)

    @staticmethod
    def _validate_power_curve(body: TurbineModelCreate) -> None:
        points = sorted(body.power_curve, key=lambda p: p.wind_speed_ms)

        # Power must be non-decreasing up to rated speed
        prev_power = -1.0
        for pt in points:
            if pt.wind_speed_ms <= body.rated_speed_ms:
                if pt.power_kw < prev_power:
                    raise InvalidPowerCurveError(
                        f"Power curve must be non-decreasing up to rated speed "
                        f"({body.rated_speed_ms} m/s). Got {pt.power_kw} kW after {prev_power} kW."
                    )
                prev_power = pt.power_kw

        # Power at rated speed should not exceed rated power by more than 5%
        at_rated = [pt for pt in points if abs(pt.wind_speed_ms - body.rated_speed_ms) < 0.5]
        if at_rated:
            max_at_rated = max(pt.power_kw for pt in at_rated)
            if max_at_rated > body.rated_power_kw * 1.05:
                raise InvalidPowerCurveError(
                    f"Power at rated speed ({max_at_rated} kW) exceeds "
                    f"rated power ({body.rated_power_kw} kW) by more than 5%."
                )


class CreateWindAssetUseCase:
    """Validate and persist a new wind turbine deployment."""

    def __init__(self, repo: WindTurbineRepositoryImpl) -> None:
        self._repo = repo

    async def execute(self, body: WindAssetCreate) -> WindAssetResponse:
        """Look up the turbine model, create and persist the asset.

        Raises:
            TurbineModelNotFoundError: If turbine_model_id does not exist.
        """
        turbine_model = await self._repo.get_turbine_model(body.turbine_model_id)
        if turbine_model is None:
            raise TurbineModelNotFoundError(body.turbine_model_id)

        now = datetime.now(UTC)
        asset = WindTurbineAsset(
            id=uuid.uuid4(),
            name=body.name,
            turbine_model=turbine_model,
            latitude=body.latitude,
            longitude=body.longitude,
            altitude_m=body.altitude_m,
            quantity=body.quantity,
            is_active=body.is_active,
            created_at=now,
            updated_at=now,
        )
        saved = await self._repo.create_asset(asset)
        _log.info("Created wind asset '%s' (id=%s)", saved.name, saved.id)
        return _asset_entity_to_schema(saved)


class GetWindMeasurementsUseCase:
    """Retrieve stored KNMI measurements and optionally convert to WindDataPoints."""

    def __init__(self, repo: WindTurbineRepositoryImpl) -> None:
        self._repo = repo

    async def execute(
        self,
        station_code: str,
        start: datetime,
        end: datetime,
        limit: int = 1000,
        offset: int = 0,
    ) -> tuple[list[WindMeasurementResponse], list[WindDataPoint]]:
        """Fetch measurements and return both raw responses and domain wind data points.

        Returns:
            A (responses, wind_data_points) tuple.
        """
        measurements = await self._repo.get_wind_measurements(station_code, start, end)
        # Apply pagination
        page = measurements[offset: offset + limit]

        responses = [
            WindMeasurementResponse(
                station_code=m.station_code,
                station_name=m.station_name,
                timestamp=m.timestamp,
                wind_speed_ms=m.wind_speed_ms,
                wind_direction_deg=m.wind_direction_deg,
                temperature_c=m.temperature_c,
                air_pressure_hpa=m.air_pressure_hpa,
            )
            for m in page
        ]
        wind_points = [
            WindDataPoint(
                timestamp=m.timestamp,
                wind_speed_ms=m.wind_speed_ms or 0.0,
                wind_direction_deg=m.wind_direction_deg,
                temperature_c=m.temperature_c,
            )
            for m in measurements  # use full list for power calc, not paginated page
        ]
        return responses, wind_points

    async def get_stats(
        self, station_code: str, start: datetime, end: datetime
    ) -> WindMeasurementStatsResponse:
        """Compute summary statistics for a station + time range."""
        measurements = await self._repo.get_wind_measurements(station_code, start, end)
        count = len(measurements)
        if count == 0:
            return WindMeasurementStatsResponse(
                station_code=station_code,
                count=0,
                missing_wind_pct=100.0,
            )

        speeds = [m.wind_speed_ms for m in measurements if m.wind_speed_ms is not None]
        temps = [m.temperature_c for m in measurements if m.temperature_c is not None]
        missing = sum(1 for m in measurements if m.wind_speed_ms is None)

        return WindMeasurementStatsResponse(
            station_code=station_code,
            count=count,
            start=measurements[0].timestamp,
            end=measurements[-1].timestamp,
            avg_wind_speed_ms=sum(speeds) / len(speeds) if speeds else None,
            min_wind_speed_ms=min(speeds) if speeds else None,
            max_wind_speed_ms=max(speeds) if speeds else None,
            avg_temperature_c=sum(temps) / len(temps) if temps else None,
            missing_wind_pct=round(missing / count * 100, 2),
        )


class CalculateWindPowerUseCase:
    """Compute the power time series and summary statistics for a wind asset.

    Supports two input modes:
    - **Inline**: wind data provided directly in the request body.
    - **DB**: station_code + start + end — fetches from ``weather_profile`` table.
    """

    def __init__(self, repo: WindTurbineRepositoryImpl) -> None:
        self._repo = repo
        self._calculator = WindPowerCalculator()

    async def execute(self, body: CalculatePowerRequest) -> CalculatePowerResponse:
        """Load asset, resolve wind data, run calculation, return series + stats.

        Raises:
            WindAssetNotFoundError: If asset_id does not exist.
        """
        asset = await self._repo.get_asset(body.asset_id)
        if asset is None:
            raise WindAssetNotFoundError(body.asset_id)

        if body.wind_data:
            # Option A: inline data provided in request
            wind_data: list[WindDataPoint] = [
                WindDataPoint(
                    timestamp=pt.timestamp,
                    wind_speed_ms=pt.wind_speed_ms,
                    wind_direction_deg=pt.wind_direction_deg,
                    temperature_c=pt.temperature_c,
                )
                for pt in body.wind_data
            ]
        else:
            # Option B: fetch from weather_profile table
            assert body.station_code and body.start and body.end
            measurements = await self._repo.get_wind_measurements(
                body.station_code, body.start, body.end
            )
            wind_data = [
                WindDataPoint(
                    timestamp=m.timestamp,
                    wind_speed_ms=m.wind_speed_ms or 0.0,
                    wind_direction_deg=m.wind_direction_deg,
                    temperature_c=m.temperature_c,
                )
                for m in measurements
            ]
            _log.info(
                "Power calc for '%s': fetched %d measurements from DB (station=%s)",
                asset.name, len(wind_data), body.station_code,
            )

        series = self._calculator.calculate_power_series(
            wind_data, asset, availability=body.availability
        )
        capacity_factor = self._calculator.calculate_capacity_factor(
            series, asset.turbine_model.rated_power_kw * asset.quantity
        )

        powers = [p for _, p in series]
        total_energy_kwh = sum(powers)
        peak_power_kw = max(powers) if powers else 0.0

        _log.info(
            "Power calc for asset '%s': CF=%.3f, total=%.0f kWh, peak=%.0f kW",
            asset.name, capacity_factor, total_energy_kwh, peak_power_kw,
        )

        return CalculatePowerResponse(
            asset_id=asset.id,
            asset_name=asset.name,
            power_series=[
                PowerSeriesPoint(timestamp=ts, power_kw=power) for ts, power in series
            ],
            capacity_factor=capacity_factor,
            total_energy_kwh=total_energy_kwh,
            peak_power_kw=peak_power_kw,
        )
