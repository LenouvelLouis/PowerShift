"""Abstract network repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.network.base_network import BaseNetwork


class INetworkRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[BaseNetwork]:
        """Return all network components."""

    @abstractmethod
    async def get_paginated(self, *, offset: int, limit: int) -> list[BaseNetwork]:
        """Return a page of network components using OFFSET/LIMIT."""

    @abstractmethod
    async def count(self) -> int:
        """Return the total number of network components."""

    @abstractmethod
    async def get_by_id(self, component_id: str) -> BaseNetwork | None:
        """Return a single network component by UUID string, or None."""

    @abstractmethod
    async def create(self, component: BaseNetwork) -> BaseNetwork:
        """Persist a new network component and return the saved entity."""

    @abstractmethod
    async def update(self, component_id: str, component: BaseNetwork) -> BaseNetwork | None:
        """Update an existing network component and return it, or None if not found."""

    @abstractmethod
    async def delete(self, component_id: str) -> bool:
        """Delete a network component by UUID string. Returns True if deleted, False if not found."""
