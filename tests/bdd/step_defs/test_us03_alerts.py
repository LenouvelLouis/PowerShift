"""Step definitions for US-03 — Alert on supply failure."""

from __future__ import annotations

from pytest_bdd import parsers, scenario, then


# ── Scenarios ────────────────────────────────────────────────────────────────

@scenario(
    "../features/US03_alert_on_supply_failure.feature",
    "Simulation detects insufficient supply",
)
def test_insufficient_supply():
    pass


@scenario(
    "../features/US03_alert_on_supply_failure.feature",
    "Other houses are not impacted when supply is sufficient",
)
def test_other_houses_unaffected():
    pass


@scenario(
    "../features/US03_alert_on_supply_failure.feature",
    "Failure information is included in the result",
)
def test_failure_info():
    pass


# ── Then (US-03 specific) ───────────────────────────────────────────────────

@then(parsers.parse('the simulation status is not "{status}"'))
def then_status_is_not(simulation_context, status):
    actual = simulation_context["result"].status
    assert actual != status, f"Expected status != '{status}', got '{actual}'"


@then("the simulation result contains error details")
def then_result_has_error(simulation_context):
    result_json = simulation_context["result"].result_json
    has_error = "error" in result_json
    has_violations = "violations" in result_json
    assert has_error or has_violations, (
        f"Expected error details in result, got keys: {list(result_json.keys())}"
    )
