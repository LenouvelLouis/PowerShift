"""PyPSA network builder — runs simulation in a thread-pool executor."""

from __future__ import annotations

import asyncio
import re
from concurrent.futures import ThreadPoolExecutor

import logging

from app.application.wind.schemas import CalculatePowerRequest
from app.application.wind.use_cases import CalculateWindPowerUseCase
from app.domain.interfaces.load_profile_provider import ILoadProfileProvider
from app.domain.interfaces.pv_profile_repository import IPVProfileRepository
from app.domain.interfaces.simulation_repository import (
    ISimulationRepository,
    SimulationRunInput,
    SimulationRunOutput,
)
from app.domain.wind.exceptions import WindAssetNotFoundError, WindTurbineError
from app.infrastructure.simulation.pypsa_adapter import (
    AbstractGridSimulation,
    AdapterOutput,
    SimulationConfig,
)
from app.infrastructure.wind.repository import WindTurbineRepositoryImpl
from app.infrastructure.nuclear.repository import NuclearRepositoryImpl
from app.domain.nuclear.services import NuclearConstraintsBuilder

_log = logging.getLogger(__name__)


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
            params = supply.to_pypsa_params()

            solar_profile = config.solar_profiles.get(supply.name)
            if solar_profile is not None:
                # PyPSA requires p_max_pu to be a pd.Series indexed on network snapshots
                # to align the solar profile temporally with the optimization timesteps.
                # Imported inline to avoid making pandas a hard dependency of the whole module.
                import pandas as pd  # noqa: PLC0415

                params["p_max_pu"] = pd.Series(solar_profile, index=n.snapshots)

            wind_profile = config.wind_profiles.get(supply.name)
            if wind_profile is not None:
                import pandas as pd  # noqa: PLC0415

                params["p_max_pu"] = pd.Series(wind_profile, index=n.snapshots)

            nuclear_params = config.nuclear_constraints.get(supply.name)
            if nuclear_params is not None:
                params.update(nuclear_params)
                # nuclear_params already contains p_min_pu, marginal_cost, etc.
                # Do NOT set p_max_pu — nuclear dispatches freely up to p_nom

            params.update(config.pypsa_params.get(supply.name, {}))
            n.add("Generator", supply.name, **params)

        for demand in config.demands:
            profile = config.load_profiles.get(demand.name)
            params = demand.to_pypsa_params(profile=profile)
            # PyPSA requires p_set to be a pd.Series indexed on network snapshots.
            # Imported inline to avoid making pandas a hard dependency of the whole module.
            if isinstance(params.get("p_set"), list):
                import pandas as pd  # noqa: PLC0415

                params["p_set"] = pd.Series(params["p_set"], index=n.snapshots)
            n.add("Load", demand.name, **params)

        for component in config.network_components:
            pypsa_type = "Transformer" if component.get_network_type() == "transformer" else "Line"
            comp_params = component.to_pypsa_params()
            comp_params.update(config.pypsa_params.get(component.name, {}))
            n.add(pypsa_type, component.name, **comp_params)

        try:
            optimize_result = n.optimize(solver_name=config.solver)
            if isinstance(optimize_result, tuple) and optimize_result[1] == "infeasible":
                status = "infeasible"
                objective_value = 0.0
                total_supply = total_demand = 0.0
                result_json = {"error": "Optimization infeasible — supply cannot meet demand"}
            else:
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
            error_message = str(e)
            lowered = error_message.lower()
            solver_error_hints = (
                "solver",
                "not installed",
                "not found",
                "unknown solver",
                "no executable",
                "license",
                "xpress",
                "cplex",
                "cbc",
                "highs",
            )
            error_type = "solver_error" if any(hint in lowered for hint in solver_error_hints) else "runtime_error"
            compact_error = re.sub(r"\s+", " ", error_message).strip()
            status = "error"
            objective_value = 0.0
            total_supply = 0.0
            total_demand = 0.0
            result_json = {
                "error": compact_error,
                "error_type": error_type,
                "solver": config.solver,
            }

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


# Groningen Eelde — the single station backing the weather_profile table.
# Used as a named constant so the hardcoded value is explicit and easy to locate.
_WEATHER_STATION = "06280"


