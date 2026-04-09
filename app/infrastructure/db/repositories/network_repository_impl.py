"""Concrete network repository backed by async SQLAlchemy."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domain.entities.base_component import ComponentStatus
from app.domain.entities.network.base_network import BaseNetwork
from app.domain.entities.network.cable import Cable
from app.domain.entities.network.transformer import Transformer
from app.domain.interfaces.network_repository import INetworkRepository
from app.infrastructure.db.models.network_model import NetworkModel

_TYPE_MAP: dict[str, type[BaseNetwork]] = {
    "transformer": Transformer,
    "cable": Cable,
}


class NetworkRepositoryImpl(INetworkRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── INetworkRepository ───────────────────────────────────────────────────

    async def get_all(self) -> list[BaseNetwork]:
        result = await self._session.execute(select(NetworkModel))
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def get_by_id(self, component_id: str) -> BaseNetwork | None:
        result = await self._session.execute(
            select(NetworkModel).where(NetworkModel.id == uuid.UUID(component_id))
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def create(self, component: BaseNetwork) -> BaseNetwork:
        row = self._to_orm(component)
        self._session.add(row)
        await self._session.flush()
        return self._to_domain(row)

    async def update(self, component_id: str, component: BaseNetwork) -> BaseNetwork | None:
        result = await self._session.execute(
            select(NetworkModel).where(NetworkModel.id == uuid.UUID(component_id))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None

        row.name = component.name
        row.type = component.get_network_type()
        row.voltage_kv = component.voltage_kv
        row.capacity_mva = component.capacity_mva
        row.losses_kw = component.losses_kw
        row.status = component.status
        row.unit = component.unit
        row.description = component.description
        row.updated_at = datetime.now(UTC)

        if isinstance(component, Transformer):
            row.voltage_hv_kv = component.voltage_hv_kv
            row.voltage_lv_kv = component.voltage_lv_kv
        elif isinstance(component, Cable):
            row.length_km = component.length_km
            row.resistance_ohm_per_km = component.resistance_ohm_per_km
            row.reactance_ohm_per_km = component.reactance_ohm_per_km

        await self._session.flush()
        return self._to_domain(row)

    async def delete(self, component_id: str) -> bool:
        result = await self._session.execute(
            select(NetworkModel).where(NetworkModel.id == uuid.UUID(component_id))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    # ── Mapping helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _to_domain(row: NetworkModel) -> BaseNetwork:
        common = dict(
            id=row.id,
            name=row.name,
            voltage_kv=row.voltage_kv,
            capacity_mva=row.capacity_mva or 0.0,
            losses_kw=row.losses_kw,
            status=ComponentStatus(row.status),
            unit=row.unit,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        if row.type == "transformer":
            return Transformer(
                **common,
                voltage_hv_kv=row.voltage_hv_kv or row.voltage_kv,
                voltage_lv_kv=row.voltage_lv_kv or 0.4,
            )
        # Default: cable
        return Cable(
            **common,
            length_km=row.length_km or 0.0,
            resistance_ohm_per_km=row.resistance_ohm_per_km or 0.0,
            reactance_ohm_per_km=row.reactance_ohm_per_km or 0.0,
        )

    @staticmethod
    def _to_orm(component: BaseNetwork) -> NetworkModel:
        now = datetime.now(UTC)
        row = NetworkModel(
            id=component.id,
            name=component.name,
            type=component.get_network_type(),
            voltage_kv=component.voltage_kv,
            capacity_mva=component.capacity_mva,
            losses_kw=component.losses_kw,
            status=component.status,
            unit=component.unit,
            description=component.description,
            created_at=component.created_at or now,
            updated_at=component.updated_at or now,
        )
        if isinstance(component, Transformer):
            row.voltage_hv_kv = component.voltage_hv_kv
            row.voltage_lv_kv = component.voltage_lv_kv
        elif isinstance(component, Cable):
            row.length_km = component.length_km
            row.resistance_ohm_per_km = component.resistance_ohm_per_km
            row.reactance_ohm_per_km = component.reactance_ohm_per_km
        return row
