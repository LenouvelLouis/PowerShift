"""Aggregate all v1 endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import demand, network, referential, simulation, supply

router = APIRouter()

router.include_router(referential.router)
router.include_router(supply.router)
router.include_router(demand.router)
router.include_router(network.router)
router.include_router(simulation.router)
