"""Solar profile repository — reads radiation data from weather_profile table."""

from __future__ import annotations

from datetime import date, datetime, time, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domain.interfaces.pv_profile_repository import IPVProfileRepository
from app.infrastructure.db.models.weather_profile_model import WeatherProfileModel


class PVHourlyRepositoryImpl(IPVProfileRepository):
    """Fetches normalized solar irradiance profiles from the weather_profile table.

    Source column: radiation_wm2 (KNMI variable qg — global solar radiation, W/m²).
    The table stores data at 30-minute resolution; this repository aggregates
    pairs of consecutive 30-min slots into hourly values to match the simulation's
    hourly snapshot resolution.

    The returned profile is normalized to [0.0–1.0] for use as p_max_pu.
    radiation_wm2 is naturally 0 at night (no sun), so no explicit sun-elevation
    filter is needed.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_solar_profile(self, start_date: date, end_date: date) -> list[float]:
        start_dt = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
        end_dt   = datetime.combine(end_date,   time.min).replace(tzinfo=timezone.utc)

        result = await self._session.execute(
            select(WeatherProfileModel)
            .where(
                WeatherProfileModel.timestamp >= start_dt,
                WeatherProfileModel.timestamp < end_dt,
            )
            .order_by(WeatherProfileModel.timestamp)
        )
        rows = list(result.scalars().all())

        if not rows:
            hours = max(1, (end_date - start_date).days * 24)
            return [0.0] * hours

        # Aggregate pairs of 30-min slots → hourly values (average radiation)
        hourly: list[float] = []
        for i in range(0, len(rows) - 1, 2):
            v1 = rows[i].radiation_wm2 or 0.0
            v2 = rows[i + 1].radiation_wm2 or 0.0
            hourly.append((v1 + v2) / 2.0)

        # If an odd row remains (incomplete last hour), include it as-is
        if len(rows) % 2 == 1:
            hourly.append(rows[-1].radiation_wm2 or 0.0)

        max_val = max(hourly)
        if max_val == 0.0:
            return [0.0] * len(hourly)

        return [v / max_val for v in hourly]
