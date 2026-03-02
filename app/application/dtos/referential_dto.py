"""Referential DTO — application layer."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.dtos.demand_dto import DemandDTO
from app.application.dtos.network_dto import NetworkDTO
from app.application.dtos.supply_dto import SupplyDTO


@dataclass
class ReferentialDTO:
    supplies: list[SupplyDTO]
    demands: list[DemandDTO]
    network: list[NetworkDTO]
