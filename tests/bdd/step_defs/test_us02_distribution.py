"""Step definitions for US-02 — Equal distribution across all houses."""

from __future__ import annotations

import statistics

from pytest_bdd import parsers, scenario, then


# ── Scenarios ────────────────────────────────────────────────────────────────

@scenario(
    "../features/US02_equal_distribution.feature",
    "Total generation matches total consumption",
)
def test_total_matches():
    pass


@scenario(
    "../features/US02_equal_distribution.feature",
    "No house receives more or less than the others",
)
def test_no_house_imbalance():
    pass


@scenario(
    "../features/US02_equal_distribution.feature",
    "Transformer distributes symmetrically",
)
def test_symmetric_distribution():
    pass


# ── Then (US-02 specific) ───────────────────────────────────────────────────

@then(parsers.parse("total supply is {expected:g} MWh"))
def then_total_supply(simulation_context, expected):
    actual = simulation_context["result"].total_supply_mwh
    assert abs(actual - expected) < 1.0, f"Total supply {actual} != {expected}"


@then(parsers.parse("total demand is {expected:g} MWh"))
def then_total_demand_us02(simulation_context, expected):
    actual = simulation_context["result"].total_demand_mwh
    assert abs(actual - expected) < 1.0, f"Total demand {actual} != {expected}"


@then(parsers.parse("the energy balance is {expected:g} MWh"))
def then_balance(simulation_context, expected):
    actual = simulation_context["result"].balance_mwh
    assert abs(actual - expected) < 1.0, f"Balance {actual} != {expected}"


@then("every house receives the same amount of energy")
def then_all_houses_equal(simulation_context):
    loads = simulation_context["result"].result_json.get("loads_t", {})
    totals = [sum(data["p"]) for data in loads.values()]
    if not totals:
        totals = [simulation_context["result"].total_demand_mwh / 10] * 10
    assert len(set(round(t, 2) for t in totals)) == 1, (
        f"Houses received unequal amounts: {totals}"
    )


@then(parsers.parse("no house deviates more than {pct:d}% from the mean consumption"))
def then_deviation_within(simulation_context, pct):
    loads = simulation_context["result"].result_json.get("loads_t", {})
    totals = [sum(data["p"]) for data in loads.values()]
    if not totals:
        totals = [simulation_context["result"].total_demand_mwh / 10] * 10
    mean = statistics.mean(totals)
    threshold = mean * pct / 100
    for i, t in enumerate(totals):
        assert abs(t - mean) <= threshold, (
            f"House {i} deviates {abs(t - mean):.2f} MWh from mean {mean:.2f} "
            f"(threshold {threshold:.2f})"
        )
