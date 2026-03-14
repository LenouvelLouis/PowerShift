"""PV hourly profile repository — reads irradiance data from pv_hourly table."""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domain.interfaces.pv_profile_repository import IPVProfileRepository
from app.infrastructure.db.models.pv_hourly_model import PVHourlyModel

# The pv_hourly table contains exactly 8760 rows for year 2023 (one per hour).
# Each time key follows YYYYMMDD:HH11 (e.g. '20230601:0811').
_DATA_YEAR = 2023
_TOTAL_HOURS = 8760


def _sun_above_horizon(h_west: float | None, h_east: float | None) -> bool:
    """Return True when the sun is above the horizon (elevation > 0°).

    Uses h_sun_west first, falling back to h_sun_east.
    If no elevation data is available, returns True to avoid silently zeroing output.
    """
    h = h_west if h_west is not None else h_east
    if h is None:
        return True  # no elevation data → don't filter
    return h > 0


class PVHourlyRepositoryImpl(IPVProfileRepository):
    """Fetches solar power profiles from the pv_hourly table.

    Uses p_west + p_east (actual electrical output in W) as the most precise
    per-hour value, rather than g(i) irradiance which requires additional
    conversion (efficiency × area).

    Dates are mapped to 2023 (the only year available in the table).
    If the range wraps past Dec 31, the profile tiles back to Jan 1.
    The returned profile is normalized to [0.0–1.0] for use as p_max_pu.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_solar_profile(self, start_date: date, end_date: date) -> list[float]:
        hours = max(1, (end_date - start_date).days * 24)

        # Map start_date to 2023 and compute its hour-of-year index (0-indexed)
        start_2023 = date(_DATA_YEAR, start_date.month, start_date.day)
        start_idx = (start_2023 - date(_DATA_YEAR, 1, 1)).days * 24

        rows = await self._fetch_hours(start_idx, hours)

        raw = [
            (row.p_west or 0.0) + (row.p_east or 0.0)
            if _sun_above_horizon(row.h_sun_west, row.h_sun_east)
            else 0.0
            for row in rows
        ]

        # Pad with zeros if fewer rows than expected
        if len(raw) < hours:
            raw.extend([0.0] * (hours - len(raw)))

        max_power = max(raw)
        if max_power == 0.0:
            return [0.0] * hours

        return [v / max_power for v in raw]

    async def _fetch_hours(self, start_idx: int, hours: int) -> list[PVHourlyModel]:
        """Fetch exactly `hours` rows starting at `start_idx`, wrapping if needed."""
        first_count = min(hours, _TOTAL_HOURS - start_idx)

        result = await self._session.execute(
            select(PVHourlyModel)
            .order_by(PVHourlyModel.time)
            .offset(start_idx)
            .limit(first_count)
        )
        rows = list(result.scalars().all())

        remaining = hours - first_count
        if remaining > 0:
            result2 = await self._session.execute(
                select(PVHourlyModel)
                .order_by(PVHourlyModel.time)
                .limit(remaining)
            )
            rows.extend(result2.scalars().all())

        return rows
