from __future__ import annotations

import uuid
from typing import Protocol

from app.domain.nuclear.entities import NuclearReactor


class NuclearRepository(Protocol):
    async def get_reactor(self, reactor_id: uuid.UUID) -> NuclearReactor | None:
        ...

    async def list_reactors(self) -> list[NuclearReactor]:
        ...

    async def create_reactor(self, reactor: NuclearReactor) -> NuclearReactor:
        ...

