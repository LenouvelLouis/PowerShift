"""Referential service — orchestrates use case and maps domain → DTO."""

from __future__ import annotations

from app.application.dtos.demand_dto import DemandDTO
from app.application.dtos.network_dto import NetworkDTO
from app.application.dtos.referential_dto import ReferentialDTO
from app.application.dtos.supply_dto import SupplyDTO
from app.domain.entities.demand.base_demand import BaseDemand
from app.domain.entities.network.base_network import BaseNetwork
from app.domain.entities.network.cable import Cable
from app.domain.entities.network.transformer import Transformer
from app.domain.entities.supply.base_supply import BaseSupply
from app.domain.use_cases.get_referential import GetReferentialUseCase


class ReferentialService:
    def __init__(self, use_case: GetReferentialUseCase) -> None:
        self._use_case = use_case

    async def get_referential(self) -> ReferentialDTO:
        result = await self._use_case.execute()
        return ReferentialDTO(
            supplies=[self._supply_to_dto(s) for s in result.supplies],
            demands=[self._demand_to_dto(d) for d in result.demands],
            network=[self._network_to_dto(n) for n in result.network],
        )

    @staticmethod
    def _supply_to_dto(supply: BaseSupply) -> SupplyDTO:
        return SupplyDTO(
            id=supply.id,
            name=supply.name,
            type=supply.get_type(),
            capacity_mw=supply.capacity_mw,
            efficiency=supply.efficiency,
            status=supply.status,
            unit=supply.unit,
            description=supply.description,
            carrier=supply.get_carrier(),
            created_at=supply.created_at,
            updated_at=supply.updated_at,
        )

    @staticmethod
    def _demand_to_dto(demand: BaseDemand) -> DemandDTO:
        return DemandDTO(
            id=demand.id,
            name=demand.name,
            type=demand.get_type(),
            load_mw=demand.load_mw,
            status=demand.status,
            unit=demand.unit,
            description=demand.description,
            created_at=demand.created_at,
            updated_at=demand.updated_at,
        )

    @staticmethod
    def _network_to_dto(component: BaseNetwork) -> NetworkDTO:
        voltage_hv_kv = component.voltage_hv_kv if isinstance(component, Transformer) else None
        voltage_lv_kv = component.voltage_lv_kv if isinstance(component, Transformer) else None
        length_km = component.length_km if isinstance(component, Cable) else None
        resistance_ohm_per_km = component.resistance_ohm_per_km if isinstance(component, Cable) else None
        reactance_ohm_per_km = component.reactance_ohm_per_km if isinstance(component, Cable) else None

        return NetworkDTO(
            id=component.id,
            name=component.name,
            type=component.get_network_type(),
            voltage_kv=component.voltage_kv,
            capacity_mva=component.capacity_mva,
            losses_kw=component.losses_kw,
            voltage_hv_kv=voltage_hv_kv,
            voltage_lv_kv=voltage_lv_kv,
            length_km=length_km,
            resistance_ohm_per_km=resistance_ohm_per_km,
            reactance_ohm_per_km=reactance_ohm_per_km,
            status=component.status,
            unit=component.unit,
            description=component.description,
            created_at=component.created_at,
            updated_at=component.updated_at,
        )
