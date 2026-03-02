"""Dependency injection wiring — the single place where api touches infra."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.referential_service import ReferentialService
from app.application.services.simulation_service import SimulationService
from app.domain.use_cases.get_referential import GetReferentialUseCase
from app.domain.use_cases.run_simulation import RunSimulationUseCase
from app.infrastructure.db.connection import get_db
from app.infrastructure.db.repositories.demand_repository_impl import DemandRepositoryImpl
from app.infrastructure.db.repositories.network_repository_impl import NetworkRepositoryImpl
from app.infrastructure.db.repositories.supply_repository_impl import SupplyRepositoryImpl
from app.infrastructure.simulation.network_builder import PyPSANetworkBuilder

# ── DB session (shared by all repos via FastAPI deduplication) ───────────────

DbSession = Annotated[AsyncSession, Depends(get_db)]


# ── Repositories ─────────────────────────────────────────────────────────────

def get_supply_repository(db: DbSession) -> SupplyRepositoryImpl:
    return SupplyRepositoryImpl(db)


def get_demand_repository(db: DbSession) -> DemandRepositoryImpl:
    return DemandRepositoryImpl(db)


def get_network_repository(db: DbSession) -> NetworkRepositoryImpl:
    return NetworkRepositoryImpl(db)


# ── Use cases ────────────────────────────────────────────────────────────────

def get_referential_use_case(
    supply_repo: Annotated[SupplyRepositoryImpl, Depends(get_supply_repository)],
    demand_repo: Annotated[DemandRepositoryImpl, Depends(get_demand_repository)],
    network_repo: Annotated[NetworkRepositoryImpl, Depends(get_network_repository)],
) -> GetReferentialUseCase:
    return GetReferentialUseCase(
        supply_repo=supply_repo,
        demand_repo=demand_repo,
        network_repo=network_repo,
    )


def get_simulation_use_case() -> RunSimulationUseCase:
    return RunSimulationUseCase(simulation_repo=PyPSANetworkBuilder())


# ── Services ─────────────────────────────────────────────────────────────────

def get_referential_service(
    use_case: Annotated[GetReferentialUseCase, Depends(get_referential_use_case)],
) -> ReferentialService:
    return ReferentialService(use_case=use_case)


def get_simulation_service(
    use_case: Annotated[RunSimulationUseCase, Depends(get_simulation_use_case)],
) -> SimulationService:
    return SimulationService(use_case=use_case)
