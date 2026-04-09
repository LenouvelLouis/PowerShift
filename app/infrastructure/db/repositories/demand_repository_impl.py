"""Concrete demand repository backed by async SQLAlchemy."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domain.entities.base_component import ComponentStatus
from app.domain.entities.demand.base_demand import BaseDemand
from app.domain.entities.demand.electric_vehicle import ElectricVehicle
from app.domain.entities.demand.house import House
from app.domain.interfaces.demand_repository import IDemandRepository
from app.infrastructure.db.models.demand_model import DemandModel

_TYPE_MAP: dict[str, type[BaseDemand]] = {
    "house": House,
    "electric_vehicle": ElectricVehicle,
}


class DemandRepositoryImpl(IDemandRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── IDemandRepository ────────────────────────────────────────────────────

    async def get_all(self) -> list[BaseDemand]:
        result = await self._session.execute(select(DemandModel))
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def get_by_id(self, demand_id: str) -> BaseDemand | None:
        result = await self._session.execute(
            select(DemandModel).where(DemandModel.id == uuid.UUID(demand_id))
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def save(self, demand: BaseDemand) -> BaseDemand:
        row = self._to_orm(demand)
        self._session.add(row)
        await self._session.flush()
        return self._to_domain(row)

    async def create(self, demand: BaseDemand) -> BaseDemand:
        row = self._to_orm(demand)
        self._session.add(row)
        await self._session.flush()
        return self._to_domain(row)

    async def update(self, demand_id: str, demand: BaseDemand) -> BaseDemand | None:
        result = await self._session.execute(
            select(DemandModel).where(DemandModel.id == uuid.UUID(demand_id))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None

        row.name = demand.name
        row.type = demand.get_type()
        row.load_mw = demand.load_mw
        row.status = demand.status
        row.unit = demand.unit
        row.description = demand.description
        row.updated_at = datetime.now(UTC)

        await self._session.flush()
        return self._to_domain(row)

    async def delete(self, demand_id: str) -> bool:
        result = await self._session.execute(
            select(DemandModel).where(DemandModel.id == uuid.UUID(demand_id))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    # ── Mapping helpers ──────────────────────────────────────────────────────

    @staticmethod
    def build_entity(type_str: str, **kwargs: object) -> BaseDemand:
        """Instantiate the correct BaseDemand subclass from a type string."""
        cls = _TYPE_MAP.get(type_str, House)
        return cls(**kwargs)  # type: ignore[arg-type]

    @staticmethod
    def _to_domain(row: DemandModel) -> BaseDemand:
        return DemandRepositoryImpl.build_entity(
            row.type,
            id=row.id,
            name=row.name,
            load_mw=row.load_mw,
            status=ComponentStatus(row.status),
            unit=row.unit,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_orm(demand: BaseDemand) -> DemandModel:
        now = datetime.now(UTC)
        return DemandModel(
            id=demand.id,
            name=demand.name,
            type=demand.get_type(),
            load_mw=demand.load_mw,
            status=demand.status,
            unit=demand.unit,
            description=demand.description,
            created_at=demand.created_at or now,
            updated_at=demand.updated_at or now,
        )
