"""Shared step definitions for all BDD scenarios.

pytest-bdd discovers steps defined in conftest.py files automatically,
so all Given/When steps shared across user stories live here.
"""

from __future__ import annotations

from pytest_bdd import given, parsers, then, when

from tests.bdd.conftest import run_simulation


# ── Given (shared across US-01..04) ─────────────────────────────────────────

@given("a generator with 100 MW capacity", target_fixture="supplies")
def given_generator(simulation_context, make_generator):
    gen = make_generator(capacity_mw=100.0)
    simulation_context["supplies"] = [gen]
    return [gen]


@given("10 houses each demanding 10 MW", target_fixture="demands")
def given_10_houses(simulation_context, make_house):
    houses = [make_house(load_mw=10.0, idx=i) for i in range(10)]
    simulation_context["demands"] = houses
    return houses


@given("a transformer connecting the grid", target_fixture="network_components")
def given_transformer(simulation_context, make_transformer):
    t = make_transformer()
    simulation_context["network_components"] = [t]
    return [t]


@given(parsers.parse("the generator capacity is reduced to {capacity:d} MW"))
def given_reduced_capacity(simulation_context, capacity, make_generator):
    gen = make_generator(capacity_mw=float(capacity))
    simulation_context["supplies"] = [gen]


# ── Given (US-05 specific) ──────────────────────────────────────────────────

@given(parsers.parse("a nuclear power plant producing {capacity:g} kWh"), target_fixture="supplies")
def given_nuclear_plant_kwh(simulation_context, capacity, make_generator):
    # Convert kWh to MW (for 1-hour simulation, 1000 kWh = 1 MWh = 1 MW)
    gen = make_generator(capacity_mw=capacity / 1000.0)
    simulation_context["supplies"] = [gen]
    return [gen]


@given(parsers.parse("{num_houses:d} houses each consuming {load:g} kWh"), target_fixture="demands")
def given_n_houses_kwh(simulation_context, num_houses, load, make_house):
    # Convert kWh to MW (for 1-hour simulation, 1000 kWh = 1 MWh = 1 MW)
    houses = [make_house(load_mw=load / 1000.0, idx=i) for i in range(num_houses)]
    simulation_context["demands"] = houses
    return houses


@given("the simulation runs for 1 hour")
def given_simulation_duration_1hour(simulation_context):
    simulation_context["snapshot_hours"] = 1


# ── When (shared across US-01..05) ──────────────────────────────────────────

@when("I run a 1-hour simulation")
def when_run_simulation(simulation_context, pypsa_simulation):
    result = run_simulation(
        pypsa_simulation,
        simulation_context["supplies"],
        simulation_context["demands"],
        simulation_context["network_components"],
        snapshot_hours=1,
    )
    simulation_context["result"] = result


@when("I run the simulation")
def when_run_simulation_us05(simulation_context, pypsa_simulation, make_transformer):
    # Ensure we have network components (US-05 doesn't explicitly request transformer)
    if "network_components" not in simulation_context:
        simulation_context["network_components"] = [make_transformer()]
    
    snapshot_hours = simulation_context.get("snapshot_hours", 1)
    result = run_simulation(
        pypsa_simulation,
        simulation_context["supplies"],
        simulation_context["demands"],
        simulation_context["network_components"],
        snapshot_hours=snapshot_hours,
    )
    simulation_context["result"] = result


# ── Then (shared across multiple user stories) ──────────────────────────────

@then(parsers.parse('the simulation status is "{expected_status}"'))
def then_status_is(simulation_context, expected_status):
    assert simulation_context["result"].status == expected_status


@then(parsers.parse("each house should receive between {lo:g} and {hi:g} MWh"))
def then_each_house_in_range(simulation_context, lo, hi):
    result = simulation_context["result"]
    loads = result.result_json.get("loads_t", {})
    for house_name, data in loads.items():
        total = sum(data["p"])
        assert lo <= total <= hi, (
            f"{house_name} received {total:.2f} MWh, expected [{lo}, {hi}]"
        )
