"""Weather profile repository — reads data from the weather_profile table."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domain.interfaces.pv_profile_repository import IPVProfileRepository
from app.infrastructure.cache.weather_cache import get_weather_cache
from app.infrastructure.db.models.weather_profile_model import WeatherProfileModel

_log = logging.getLogger(__name__)


class WeatherProfileRepositoryImpl(IPVProfileRepository):
    """Fetches normalized solar irradiance profiles from the weather_profile table.

    Source column: radiation_wm2 (KNMI variable qg — global solar radiation, W/m²).
    The table stores data at 30-minute resolution; this repository projects the
    available slots onto a fixed hourly grid derived from the requested date range.

    Each hour bucket collects the slots whose timestamp falls within that hour
    (i.e. HH:00 < slot <= HH+1:00). If a slot is missing (KNMI gap), the bucket
    average is computed from whatever slots are present. This guarantees that the
    returned list always has exactly (end_date - start_date + 1) * 24 elements,
    matching snapshot_hours and preventing PyPSA index mismatches.

    The returned profile is normalized to [0.0–1.0] for use as p_max_pu.
    radiation_wm2 is naturally 0 at night, so no sun-elevation filter is needed.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_solar_profile(self, start_date: date, end_date: date) -> list[float]:
        cache = get_weather_cache()
        cached = await cache.get("solar", start_date, end_date)
        if cached is not None:
            _log.debug("Weather cache HIT for solar %s → %s", start_date, end_date)
            return cached

        profile = await self._fetch_solar_profile(start_date, end_date)
        await cache.set("solar", start_date, end_date, profile)
        return profile

    async def _fetch_solar_profile(self, start_date: date, end_date: date) -> list[float]:
        # Inclusive: start 00:00 → end 23:30 (last slot of end_date)
        start_dt = datetime.combine(start_date, time.min).replace(tzinfo=UTC)
        end_dt   = datetime.combine(end_date,   time.max).replace(tzinfo=UTC)
        snapshot_hours = ((end_date - start_date).days + 1) * 24

        result = await self._session.execute(
            select(WeatherProfileModel)
            .where(
                WeatherProfileModel.timestamp >= start_dt,
                WeatherProfileModel.timestamp <= end_dt,
            )
            .order_by(WeatherProfileModel.timestamp)
        )
        rows = list(result.scalars().all())

        if not rows:
            _log.warning(
                "No weather_profile data for %s → %s — solar profile will be all zeros.",
                start_date, end_date,
            )
            return [0.0] * snapshot_hours

        # Build a lookup: slot timestamp → radiation value
        slot_map: dict[datetime, float] = {
            row.timestamp: (row.radiation_wm2 or 0.0) for row in rows
        }

        # Project onto fixed hourly grid — each bucket covers ]HH:00, HH+1:00]
        hourly: list[float] = []
        for h in range(snapshot_hours):
            bucket_start = start_dt + timedelta(hours=h)
            slot_60 = bucket_start + timedelta(hours=1)
            values = [v for ts, v in slot_map.items() if bucket_start < ts <= slot_60]
            hourly.append(sum(values) / len(values) if values else 0.0)

        missing = snapshot_hours * 2 - len(rows)
        if missing > 0:
            _log.warning(
                "weather_profile: %d/%d expected 30-min slots missing for %s → %s "
                "(gaps filled with 0).",
                missing, snapshot_hours * 2, start_date, end_date,
            )

        max_val = max(hourly)
        if max_val == 0.0:
            return [0.0] * snapshot_hours

        return [v / max_val for v in hourly]

    async def get_wind_profile(self, start_date: date, end_date: date) -> list[float]:
        """Return a normalized wind power profile [0.0–1.0] for the given date range.

        Reads wind_speed_ms from weather_profile, extrapolates from 10 m to 80 m hub height
        using the power law (α=0.14), then applies a generic cubic power curve:
          - below cut-in (3 m/s) or above cut-out (25 m/s) → 0
          - between cut-in and rated (12 m/s) → (v / v_rated)³
          - above rated → 1.0
        Aggregates 30-min slots into hourly buckets (same logic as get_solar_profile).
        """
        cache = get_weather_cache()
        cached = await cache.get("wind", start_date, end_date)
        if cached is not None:
            _log.debug("Weather cache HIT for wind %s → %s", start_date, end_date)
            return cached

        profile = await self._fetch_wind_profile(start_date, end_date)
        await cache.set("wind", start_date, end_date, profile)
        return profile

    async def _fetch_wind_profile(self, start_date: date, end_date: date) -> list[float]:
        _CUT_IN_MS  = 3.0
        _RATED_MS   = 12.0
        _CUT_OUT_MS = 25.0
        _REF_HEIGHT = 10.0   # KNMI measurement height (m)
        _HUB_HEIGHT = 80.0   # generic hub height (m)
        _SHEAR_EXP  = 0.14   # open terrain

        start_dt = datetime.combine(start_date, time.min).replace(tzinfo=UTC)
        end_dt   = datetime.combine(end_date,   time.max).replace(tzinfo=UTC)
        snapshot_hours = ((end_date - start_date).days + 1) * 24

        result = await self._session.execute(
            select(WeatherProfileModel)
            .where(
                WeatherProfileModel.timestamp >= start_dt,
                WeatherProfileModel.timestamp <= end_dt,
            )
            .order_by(WeatherProfileModel.timestamp)
        )
        rows = list(result.scalars().all())

        if not rows:
            _log.warning(
                "No weather_profile data for %s → %s — wind profile will be all zeros.",
                start_date, end_date,
            )
            return [0.0] * snapshot_hours

        def _to_p_max_pu(wind_speed_ms: float | None) -> float:
            if not wind_speed_ms:
                return 0.0
            v = wind_speed_ms * (_HUB_HEIGHT / _REF_HEIGHT) ** _SHEAR_EXP
            if v < _CUT_IN_MS or v > _CUT_OUT_MS:
                return 0.0
            return min((v / _RATED_MS) ** 3, 1.0)

        slot_map: dict[datetime, float] = {
            row.timestamp: _to_p_max_pu(row.wind_speed_ms) for row in rows
        }

        hourly: list[float] = []
        for h in range(snapshot_hours):
            bucket_start = start_dt + timedelta(hours=h)
            slot_60 = bucket_start + timedelta(hours=1)
            values = [v for ts, v in slot_map.items() if bucket_start < ts <= slot_60]
            hourly.append(sum(values) / len(values) if values else 0.0)

        return hourly
