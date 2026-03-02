"""Use case: fetch the referential (all supplies, demands, and network components)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.domain.entities.demand.base_demand import BaseDemand
from app.domain.entities.network.base_network import BaseNetwork
from app.domain.entities.supply.base_supply import BaseSupply
from app.domain.interfaces.demand_repository import IDemandRepository
from app.domain.interfaces.network_repository import INetworkRepository
from app.domain.interfaces.supply_repository import ISupplyRepository


@dataclass
class ReferentialResult:
    supplies: list[BaseSupply]
    demands: list[BaseDemand]
    network: list[BaseNetwork]


class GetReferentialUseCase:
    def __init__(
        self,
        supply_repo: ISupplyRepository,
        demand_repo: IDemandRepository,
        network_repo: INetworkRepository,
    ) -> None:
        self._supply_repo = supply_repo
        self._demand_repo = demand_repo
        self._network_repo = network_repo

    async def execute(self) -> ReferentialResult:
        supplies, demands, network = await asyncio.gather(
            self._supply_repo.get_all(),
            self._demand_repo.get_all(),
            self._network_repo.get_all(),
        )
        return ReferentialResult(supplies=supplies, demands=demands, network=network)
