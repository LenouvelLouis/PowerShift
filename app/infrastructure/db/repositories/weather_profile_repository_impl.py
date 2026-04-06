"""Weather profile repository — reads data from the weather_profile table."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, time, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domain.interfaces.pv_profile_repository import IPVProfileRepository
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
        # Inclusive: start 00:00 → end 23:30 (last slot of end_date)
        start_dt = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
        end_dt   = datetime.combine(end_date,   time.max).replace(tzinfo=timezone.utc)
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
            slot_30 = bucket_start + timedelta(minutes=30)
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
