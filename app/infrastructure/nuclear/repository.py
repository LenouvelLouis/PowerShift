from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domain.nuclear.entities import NuclearReactor
from app.infrastructure.db.models.asset_parameters_model import AssetParametersModel
from app.infrastructure.db.models.supply_model import SupplyModel


class NuclearRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_reactor(self, reactor_id: uuid.UUID) -> NuclearReactor | None:
        stmt = (
            select(SupplyModel, AssetParametersModel)
            .join(AssetParametersModel, AssetParametersModel.asset_id == SupplyModel.id)
            .where(SupplyModel.id == reactor_id)
            .where(SupplyModel.type == "nuclear_plant")
            .where(AssetParametersModel.asset_type == "nuclear_plant")
        )
        result = await self._session.execute(stmt)
        row = result.first()
        if row is None:
            return None
        supply, asset_params = row
        return self._to_entity(supply, asset_params)

    async def list_reactors(self) -> list[NuclearReactor]:
        stmt = (
            select(SupplyModel, AssetParametersModel)
            .join(AssetParametersModel, AssetParametersModel.asset_id == SupplyModel.id)
            .where(SupplyModel.type == "nuclear_plant")
            .where(AssetParametersModel.asset_type == "nuclear_plant")
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return [self._to_entity(supply, asset_params) for supply, asset_params in rows]

    async def create_reactor(self, reactor: NuclearReactor) -> NuclearReactor:
        existing = await self.get_reactor(reactor.id)
        if existing is not None:
            return existing

        supply = SupplyModel(
            id=reactor.id,
            name=reactor.name,
            type="nuclear_plant",
            capacity_mw=reactor.capacity_mw,
            status="active" if reactor.is_active else "inactive",
            created_at=reactor.created_at,
            updated_at=reactor.updated_at,
        )
        asset_params = AssetParametersModel(
            asset_id=reactor.id,
            asset_type="nuclear_plant",
            params={
                "reactor_type": reactor.reactor_type,
                "thermal_power_mw": reactor.thermal_power_mw,
                "electrical_efficiency": reactor.electrical_efficiency,
                "p_min_pu": reactor.p_min_pu,
                "ramp_rate_pu_per_hour": reactor.ramp_rate_pu_per_hour,
                "min_up_time_h": reactor.min_up_time_h,
                "min_down_time_h": reactor.min_down_time_h,
                "startup_cost": reactor.startup_cost,
                "marginal_cost_per_mwh": reactor.marginal_cost_per_mwh,
                "fuel_type": reactor.fuel_type,
                "is_active": reactor.is_active,
            },
            created_at=reactor.created_at,
            updated_at=reactor.updated_at,
        )

        self._session.add(supply)
        self._session.add(asset_params)
        await self._session.flush()
        return reactor

    @staticmethod
    def _to_entity(supply: SupplyModel, asset_params: AssetParametersModel) -> NuclearReactor:
        params = asset_params.params or {}
        return NuclearReactor(
            id=supply.id,
            name=supply.name,
            reactor_type=params["reactor_type"],
            capacity_mw=float(supply.capacity_mw),
            thermal_power_mw=float(params["thermal_power_mw"]),
            electrical_efficiency=float(params["electrical_efficiency"]),
            p_min_pu=float(params["p_min_pu"]),
            ramp_rate_pu_per_hour=float(params["ramp_rate_pu_per_hour"]),
            min_up_time_h=int(params["min_up_time_h"]),
            min_down_time_h=int(params["min_down_time_h"]),
            startup_cost=float(params["startup_cost"]),
            marginal_cost_per_mwh=float(params["marginal_cost_per_mwh"]),
            fuel_type=params["fuel_type"],
            is_active=bool(params.get("is_active", True)),
            created_at=supply.created_at,
            updated_at=supply.updated_at,
        )

