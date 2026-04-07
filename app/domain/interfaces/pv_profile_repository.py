"""Abstract interface for solar PV profile data."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date


class IPVProfileRepository(ABC):
    @abstractmethod
    async def get_solar_profile(self, start_date: date, end_date: date) -> list[float]:
        """Return a normalized irradiance profile [0.0–1.0] covering [start_date, end_date]."""

    @abstractmethod
    async def get_wind_profile(self, start_date: date, end_date: date) -> list[float]:
        """Return a normalized wind power profile [0.0–1.0] covering [start_date, end_date].

        Uses a generic cubic power law (cut-in=3 m/s, rated=12 m/s, cut-out=25 m/s)
        applied to KNMI wind_speed_ms measurements, extrapolated from 10 m to 80 m hub height.
        """
