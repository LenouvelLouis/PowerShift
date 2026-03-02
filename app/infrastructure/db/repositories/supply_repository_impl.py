"""Concrete supply repository backed by async SQLAlchemy."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.base_component import ComponentStatus
from app.domain.entities.supply.base_supply import BaseSupply
from app.domain.entities.supply.nuclear_plant import NuclearPlant
from app.domain.entities.supply.solar_panel import SolarPanel
from app.domain.entities.supply.wind_turbine import WindTurbine
from app.domain.interfaces.supply_repository import ISupplyRepository
from app.infrastructure.db.models.supply_model import SupplyModel

_TYPE_MAP: dict[str, type[BaseSupply]] = {
    "wind_turbine": WindTurbine,
    "solar_panel": SolarPanel,
    "nuclear_plant": NuclearPlant,
}


class SupplyRepositoryImpl(ISupplyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── ISupplyRepository ────────────────────────────────────────────────────

    async def get_all(self) -> list[BaseSupply]:
        result = await self._session.execute(select(SupplyModel))
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def get_by_id(self, supply_id: str) -> BaseSupply | None:
        result = await self._session.execute(
            select(SupplyModel).where(SupplyModel.id == uuid.UUID(supply_id))
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def save(self, supply: BaseSupply) -> BaseSupply:
        row = self._to_orm(supply)
        self._session.add(row)
        await self._session.flush()
        return self._to_domain(row)

    # ── Mapping helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _to_domain(row: SupplyModel) -> BaseSupply:
        cls = _TYPE_MAP.get(row.type, WindTurbine)
        return cls(
            id=row.id,
            name=row.name,
            capacity_mw=row.capacity_mw,
            efficiency=row.efficiency,
            status=ComponentStatus(row.status),
            unit=row.unit,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_orm(supply: BaseSupply) -> SupplyModel:
        now = datetime.now(timezone.utc)
        return SupplyModel(
            id=supply.id,
            name=supply.name,
            type=supply.get_type(),
            capacity_mw=supply.capacity_mw,
            efficiency=supply.efficiency,
            status=supply.status,
            unit=supply.unit,
            description=supply.description,
            created_at=supply.created_at or now,
            updated_at=supply.updated_at or now,
        )
