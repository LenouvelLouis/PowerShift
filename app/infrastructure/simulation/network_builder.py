"""PyPSA network builder — runs simulation in a thread-pool executor."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.domain.interfaces.load_profile_provider import ILoadProfileProvider
from app.domain.interfaces.simulation_repository import (
    ISimulationRepository,
    SimulationRunInput,
    SimulationRunOutput,
)
from app.infrastructure.simulation.pypsa_adapter import (
    AbstractGridSimulation,
    AdapterOutput,
    SimulationConfig,
)


class _DefaultPyPSASimulation(AbstractGridSimulation):
    """Concrete PyPSA backend.

    PyPSA is synchronous and CPU/I/O-bound (calls C-extension GLPK/HiGHS),
    so it must be run inside a ThreadPoolExecutor to avoid blocking the event loop.
    """

    def run_sync(self, config: SimulationConfig) -> AdapterOutput:
        import pypsa  # type: ignore[import-untyped]

        n = pypsa.Network()
        n.set_snapshots(range(config.snapshot_hours))

        # BUS CONVENTION (POC — Sprint 1):
        # All components connect to "main_bus" (single shared bus, v_nom=380).
        # Future migration: Network group will introduce bus_mv / bus_lv topology.
        # Each group only needs to update to_pypsa_params() in their own entity — nothing else changes.
        n.add("Bus", "main_bus", v_nom=380.0)

        # Generic — each group controls their own PyPSA params via to_pypsa_params()
        for supply in config.supplies:
            n.add("Generator", supply.name, **supply.to_pypsa_params())

        for demand in config.demands:
            profile = config.load_profiles.get(demand.name)
            params = demand.to_pypsa_params(profile=profile)
            # Convert list p_set to a pandas Series aligned with network snapshots
            if isinstance(params.get("p_set"), list):
                import pandas as pd  # noqa: PLC0415
                params["p_set"] = pd.Series(params["p_set"], index=n.snapshots)
            n.add("Load", demand.name, **params)

        for component in config.network_components:
            pypsa_type = "Transformer" if component.get_network_type() == "transformer" else "Line"
            n.add(pypsa_type, component.name, **component.to_pypsa_params())

        try:
            n.optimize(solver_name=config.solver, include_objective_constant=False)
            status = "optimal"
            objective_value = float(n.objective) if hasattr(n, "objective") else 0.0
            generators_t = (
                {gen: {"p": n.generators_t.p[gen].tolist()} for gen in n.generators_t.p.columns}
                if not n.generators_t.p.empty
                else {}
            )
            loads_t = (
                {load: {"p": n.loads_t.p_set[load].tolist()} for load in n.loads_t.p_set.columns}
                if not n.loads_t.p_set.empty
                else {}
            )
            capacity_factors = {
                gen: float(
                    n.generators_t.p[gen].sum()
                    / (n.generators.at[gen, "p_nom"] * config.snapshot_hours)
                )
                for gen in n.generators.index
                if gen in n.generators_t.p.columns and n.generators.at[gen, "p_nom"] > 0
            }
            total_supply = float(n.generators_t.p.sum().sum()) if not n.generators_t.p.empty else 0.0
            # p_set scalar → stored in n.loads (static), not n.loads_t (time-series)
            if not n.loads_t.p_set.empty:
                total_demand = float(n.loads_t.p_set.sum().sum())
            else:
                total_demand = float(n.loads.p_set.sum()) * config.snapshot_hours
            result_json = {
                "generators_t": generators_t,
                "loads_t": loads_t,
                "capacity_factors": capacity_factors,
                "violations": {"overloads": [], "overvoltages": []},
                "objective_value": objective_value,
            }
        except Exception as e:
            status = "error"
            objective_value = 0.0
            total_supply = 0.0
            total_demand = 0.0
            result_json = {"error": str(e)}

        balance = total_supply - total_demand
        return AdapterOutput(
            total_supply_mwh=total_supply,
            total_demand_mwh=total_demand,
            balance_mwh=balance,
            status=status,
            objective_value=objective_value,
            result_json=result_json,
        )


_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pypsa")


class PyPSANetworkBuilder(ISimulationRepository):
    """Runs PyPSA inside a ThreadPoolExecutor so the async loop stays free."""

    def __init__(
        self,
        simulation: AbstractGridSimulation | None = None,
        load_profile_provider: ILoadProfileProvider | None = None,
    ) -> None:
        self._simulation = simulation or _DefaultPyPSASimulation()
        self._load_profile_provider = load_profile_provider

    async def run(
        self,
        run_input: SimulationRunInput,
        supplies: list,
        demands: list,
        network_components: list,
    ) -> SimulationRunOutput:
        # Fetch load profiles async (before entering the sync thread executor)
        load_profiles: dict[str, list[float]] = {}
        if self._load_profile_provider is not None:
            for demand in demands:
                load_profiles[demand.name] = await self._load_profile_provider.get_profile(
                    demand.get_type(), run_input.snapshot_hours
                )

        config = SimulationConfig(
            snapshot_hours=run_input.snapshot_hours,
            solver=run_input.solver,
            supplies=supplies,
            demands=demands,
            network_components=network_components,
            load_profiles=load_profiles,
        )
        loop = asyncio.get_running_loop()
        result: AdapterOutput = await loop.run_in_executor(
            _executor,
            self._simulation.run_sync,
            config,
        )
        return SimulationRunOutput(
            total_supply_mwh=result.total_supply_mwh,
            total_demand_mwh=result.total_demand_mwh,
            balance_mwh=result.balance_mwh,
            status=result.status,
            objective_value=result.objective_value,
            result_json=result.result_json,
        )
