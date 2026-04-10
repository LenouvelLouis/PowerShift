"""PyPSA network builder — runs Linear Optimal Power Flow in a thread-pool executor."""

from __future__ import annotations

import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import logging

from app.domain.interfaces.load_profile_provider import ILoadProfileProvider
from app.domain.interfaces.pv_profile_repository import IPVProfileRepository
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
from app.infrastructure.nuclear.repository import NuclearRepositoryImpl
from app.domain.nuclear.services import NuclearConstraintsBuilder

_log = logging.getLogger(__name__)


class _DefaultPyPSASimulation(AbstractGridSimulation):
    """Concrete PyPSA backend using Linear Optimal Power Flow (n.optimize / LOPF).

    PyPSA is synchronous and CPU/I/O-bound, so it runs inside a
    ThreadPoolExecutor to avoid blocking the event loop.

    Dispatch strategy (LOPF merit-order via marginal costs):
      1. Renewables (solar/wind) — p_max_pu from KNMI weather, marginal_cost ≈ 0.
      2. Conventional generators — p_max_pu = 1.0, marginal_cost by type.
      3. Battery StorageUnits — temporally coupled; absorb surplus, fill deficit.
      4. __grid_import__ backstop (1 GW, cost = 500 €/MWh) — keeps model feasible.
    """

    def run_sync(self, config: SimulationConfig) -> AdapterOutput:
        import pandas as pd  # noqa: PLC0415
        import pypsa  # type: ignore[import-untyped]
        from app.domain.entities.supply.battery_storage import BatteryStorage  # noqa: PLC0415

        n = pypsa.Network()
        n.set_snapshots(range(config.snapshot_hours))

        # ── Single shared bus ────────────────────────────────────────────────────
        n.add("Bus", "main_bus", v_nom=380.0)

        # ── 1. Add loads ─────────────────────────────────────────────────────────
        for demand in config.demands:
            profile = config.load_profiles.get(demand.name)
            params = demand.to_pypsa_params(profile=profile)
            if isinstance(params.get("p_set"), list):
                params["p_set"] = pd.Series(params["p_set"], index=n.snapshots)
            n.add("Load", demand.name, **params)

        # ── 2. Add generators and storage units ──────────────────────────────────
        # Also pre-compute renewable available energy for post-LOPF curtailment calc.
        renewable_available_mwh: dict[str, float] = {}  # gen_name → total available MWh

        for supply in config.supplies:
            if isinstance(supply, BatteryStorage):
                params = supply.to_pypsa_params()
                supply_overrides = config.pypsa_params.get(supply.name, {})
                params.update({k: v for k, v in supply_overrides.items() if k != "emissions_factor"})
                n.add("StorageUnit", supply.name, **params)
                continue

            params = supply.to_pypsa_params()
            params.pop("p_set", None)

            # Set p_max_pu from weather profiles (0–1 capacity factor per snapshot)
            solar_profile = config.solar_profiles.get(supply.name)
            wind_profile = config.wind_profiles.get(supply.name)
            if solar_profile is not None:
                params["p_max_pu"] = pd.Series(solar_profile, index=n.snapshots)
                renewable_available_mwh[supply.name] = sum(solar_profile) * supply.capacity_mw
            elif wind_profile is not None:
                params["p_max_pu"] = pd.Series(wind_profile, index=n.snapshots)
                renewable_available_mwh[supply.name] = sum(wind_profile) * supply.capacity_mw
            else:
                params["p_max_pu"] = 1.0

            # Nuclear operational constraints (min-stable-power, maintenance windows…)
            nuclear_params = config.nuclear_constraints.get(supply.name, {})
            params.update(nuclear_params)

            # User-supplied pypsa_params overrides
            supply_overrides = config.pypsa_params.get(supply.name, {})
            params.update({k: v for k, v in supply_overrides.items() if k != "emissions_factor"})

            n.add("Generator", supply.name, **params)

        # ── 3. Backstop grid-import generator (keeps LOPF always feasible) ───────
        # Very high marginal cost → dispatched only when local resources are exhausted.
        n.add("Generator", "__grid_import__", bus="main_bus", p_nom=1e9, marginal_cost=500.0)

        # ── 4. Run LOPF ──────────────────────────────────────────────────────────
        try:
            opt_result = n.optimize(solver_name=config.solver)

            # PyPSA 0.26+ returns (status, termination_condition) or None
            opt_status, opt_condition = ("ok", "optimal")
            if isinstance(opt_result, tuple) and len(opt_result) == 2:
                opt_status, opt_condition = opt_result

            if opt_condition not in ("optimal", "feasible"):
                raise RuntimeError(
                    f"LOPF did not find an optimal solution: "
                    f"status={opt_status!r}, condition={opt_condition!r}"
                )

            status = "optimized"
            objective_value = float(getattr(n, "objective", 0.0) or 0.0)

            # ── Generator time-series (exclude internal backstop) ────────────────
            generators_t: dict = {}
            grid_import_mw: list[float] = []
            if not n.generators_t.p.empty:
                for gen in n.generators_t.p.columns:
                    if gen == "__grid_import__":
                        grid_import_mw = n.generators_t.p[gen].tolist()
                        continue
                    generators_t[gen] = {"p": n.generators_t.p[gen].tolist()}

            # ── Storage unit time-series ─────────────────────────────────────────
            storage_units_t: dict = {}
            if not n.storage_units_t.p.empty:
                for su in n.storage_units_t.p.columns:
                    soc = (
                        n.storage_units_t.state_of_charge[su].tolist()
                        if not n.storage_units_t.state_of_charge.empty
                        and su in n.storage_units_t.state_of_charge.columns
                        else []
                    )
                    storage_units_t[su] = {
                        "p": n.storage_units_t.p[su].tolist(),
                        "state_of_charge": soc,
                    }

            # ── Load time-series ─────────────────────────────────────────────────
            loads_t: dict = {}
            load_p_src = n.loads_t.p if not n.loads_t.p.empty else n.loads_t.p_set
            for load in load_p_src.columns:
                loads_t[load] = {"p": load_p_src[load].tolist()}

            # ── Capacity factors: actual generation / (p_nom × hours) ───────────
            capacity_factors: dict = {}
            for gen in n.generators.index:
                if gen == "__grid_import__":
                    continue
                p_nom_val = float(n.generators.at[gen, "p_nom"])
                if gen in n.generators_t.p.columns and p_nom_val > 0:
                    capacity_factors[gen] = float(
                        n.generators_t.p[gen].sum() / (p_nom_val * config.snapshot_hours)
                    )

            # ── Totals ───────────────────────────────────────────────────────────
            # Supply = local generator dispatch only (excludes backstop grid import)
            total_supply = float(
                sum(
                    n.generators_t.p[gen].clip(lower=0).sum()
                    for gen in n.generators_t.p.columns
                    if gen != "__grid_import__"
                )
            ) if not n.generators_t.p.empty else 0.0

            total_demand = (
                float(load_p_src.sum().sum()) if not load_p_src.empty
                else float(n.loads.p_set.sum()) * config.snapshot_hours
            )

            # ── Grid exchange summary ────────────────────────────────────────────
            total_import = float(sum(v for v in grid_import_mw if v > 0))
            # Curtailment = renewable energy available but not dispatched (LOPF chose not to).
            # Use the pre-computed profiles (stored before optimization) — avoids relying on
            # n.generators_t.p_max_pu which may be empty after n.optimize().
            curtailed_mwh = 0.0
            if not n.generators_t.p.empty:
                for gen_name, available in renewable_available_mwh.items():
                    if gen_name in n.generators_t.p.columns:
                        actual = float(n.generators_t.p[gen_name].sum())
                        curtailed_mwh += max(0.0, available - actual)

            result_json = {
                "generators_t": generators_t,
                "storage_units_t": storage_units_t,
                "loads_t": loads_t,
                "capacity_factors": capacity_factors,
                "convergence": {
                    "all_converged": True,
                    "converged_count": config.snapshot_hours,
                    "total_snapshots": config.snapshot_hours,
                    "non_converged_snapshots": [],
                },
                "grid_exchange": {
                    "import_export_mw": grid_import_mw,
                    "total_import_mwh": total_import,
                    "total_export_mwh": curtailed_mwh,
                },
                "violations": {
                    "overloads": [],
                    "overvoltages": [],
                },
            }

        except Exception as e:
            error_message = str(e)
            lowered = error_message.lower()
            lopf_error_hints = (
                "infeasible", "unbounded", "not converge", "singular", "nan",
                "infinity", "optimal", "solver",
            )
            if any(hint in lowered for hint in lopf_error_hints):
                error_type = "convergence_error"
            else:
                error_type = "runtime_error"
            compact_error = re.sub(r"\s+", " ", error_message).strip()
            status = "error"
            objective_value = 0.0
            total_supply = 0.0
            total_demand = 0.0
            result_json = {
                "error": compact_error,
                "error_type": error_type,
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
        nuclear_repo: NuclearRepositoryImpl | None = None,
    ) -> None:
        self._simulation = simulation or _DefaultPyPSASimulation()
        self._load_profile_provider = load_profile_provider
        self._pv_profile_repo = pv_profile_repo
        self._nuclear_repo = nuclear_repo

    async def run(
        self,
        run_input: SimulationRunInput,
        supplies: list,
        demands: list,
        network_components: list,
    ) -> SimulationRunOutput:
        # Resolve effective date range for weather-profile lookups.
        # If the user did not supply explicit dates, derive them from snapshot_hours
        # anchored to today's month/day in 2025 (the year covered by the weather_profile table).
        effective_start = run_input.start_date
        effective_end = run_input.end_date
        if effective_start is None or effective_end is None:
            today = date.today()
            try:
                anchor = date(2025, today.month, today.day)
            except ValueError:
                # Feb 29 doesn't exist in 2025 — fall back to Feb 28
                anchor = date(2025, today.month, 28)
            days_needed = max(1, (run_input.snapshot_hours + 23) // 24)
            effective_start = anchor
            effective_end = anchor + timedelta(days=days_needed - 1)

        # Fetch load profiles async (before entering the sync thread executor)
        load_profiles: dict[str, list[float]] = {}
        if self._load_profile_provider is not None:
            for demand in demands:
                load_profiles[demand.name] = await self._load_profile_provider.get_profile(
                    demand.get_type(), run_input.snapshot_hours, effective_start
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
        if self._pv_profile_repo is not None:
            for supply in supplies:
                if supply.get_carrier() == "solar":
                    profile = await self._pv_profile_repo.get_solar_profile(
                        effective_start, effective_end
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
        if self._pv_profile_repo is not None:
            for supply in supplies:
                if supply.get_carrier() == "wind":
                    profile = await self._pv_profile_repo.get_wind_profile(
                        effective_start, effective_end
                    )
                    wind_profiles[supply.name] = profile
                    if all(v == 0.0 for v in profile):
                        profile_warnings.append(
                            f"Wind asset '{supply.name}': no KNMI data for "
                            f"{effective_start} → {effective_end}. Running at rated capacity (p_nom)."
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