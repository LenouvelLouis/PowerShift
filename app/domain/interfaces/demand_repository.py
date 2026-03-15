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

    @abstractmethod
    async def create(self, demand: BaseDemand) -> BaseDemand:
        """Insert a new demand component and return it."""

    @abstractmethod
    async def update(self, demand_id: str, demand: BaseDemand) -> BaseDemand | None:
        """Update an existing demand component, return updated entity or None if not found."""

    @abstractmethod
    async def delete(self, demand_id: str) -> bool:
        """Delete a demand component. Returns True if deleted, False if not found."""
