"""Abstract interface for solar PV profile data."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date


class IPVProfileRepository(ABC):
    @abstractmethod
    async def get_solar_profile(self, start_date: date, end_date: date) -> list[float]:
        """Return a normalized irradiance profile [0.0–1.0] covering [start_date, end_date[."""
