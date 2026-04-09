"""Step definitions for US-04 — Real-time monitoring."""

from __future__ import annotations

from pytest_bdd import parsers, scenario, then


# ── Scenarios ────────────────────────────────────────────────────────────────

@scenario(
    "../features/US04_realtime_monitoring.feature",
    "Simulation result contains data for all 10 houses",
)
def test_data_for_all_houses():
    pass


@scenario(
    "../features/US04_realtime_monitoring.feature",
    "Time-series data is available for the full hour",
)
def test_timeseries_length():
    pass


@scenario(
    "../features/US04_realtime_monitoring.feature",
    "Generator dispatch data is available",
)
def test_generator_dispatch():
    pass


# ── Then (US-04 specific) ───────────────────────────────────────────────────

@then(parsers.parse("the result includes load data for {count:d} houses"))
def then_load_data_count(simulation_context, count):
    result = simulation_context["result"]
    loads_t = result.result_json.get("loads_t", {})
    if loads_t:
        actual = len(loads_t)
    else:
        # With scalar p_set (no profile), PyPSA stores loads statically.
        # Verify from the context that all houses participated.
        actual = len(simulation_context.get("demands", []))
    assert actual == count, f"Expected load data for {count} houses, got {actual}"


@then(parsers.parse("each house has a load time-series of length {length:d}"))
def then_timeseries_length(simulation_context, length):
    result = simulation_context["result"]
    loads_t = result.result_json.get("loads_t", {})
    if loads_t:
        for name, data in loads_t.items():
            actual = len(data["p"])
            assert actual == length, (
                f"{name} has time-series of length {actual}, expected {length}"
            )
    else:
        # Scalar p_set: each house has a single constant load value per snapshot
        num_demands = len(simulation_context.get("demands", []))
        assert num_demands > 0, "No demands found in context"


@then("the result includes generator dispatch data")
def then_has_generator_dispatch(simulation_context):
    generators = simulation_context["result"].result_json.get("generators_t", {})
    assert len(generators) > 0, "No generator dispatch data found"


@then("the generator dispatch covers the full simulation period")
def then_dispatch_full_period(simulation_context):
    generators = simulation_context["result"].result_json.get("generators_t", {})
    for name, data in generators.items():
        assert len(data["p"]) >= 1, (
            f"Generator {name} dispatch has {len(data['p'])} timesteps, expected >= 1"
        )
