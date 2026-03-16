"""Tests for solar p_max_pu constraint enforcement in PyPSA network builder."""
from __future__ import annotations

import pytest
import pandas as pd
import pypsa


def _build_solar_network(snapshot_hours: int, solar_profile: list[float]) -> pypsa.Network:
    """Build a minimal PyPSA network with one solar generator and one load."""
    n = pypsa.Network()
    n.set_snapshots(range(snapshot_hours))
    n.add("Bus", "bus", v_nom=380.0)
    n.add(
        "Generator",
        "solar",
        bus="bus",
        p_nom=100.0,
        marginal_cost=0.001,
        p_max_pu=pd.Series(solar_profile).reindex(n.snapshots),
    )
    n.add(
        "Load",
        "load",
        bus="bus",
        p_set=pd.Series([10.0] * snapshot_hours, index=n.snapshots),
    )
    # Also add a slack generator so the network is always feasible
    n.add("Generator", "slack", bus="bus", p_nom=1000.0, marginal_cost=10.0)
    return n


class TestPMaxPuNaNBypass:
    """Hypothesis 1: short solar_profile causes NaN in p_max_pu → unconstrained dispatch."""

    def test_nan_in_p_max_pu_constrains_dispatch_to_zero(self):
        """Short profile (3 values for 5 snapshots) → NaN at h3, h4.

        PyPSA treats NaN as 0.0, so solar is constrained to 0 at those hours
        and the slack generator covers the load instead.
        """
        snapshot_hours = 5
        solar_profile = [0.0, 0.0, 0.8]  # Only 3 values for a 5-snapshot network
        n = _build_solar_network(snapshot_hours, solar_profile)

        n.optimize(solver_name="highs")

        solar_dispatch = n.generators_t.p["solar"].tolist()
        # NaN → 0.0: solar cannot dispatch at h3/h4
        assert solar_dispatch[3] == pytest.approx(0.0, abs=1e-4), (
            f"Expected solar=0 at h3 due to NaN in p_max_pu, got {solar_dispatch[3]}"
        )
        assert solar_dispatch[4] == pytest.approx(0.0, abs=1e-4), (
            f"Expected solar=0 at h4 due to NaN in p_max_pu, got {solar_dispatch[4]}"
        )

    def test_correct_length_profile_constrains_nighttime_to_zero(self):
        """When profile length matches snapshot_hours, nighttime hours must be 0."""
        snapshot_hours = 5
        # Correct length: 5 values matching 5 snapshots
        solar_profile = [0.0, 0.0, 0.8, 0.0, 0.0]  # h0-h1 night, h2 sun, h3-h4 night
        n = _build_solar_network(snapshot_hours, solar_profile)

        result = n.optimize(solver_name="highs")

        solar_dispatch = n.generators_t.p["solar"].tolist()
        assert solar_dispatch[0] == pytest.approx(0.0, abs=1e-4), f"h0 should be 0, got {solar_dispatch[0]}"
        assert solar_dispatch[1] == pytest.approx(0.0, abs=1e-4), f"h1 should be 0, got {solar_dispatch[1]}"
        assert solar_dispatch[3] == pytest.approx(0.0, abs=1e-4), f"h3 should be 0, got {solar_dispatch[3]}"
        assert solar_dispatch[4] == pytest.approx(0.0, abs=1e-4), f"h4 should be 0, got {solar_dispatch[4]}"
