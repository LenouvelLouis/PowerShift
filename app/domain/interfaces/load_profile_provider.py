"""Interface for external load profile providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ILoadProfileProvider(ABC):
    @abstractmethod
    async def get_profile(self, demand_type: str, hours: int) -> list[float]:
        """Return a normalized load profile of length `hours` (values 0.0–1.0)."""
