"""Unit tests for optimization strategy pattern.

Pure tests — no PyPSA, no database, no IO.
Each strategy receives a params dict + carrier + supply_overrides
and must return a params dict with the correct marginal_cost.
"""

from __future__ import annotations

import pytest

from app.infrastructure.simulation.objectives import get_strategy
from app.infrastructure.simulation.objectives.base import OptimizationStrategy
from app.infrastructure.simulation.objectives.min_cost import MinCostStrategy
from app.infrastructure.simulation.objectives.min_emissions import MinEmissionsStrategy
from app.infrastructure.simulation.objectives.max_renewable import MaxRenewableStrategy


# ── Helpers ───────────────────────────────────────────────────────────────────

def _params(marginal_cost: float = 1.0) -> dict:
    return {"bus": "main_bus", "carrier": "solar", "p_nom": 100.0, "marginal_cost": marginal_cost}


# ── get_strategy factory ──────────────────────────────────────────────────────

class TestGetStrategy:
    def test_returns_min_cost_strategy(self):
        assert isinstance(get_strategy("min_cost"), MinCostStrategy)

    def test_returns_min_emissions_strategy(self):
        assert isinstance(get_strategy("min_emissions"), MinEmissionsStrategy)

    def test_returns_max_renewable_strategy(self):
        assert isinstance(get_strategy("max_renewable"), MaxRenewableStrategy)

    def test_raises_on_unknown_objective(self):
        with pytest.raises(KeyError):
            get_strategy("unknown_objective")

    def test_all_strategies_implement_base(self):
        for key in ("min_cost", "min_emissions", "max_renewable"):
            assert isinstance(get_strategy(key), OptimizationStrategy)


# ── MinCostStrategy ───────────────────────────────────────────────────────────

class TestMinCostStrategy:
    def setup_method(self):
        self.strategy = MinCostStrategy()

    def test_does_not_modify_marginal_cost_for_solar(self):
        params = _params(marginal_cost=0.001)
        result = self.strategy.apply_marginal_cost(params, "solar", {})
        assert result["marginal_cost"] == 0.001

    def test_does_not_modify_marginal_cost_for_wind(self):
        params = _params(marginal_cost=0.0)
        result = self.strategy.apply_marginal_cost(params, "wind", {})
        assert result["marginal_cost"] == 0.0

    def test_does_not_modify_marginal_cost_for_nuclear(self):
        params = _params(marginal_cost=5.0)
        result = self.strategy.apply_marginal_cost(params, "nuclear", {})
        assert result["marginal_cost"] == 5.0

    def test_returns_params_dict(self):
        params = _params()
        result = self.strategy.apply_marginal_cost(params, "solar", {})
        assert isinstance(result, dict)

    def test_does_not_mutate_original_params(self):
        params = _params(marginal_cost=99.0)
        self.strategy.apply_marginal_cost(params, "solar", {})
        assert params["marginal_cost"] == 99.0


# ── MinEmissionsStrategy ──────────────────────────────────────────────────────

class TestMinEmissionsStrategy:
    def setup_method(self):
        self.strategy = MinEmissionsStrategy()

    def test_solar_gets_zero_marginal_cost(self):
        result = self.strategy.apply_marginal_cost(_params(), "solar", {})
        assert result["marginal_cost"] == 0.0

    def test_wind_gets_zero_marginal_cost(self):
        result = self.strategy.apply_marginal_cost(_params(), "wind", {})
        assert result["marginal_cost"] == 0.0

    def test_nuclear_gets_one_marginal_cost(self):
        result = self.strategy.apply_marginal_cost(_params(), "nuclear", {})
        assert result["marginal_cost"] == 1.0

    def test_gas_gets_one_marginal_cost(self):
        result = self.strategy.apply_marginal_cost(_params(), "gas", {})
        assert result["marginal_cost"] == 1.0

    def test_custom_emissions_factor_overrides_default(self):
        overrides = {"emissions_factor": 0.42}
        result = self.strategy.apply_marginal_cost(_params(), "gas", overrides)
        assert result["marginal_cost"] == pytest.approx(0.42)

    def test_custom_emissions_factor_on_renewable_overrides_zero(self):
        overrides = {"emissions_factor": 0.05}
        result = self.strategy.apply_marginal_cost(_params(), "solar", overrides)
        assert result["marginal_cost"] == pytest.approx(0.05)

    def test_does_not_mutate_original_params(self):
        params = _params(marginal_cost=99.0)
        self.strategy.apply_marginal_cost(params, "solar", {})
        assert params["marginal_cost"] == 99.0


# ── MaxRenewableStrategy ──────────────────────────────────────────────────────

class TestMaxRenewableStrategy:
    def setup_method(self):
        self.strategy = MaxRenewableStrategy()

    def test_solar_gets_zero_marginal_cost(self):
        result = self.strategy.apply_marginal_cost(_params(), "solar", {})
        assert result["marginal_cost"] == 0.0

    def test_wind_gets_zero_marginal_cost(self):
        result = self.strategy.apply_marginal_cost(_params(), "wind", {})
        assert result["marginal_cost"] == 0.0

    def test_nuclear_gets_high_marginal_cost(self):
        result = self.strategy.apply_marginal_cost(_params(), "nuclear", {})
        assert result["marginal_cost"] == 1000.0

    def test_gas_gets_high_marginal_cost(self):
        result = self.strategy.apply_marginal_cost(_params(), "gas", {})
        assert result["marginal_cost"] == 1000.0

    def test_supply_overrides_ignored_for_carrier_logic(self):
        # MaxRenewable does not use emissions_factor — overrides don't affect it
        overrides = {"emissions_factor": 0.99}
        result = self.strategy.apply_marginal_cost(_params(), "gas", overrides)
        assert result["marginal_cost"] == 1000.0

    def test_does_not_mutate_original_params(self):
        params = _params(marginal_cost=99.0)
        self.strategy.apply_marginal_cost(params, "wind", {})
        assert params["marginal_cost"] == 99.0
