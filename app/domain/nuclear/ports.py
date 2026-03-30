from __future__ import annotations

from typing import Protocol
import uuid

from app.domain.nuclear.entities import NuclearReactor


class NuclearRepository(Protocol):
    async def get_reactor(self, reactor_id: uuid.UUID) -> NuclearReactor | None:
        ...

    async def list_reactors(self) -> list[NuclearReactor]:
        ...

    async def create_reactor(self, reactor: NuclearReactor) -> NuclearReactor:
        ...

