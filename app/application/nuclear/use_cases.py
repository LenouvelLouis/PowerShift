from __future__ import annotations

from datetime import UTC, datetime
import uuid

from app.application.nuclear.schemas import NuclearReactorCreate
from app.domain.nuclear.entities import NuclearReactor
from app.domain.nuclear.exceptions import NuclearReactorNotFoundError
from app.domain.nuclear.ports import NuclearRepository


class CreateNuclearReactorUseCase:
    def __init__(self, repository: NuclearRepository) -> None:
        self._repository = repository

    async def execute(self, payload: NuclearReactorCreate) -> NuclearReactor:
        now = datetime.now(UTC)
        reactor = NuclearReactor(
            id=uuid.uuid4(),
            name=payload.name,
            reactor_type=payload.reactor_type,
            capacity_mw=payload.capacity_mw,
            thermal_power_mw=payload.thermal_power_mw,
            electrical_efficiency=payload.electrical_efficiency,
            p_min_pu=payload.p_min_pu,
            ramp_rate_pu_per_hour=payload.ramp_rate_pu_per_hour,
            min_up_time_h=payload.min_up_time_h,
            min_down_time_h=payload.min_down_time_h,
            startup_cost=payload.startup_cost,
            marginal_cost_per_mwh=payload.marginal_cost_per_mwh,
            fuel_type=payload.fuel_type,
            is_active=payload.is_active,
            created_at=now,
            updated_at=now,
        )
        return await self._repository.create_reactor(reactor)


class GetNuclearReactorUseCase:
    def __init__(self, repository: NuclearRepository) -> None:
        self._repository = repository

    async def execute(self, reactor_id: uuid.UUID) -> NuclearReactor:
        reactor = await self._repository.get_reactor(reactor_id)
        if reactor is None:
            raise NuclearReactorNotFoundError(reactor_id)
        return reactor


class ListNuclearReactorsUseCase:
    def __init__(self, repository: NuclearRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[NuclearReactor]:
        return await self._repository.list_reactors()

