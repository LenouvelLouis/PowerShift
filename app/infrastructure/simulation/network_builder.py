"""PyPSA network builder — runs AC power flow in a thread-pool executor."""

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
    """Concrete PyPSA backend using AC power flow (n.pf()).

    PyPSA is synchronous and CPU/I/O-bound, so it runs inside a
    ThreadPoolExecutor to avoid blocking the event loop.

    Dispatch strategy (merit-order):
      1. Renewables (solar/wind) are dispatched at their available profile capacity.
      2. Conventional generators fill the residual demand proportionally to their rating.
      3. A __grid_slack__ generator (large capacity, control='Slack') absorbs any
         remaining imbalance — positive output = grid import, negative = grid export.
    """

    def run_sync(self, config: SimulationConfig) -> AdapterOutput:
        import pandas as pd  # noqa: PLC0415
        import pypsa  # type: ignore[import-untyped]

        n = pypsa.Network()
        n.set_snapshots(range(config.snapshot_hours))

        # ── Single shared bus ────────────────────────────────────────────────────
        n.add("Bus", "main_bus", v_nom=380.0)

        # ── 1. Add loads first (needed to compute residual for dispatch) ─────────
        for demand in config.demands:
            profile = config.load_profiles.get(demand.name)
            params = demand.to_pypsa_params(profile=profile)
            if isinstance(params.get("p_set"), list):
                params["p_set"] = pd.Series(params["p_set"], index=n.snapshots)
            n.add("Load", demand.name, **params)

        # Aggregate load profile across all loads
        if not n.loads_t.p_set.empty:
            load_total: pd.Series = n.loads_t.p_set.sum(axis=1)
        else:
            load_total = pd.Series(float(n.loads.p_set.sum()), index=n.snapshots)

        # ── 2. Compute generator dispatch (merit-order: renewables first) ────────
        gen_dispatch: dict[str, pd.Series] = {}
        renewable_total = pd.Series(0.0, index=n.snapshots)

        for supply in config.supplies:
            p_nom = supply.capacity_mw  # asset_overrides already applied at use-case level
            solar_profile = config.solar_profiles.get(supply.name)
            wind_profile = config.wind_profiles.get(supply.name)

            if solar_profile is not None:
                ps = pd.Series([v * p_nom for v in solar_profile], index=n.snapshots)
                gen_dispatch[supply.name] = ps
                renewable_total = renewable_total.add(ps)
            elif wind_profile is not None:
                ps = pd.Series([v * p_nom for v in wind_profile], index=n.snapshots)
                gen_dispatch[supply.name] = ps
                renewable_total = renewable_total.add(ps)

        # Residual demand not covered by renewables
        residual = (load_total - renewable_total).clip(lower=0.0)

        # Conventional generators: proportional dispatch up to their rated capacity
        conv_supplies = [s for s in config.supplies if s.name not in gen_dispatch]
        total_conv_nom = sum(s.capacity_mw for s in conv_supplies) if conv_supplies else 0.0

        for supply in conv_supplies:
            p_nom = supply.capacity_mw
            if total_conv_nom > 0:
                ps = (residual * (p_nom / total_conv_nom)).clip(upper=p_nom)
            else:
                ps = pd.Series(0.0, index=n.snapshots)
            gen_dispatch[supply.name] = ps

        # ── 3. Add generators with computed p_set ────────────────────────────────
        for supply in config.supplies:
            params = supply.to_pypsa_params()
            # Set power-flow dispatch (p_set replaces p_max_pu from optimize mode)
            params["p_set"] = gen_dispatch[supply.name]
            # Remove optimize-only params if present
            params.pop("p_max_pu", None)
            # Apply user pypsa_params overrides (skip dispatch & optimize-only keys)
            supply_overrides = config.pypsa_params.get(supply.name, {})
            params.update({
                k: v for k, v in supply_overrides.items()
                if k not in ("emissions_factor", "p_max_pu", "p_set")
            })
            n.add("Generator", supply.name, **params)

        # ── 4. Network components ────────────────────────────────────────────────
        # All assets share main_bus; cables/transformers are descriptive only and
        # cannot be modelled as PyPSA Lines in a single-bus topology.
        # (No n.add call here — components are visualised in the canvas instead.)

        # ── 5. Slack generator: absorbs any grid imbalance ───────────────────────
        # Positive output → system imports from grid; negative → exports to grid.
        n.add(
            "Generator", "__grid_slack__",
            bus="main_bus",
            p_nom=1e9,
            marginal_cost=0.0,
            control="Slack",
        )

        # ── 6. Run AC power flow ─────────────────────────────────────────────────
        try:
            pf_result = n.pf()

            # Convergence
            converged_df = pf_result.get("converged", pd.DataFrame())
            if converged_df.empty:
                all_converged = True
                non_converged_snapshots: list[int] = []
            else:
                snapshot_converged = converged_df.all(axis=1)
                all_converged = bool(snapshot_converged.all())
                non_converged_snapshots = [
                    int(i) for i, ok in enumerate(snapshot_converged) if not ok
                ]

            status = "converged" if all_converged else "non_converged"

            # Generator time-series (exclude internal slack)
            generators_t: dict = {}
            grid_import_export: list[float] = []
            if not n.generators_t.p.empty:
                for gen in n.generators_t.p.columns:
                    if gen == "__grid_slack__":
                        # PyPSA may return nan for the slack's active power in single-bus
                        # surplus scenarios (NR convergence artefact). Coerce to 0.0 so
                        # grid_exchange totals and balance_mwh stay finite.
                        raw = n.generators_t.p[gen]
                        grid_import_export = [v if v == v else 0.0 for v in raw]
                        continue
                    entry: dict = {"p": n.generators_t.p[gen].tolist()}
                    if not n.generators_t.q.empty and gen in n.generators_t.q.columns:
                        entry["q"] = n.generators_t.q[gen].tolist()
                    generators_t[gen] = entry

            # Load time-series — prefer actual p (post-PF) over p_set
            loads_t: dict = {}
            load_p_src = n.loads_t.p if not n.loads_t.p.empty else n.loads_t.p_set
            for load in load_p_src.columns:
                entry = {"p": load_p_src[load].tolist()}
                if not n.loads_t.q.empty and load in n.loads_t.q.columns:
                    entry["q"] = n.loads_t.q[load].tolist()
                loads_t[load] = entry

            # Bus voltages (v_mag_pu and voltage angle per snapshot)
            buses_t: dict = {}
            for bus in n.buses.index:
                v_mag = (
                    n.buses_t.v_mag_pu[bus].tolist()
                    if not n.buses_t.v_mag_pu.empty and bus in n.buses_t.v_mag_pu.columns
                    else [1.0] * config.snapshot_hours
                )
                v_ang = (
                    n.buses_t.v_ang[bus].tolist()
                    if not n.buses_t.v_ang.empty and bus in n.buses_t.v_ang.columns
                    else [0.0] * config.snapshot_hours
                )
                buses_t[bus] = {"v_mag_pu": v_mag, "v_ang": v_ang}

            # Line flows and loading
            lines_t: dict = {}
            for line in n.lines.index:
                s_nom = float(n.lines.at[line, "s_nom"]) if "s_nom" in n.lines.columns else 0.0
                p0 = (
                    n.lines_t.p0[line].tolist()
                    if not n.lines_t.p0.empty and line in n.lines_t.p0.columns
                    else []
                )
                loading = (
                    [abs(v) / s_nom * 100 if s_nom > 0 else 0.0 for v in p0]
                    if p0 else []
                )
                lines_t[line] = {"p0": p0, "loading": loading}

            # Capacity factors: actual generation / (p_nom × hours)
            capacity_factors: dict = {}
            for gen in n.generators.index:
                if gen == "__grid_slack__":
                    continue
                p_nom_val = n.generators.at[gen, "p_nom"]
                if gen in n.generators_t.p.columns and p_nom_val > 0:
                    capacity_factors[gen] = float(
                        n.generators_t.p[gen].sum() / (p_nom_val * config.snapshot_hours)
                    )

            # Totals (exclude slack generator from supply)
            total_supply = float(
                sum(
                    n.generators_t.p[gen].sum()
                    for gen in n.generators_t.p.columns
                    if gen != "__grid_slack__" and n.generators_t.p[gen].sum() > 0
                )
            ) if not n.generators_t.p.empty else 0.0

            if not load_p_src.empty:
                total_demand = float(load_p_src.sum().sum())
            else:
                total_demand = float(n.loads.p_set.sum()) * config.snapshot_hours

            # Grid exchange summary
            total_import = float(sum(v for v in grid_import_export if v > 0))
            total_export = float(abs(sum(v for v in grid_import_export if v < 0)))

            # Violations
            overloaded_lines = [
                line for line, data in lines_t.items()
                if data["loading"] and max(data["loading"]) > 100
            ]
            overvoltage_buses = [
                bus for bus, data in buses_t.items()
                if data["v_mag_pu"] and max(data["v_mag_pu"]) > 1.05
            ]

            result_json = {
                "generators_t": generators_t,
                "loads_t": loads_t,
                "buses_t": buses_t,
                "lines_t": lines_t,
                "capacity_factors": capacity_factors,
                "convergence": {
                    "all_converged": all_converged,
                    "converged_count": config.snapshot_hours - len(non_converged_snapshots),
                    "total_snapshots": config.snapshot_hours,
                    "non_converged_snapshots": non_converged_snapshots,
                },
                "grid_exchange": {
                    "import_export_mw": grid_import_export,
                    "total_import_mwh": total_import,
                    "total_export_mwh": total_export,
                },
                "violations": {
                    "overloads": overloaded_lines,
                    "overvoltages": overvoltage_buses,
                },
            }

            objective_value = 0.0

        except Exception as e:
            error_message = str(e)
            lowered = error_message.lower()
            pf_error_hints = (
                "convergence", "not converge", "singular", "nan", "infinity",
                "jacobian", "power flow",
            )
            if any(hint in lowered for hint in pf_error_hints):
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