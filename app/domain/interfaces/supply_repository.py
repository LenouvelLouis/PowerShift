"""Abstract supply repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.supply.base_supply import BaseSupply


class ISupplyRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[BaseSupply]:
        """Return all supply components."""

    @abstractmethod
    async def get_paginated(self, *, offset: int, limit: int) -> list[BaseSupply]:
        """Return a page of supply components using OFFSET/LIMIT."""

    @abstractmethod
    async def count(self) -> int:
        """Return the total number of supply components."""

    @abstractmethod
    async def get_by_id(self, supply_id: str) -> BaseSupply | None:
        """Return a single supply component by UUID string, or None."""

    @abstractmethod
    async def save(self, supply: BaseSupply) -> BaseSupply:
        """Persist a supply component and return the saved entity."""

    @abstractmethod
    async def create(self, supply: BaseSupply) -> BaseSupply:
        """Insert a new supply component and return it."""

    @abstractmethod
    async def update(self, supply_id: str, supply: BaseSupply) -> BaseSupply | None:
        """Update an existing supply component, return updated entity or None if not found."""

    @abstractmethod
    async def delete(self, supply_id: str) -> bool:
        """Delete a supply component. Returns True if deleted, False if not found."""
