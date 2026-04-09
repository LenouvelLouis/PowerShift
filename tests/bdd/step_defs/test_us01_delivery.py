"""Step definitions for US-01 — Constant energy delivery."""

from __future__ import annotations

from pytest_bdd import parsers, scenario, then


# ── Scenarios ────────────────────────────────────────────────────────────────

@scenario(
    "../features/US01_constant_energy_delivery.feature",
    "Each house receives 10 MWh within tolerance",
)
def test_each_house_receives_10mwh():
    pass


@scenario(
    "../features/US01_constant_energy_delivery.feature",
    "Delivery is continuous for the full hour",
)
def test_delivery_is_continuous():
    pass


@scenario(
    "../features/US01_constant_energy_delivery.feature",
    "Simulation completes without interruption",
)
def test_simulation_completes():
    pass


# ── Then (US-01 specific) ───────────────────────────────────────────────────

@then("no house has a zero-power gap in its load series")
def then_no_zero_gaps(simulation_context):
    result = simulation_context["result"]
    loads = result.result_json.get("loads_t", {})
    for house_name, data in loads.items():
        for t, p in enumerate(data["p"]):
            assert p > 0, f"{house_name} has zero power at timestep {t}"


@then(parsers.parse("the total demand is {expected:g} MWh"))
def then_total_demand(simulation_context, expected):
    actual = simulation_context["result"].total_demand_mwh
    assert abs(actual - expected) < 1.0, f"Total demand {actual} != {expected}"
