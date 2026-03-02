"""Abstract demand repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.demand.base_demand import BaseDemand


class IDemandRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[BaseDemand]:
        """Return all demand components."""

    @abstractmethod
    async def get_by_id(self, demand_id: str) -> BaseDemand | None:
        """Return a single demand component by UUID string, or None."""

    @abstractmethod
    async def save(self, demand: BaseDemand) -> BaseDemand:
        """Persist a demand component and return the saved entity."""
