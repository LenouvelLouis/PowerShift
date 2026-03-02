"""Abstract supply repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.supply.base_supply import BaseSupply


class ISupplyRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[BaseSupply]:
        """Return all supply components."""

    @abstractmethod
    async def get_by_id(self, supply_id: str) -> BaseSupply | None:
        """Return a single supply component by UUID string, or None."""

    @abstractmethod
    async def save(self, supply: BaseSupply) -> BaseSupply:
        """Persist a supply component and return the saved entity."""
