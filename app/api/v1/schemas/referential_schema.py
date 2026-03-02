"""Pydantic v2 schema for the referential endpoint."""

from __future__ import annotations

from pydantic import BaseModel

from app.api.v1.schemas.demand_schema import DemandResponse
from app.api.v1.schemas.network_schema import NetworkResponse
from app.api.v1.schemas.supply_schema import SupplyResponse


class ReferentialResponse(BaseModel):
    supplies: list[SupplyResponse]
    demands: list[DemandResponse]
    network: list[NetworkResponse]
