"""Step definitions for US-06 — Time variation over 24 hours with variable demand."""

from __future__ import annotations

import pandas as pd
import pypsa
import pytest
from pytest_bdd import given, parsers, scenario, then, when

SNAPSHOT_HOURS = 24
NUCLEAR_CAPACITY_MW = 100.0
NUM_HOUSES = 10

# Realistic 24h variable load profile per house (normalized)
# Source: CBS Netherlands 2023 — residential consumption patterns
HOUSE_LOAD_PROFILE = [
    0.5, 0.4, 0.4, 0.4, 0.5, 0.7,   # 00h-05h night
    1.2, 1.5, 1.3, 1.0, 0.9, 0.8,   # 06h-11h morning peak
    0.9, 0.8, 0.8, 0.9, 1.1, 1.4,   # 12h-17h afternoon
    1.6, 1.5, 1.3, 1.1, 0.9, 0.6,   # 18h-23h evening peak
]


# ── Scenarios ────────────────────────────────────────────────────────────────

@scenario(
    "../features/US06_24h_variable_demand.feature",
    "Simulation completes over 24 time steps",
)
def test_simulation_completes_24h():
    pass


@scenario(
    "../features/US06_24h_variable_demand.feature",
    "Power balance is maintained at every hour",
)
def test_power_balance_24h():
    pass


@scenario(
    "../features/US06_24h_variable_demand.feature",
    "Demand varies across the 24 hours",
)
def test_demand_varies():
    pass


@scenario(
    "../features/US06_24h_variable_demand.feature",
    "Nuclear plant never exceeds its capacity",
)
def test_nuclear_capacity():
    pass


@scenario(
    "../features/US06_24h_variable_demand.feature",
    "Evening peak is higher than night valley",
)
def test_evening_peak():
    pass


@scenario(
    "../features/US06_24h_variable_demand.feature",
    "All 10 houses are present in the simulation",
)
def test_10_houses_present():
    pass


# ── Given ────────────────────────────────────────────────────────────────────

@given("a nuclear generator with 100 MW capacity")
def given_nuclear_generator(simulation_context):
    simulation_context["network"] = pypsa.Network()
    simulation_context["network"].set_snapshots(range(SNAPSHOT_HOURS))
    simulation_context["network"].add("Bus", "main_bus", v_nom=20.0)
    simulation_context["network"].add(
        "Generator", "nuclear_plant",
        bus="main_bus",
        p_nom=NUCLEAR_CAPACITY_MW,
        marginal_cost=1.0,
    )
    simulation_context["network"].add(
        "Generator", "slack",
        bus="main_bus",
        p_nom=1000.0,
        marginal_cost=100.0,
    )


@given("10 houses with variable 24h demand profiles")
def given_10_houses(simulation_context):
    n = simulation_context["network"]
    for i in range(NUM_HOUSES):
        profile = pd.Series(HOUSE_LOAD_PROFILE, index=n.snapshots)
        n.add("Load", f"house_{i}", bus="main_bus", p_set=profile)


@given("no network component")
def given_no_network(simulation_context):
    pass


# ── When ──────────────────────────────────────────────────────────────────────

@when("I run a 24-hour simulation")
def when_run_24h(simulation_context):
    n = simulation_context["network"]
    n.optimize(solver_name="highs")
    simulation_context["result_network"] = n


# ── Then (US-06 specific) ────────────────────────────────────────────────────

@then('the simulation status is "optimal"')
def then_status_optimal(simulation_context):
    n = simulation_context["result_network"]
    assert n.objective is not None, "Simulation did not converge"


@then("the simulation covers exactly 24 time steps")
def then_24_snapshots(simulation_context):
    n = simulation_context["result_network"]
    assert len(n.snapshots) == SNAPSHOT_HOURS, (
        f"Expected {SNAPSHOT_HOURS} snapshots, got {len(n.snapshots)}"
    )


@then("the energy balance is close to 0.0 MWh over 24 hours")
def then_balance_zero(simulation_context):
    n = simulation_context["result_network"]
    for t in n.snapshots:
        total_supply = n.generators_t.p.loc[t].sum()
        total_demand = sum(
            n.loads_t.p_set.loc[t, load]
            for load in n.loads.index
            if load in n.loads_t.p_set.columns
        )
        assert abs(total_supply - total_demand) < 1e-3, (
            f"Balance violated at hour {t}: supply={total_supply:.4f}, demand={total_demand:.4f}"
        )


@then("the total demand is not constant across all hours")
def then_demand_varies(simulation_context):
    n = simulation_context["result_network"]
    total_per_hour = pd.Series(0.0, index=n.snapshots)
    for load in n.loads.index:
        if load in n.loads_t.p_set.columns:
            total_per_hour += n.loads_t.p_set[load]
    assert total_per_hour.max() > total_per_hour.min(), (
        "Demand is flat across all hours — variable profile not applied"
    )


@then("the nuclear plant output never exceeds 100 MW")
def then_nuclear_within_capacity(simulation_context):
    n = simulation_context["result_network"]
    max_output = n.generators_t.p["nuclear_plant"].max()
    assert max_output <= NUCLEAR_CAPACITY_MW + 1e-3, (
        f"Nuclear exceeded capacity: {max_output:.2f} MW > {NUCLEAR_CAPACITY_MW} MW"
    )


@then("the demand at hours 18 to 20 is higher than at hours 1 to 3")
def then_evening_peak_higher(simulation_context):
    n = simulation_context["result_network"]
    total_per_hour = pd.Series(0.0, index=n.snapshots)
    for load in n.loads.index:
        if load in n.loads_t.p_set.columns:
            total_per_hour += n.loads_t.p_set[load]
    evening = total_per_hour.iloc[18:21].mean()
    night = total_per_hour.iloc[1:4].mean()
    assert evening > night, (
        f"Evening peak ({evening:.2f} MW) not higher than night ({night:.2f} MW)"
    )


@then("the network contains exactly 10 house loads")
def then_10_houses(simulation_context):
    n = simulation_context["result_network"]
    houses = [name for name in n.loads.index if name.startswith("house_")]
    assert len(houses) == NUM_HOUSES, (
        f"Expected {NUM_HOUSES} houses, found {len(houses)}"
    )
