"""PyPSA network builder — runs simulation in a thread-pool executor."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.domain.interfaces.simulation_repository import (
    ISimulationRepository,
    SimulationRequest,
    SimulationResult,
)
from app.infrastructure.simulation.pypsa_adapter import (
    AbstractGridSimulation,
    SimulationConfig,
    SimulationResult as AdapterResult,
)


class _DefaultPyPSASimulation(AbstractGridSimulation):
    """Concrete PyPSA backend.

    PyPSA is synchronous and CPU/I/O-bound (calls C-extension GLPK/HiGHS),
    so it must be run inside a ThreadPoolExecutor to avoid blocking the event loop.
    """

    def run_sync(self, config: SimulationConfig) -> AdapterResult:
        import pypsa  # type: ignore[import-untyped]

        n = pypsa.Network()
        n.set_snapshots(range(config.snapshot_hours))

        # BUS CONVENTION (POC — Sprint 1):
        # All components connect to "main_bus" (single shared bus, v_nom=380).
        # Future migration: Network group will introduce bus_mv / bus_lv topology.
        # Each group only needs to update to_pypsa_params() in their own entity — nothing else changes.
        n.add("Bus", "main_bus", v_nom=380.0)

        # Generic — each group controls their own PyPSA params via to_pypsa_params()
        total_supply = 0.0
        for supply in config.supplies:
            n.add("Generator", supply.name, **supply.to_pypsa_params())
            total_supply += supply.capacity_mw * config.snapshot_hours

        total_demand = 0.0
        for demand in config.demands:
            n.add("Load", demand.name, **demand.to_pypsa_params())
            total_demand += demand.load_mw * config.snapshot_hours

        for component in config.network_components:
            pypsa_type = "Transformer" if component.get_network_type() == "transformer" else "Line"
            n.add(pypsa_type, component.name, **component.to_pypsa_params())

        try:
            n.optimize()
            status = "optimal"
        except Exception:
            status = "infeasible"

        balance = total_supply - total_demand
        return AdapterResult(
            total_supply_mwh=total_supply,
            total_demand_mwh=total_demand,
            balance_mwh=balance,
            status=status,
        )


_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pypsa")


class PyPSANetworkBuilder(ISimulationRepository):
    """Runs PyPSA inside a ThreadPoolExecutor so the async loop stays free."""

    def __init__(self, simulation: AbstractGridSimulation | None = None) -> None:
        self._simulation = simulation or _DefaultPyPSASimulation()

    async def run(self, request: SimulationRequest) -> SimulationResult:
        config = SimulationConfig(snapshot_hours=request.snapshot_hours)
        loop = asyncio.get_running_loop()
        result: AdapterResult = await loop.run_in_executor(
            _executor,
            self._simulation.run_sync,
            config,
        )
        return SimulationResult(
            total_supply_mwh=result.total_supply_mwh,
            total_demand_mwh=result.total_demand_mwh,
            balance_mwh=result.balance_mwh,
            status=result.status,
        )
