"""Abstract interface for simulation persistence (DB)."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.domain.interfaces.simulation_repository import SimulationRunInput, SimulationRunOutput


class ISimulationPersistenceRepository(ABC):
    @abstractmethod
    async def save_request(self, run_input: SimulationRunInput) -> uuid.UUID: ...

    @abstractmethod
    async def save_result(self, request_id: uuid.UUID, output: SimulationRunOutput) -> object: ...

    @abstractmethod
    async def get_result_by_id(self, result_id: uuid.UUID) -> object | None: ...

    @abstractmethod
    async def list_results(self) -> list: ...

    @abstractmethod
    async def list_results_paginated(self, *, offset: int, limit: int) -> list: ...

    @abstractmethod
    async def count_results(self) -> int: ...

    @abstractmethod
    async def get_request_by_id(self, request_id: uuid.UUID) -> object | None: ...

    @abstractmethod
    async def update_request_name(self, request_id: uuid.UUID, name: str) -> None: ...

    @abstractmethod
    async def delete_by_result_id(self, result_id: uuid.UUID) -> bool: ...
