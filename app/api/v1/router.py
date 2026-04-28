"""Aggregate all v1 endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.auth import require_api_key
from app.api.v1.endpoints import cache, demand, network, referential, simulation, supply

router = APIRouter(dependencies=[Depends(require_api_key)])

router.include_router(referential.router)
router.include_router(supply.router)
router.include_router(demand.router)
router.include_router(network.router)
router.include_router(simulation.router)
router.include_router(cache.router)