class PyPSANetworkBuilder(ISimulationRepository):
    """Runs PyPSA inside a ThreadPoolExecutor so the async loop stays free."""

    def __init__(
        self,
        simulation: AbstractGridSimulation | None = None,
        load_profile_provider: ILoadProfileProvider | None = None,
        pv_profile_repo: IPVProfileRepository | None = None,
        wind_repo: WindTurbineRepositoryImpl | None = None,
        nuclear_repo: NuclearRepositoryImpl | None = None,
    ) -> None:
        self._simulation = simulation or _DefaultPyPSASimulation()
        self._load_profile_provider = load_profile_provider
        self._pv_profile_repo = pv_profile_repo
        self._wind_repo = wind_repo
        self._nuclear_repo = nuclear_repo

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
                    demand.get_type(), run_input.snapshot_hours, run_input.start_date
                )

        # Hourly load overrides replace auto-generated profiles (keyed by demand UUID)
        for demand in demands:
            demand_id = str(demand.id)
            if demand_id in run_input.hourly_load_overrides:
                load_profiles[demand.name] = run_input.hourly_load_overrides[demand_id]

        # Collect data-quality warnings to surface in result_json
        profile_warnings: list[str] = []

        # Fetch solar irradiance profiles from weather_profile table
        solar_profiles: dict[str, list[float]] = {}
        if (
            self._pv_profile_repo is not None
            and run_input.start_date is not None
            and run_input.end_date is not None
        ):
            for supply in supplies:
                if supply.get_carrier() == "solar":
                    profile = await self._pv_profile_repo.get_solar_profile(
                        run_input.start_date, run_input.end_date
                    )
                    solar_profiles[supply.name] = profile
                    if all(v == 0.0 for v in profile):
                        msg = (
                            f"Solar asset '{supply.name}': no irradiance data found for "
                            f"{run_input.start_date} → {run_input.end_date}. "
                            "Profile is all-zero — check weather_profile table coverage."
                        )
                        profile_warnings.append(msg)

        # Compute wind power profiles from KNMI measurements
        wind_profiles: dict[str, list[float]] = {}
        if (
            self._wind_repo is not None
            and run_input.start_date is not None
            and run_input.end_date is not None
        ):
            for supply in supplies:
                if supply.get_carrier() == "wind":
                    wind_use_case = CalculateWindPowerUseCase(self._wind_repo)
                    try:
                        result = await wind_use_case.execute(
                            CalculatePowerRequest(
                                asset_id=supply.id,
                                station_code=_WEATHER_STATION,
                                start=run_input.start_date,
                                end=run_input.end_date,
                            )
                        )
                        rated_kw = supply.capacity_mw * 1000
                        wind_profile = [
                            min(pt.power_kw / rated_kw, 1.0) if rated_kw > 0 else 0.0
                            for pt in result.power_series
                        ]
                        wind_profiles[supply.name] = wind_profile
                        if not result.power_series or all(v == 0.0 for v in wind_profile):
                            msg = (
                                f"Wind asset '{supply.name}': no measurement data found for "
                                f"{run_input.start_date} → {run_input.end_date}. "
                                "Running at rated capacity (p_nom)."
                            )
                            profile_warnings.append(msg)
                    except (WindAssetNotFoundError, WindTurbineError) as exc:
                        _log.warning(
                            "Wind profile unavailable for '%s': %s — running at p_nom.",
                            supply.name, exc,
                        )
                        profile_warnings.append(
                            f"Wind asset '{supply.name}': profile unavailable ({exc}). "
                            "Running at rated capacity (p_nom)."
                        )

        # Build nuclear operational constraints
        nuclear_constraints: dict[str, dict] = {}
        if self._nuclear_repo is not None:
            for supply in supplies:
                if supply.get_carrier() == "nuclear":
                    reactor = await self._nuclear_repo.get_reactor(supply.id)
                    if reactor is not None:
                        nuclear_constraints[supply.name] = NuclearConstraintsBuilder.build_pypsa_params(
                            reactor
                        )

        config = SimulationConfig(
            snapshot_hours=run_input.snapshot_hours,
            solver=run_input.solver,
            supplies=supplies,
            demands=demands,
            network_components=network_components,
            load_profiles=load_profiles,
            solar_profiles=solar_profiles,
            wind_profiles=wind_profiles,
            nuclear_constraints=nuclear_constraints,
            pypsa_params=run_input.pypsa_params or {},
            optimization_objective=run_input.optimization_objective,
        )
        loop = asyncio.get_running_loop()
        result: AdapterOutput = await loop.run_in_executor(
            _executor,
            self._simulation.run_sync,
            config,
        )
        if profile_warnings:
            result.result_json["warnings"] = profile_warnings

        return SimulationRunOutput(
            total_supply_mwh=result.total_supply_mwh,
            total_demand_mwh=result.total_demand_mwh,
            balance_mwh=result.balance_mwh,
            status=result.status,
            objective_value=result.objective_value,
            result_json=result.result_json,
        )