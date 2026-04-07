"""Maximize renewable share strategy — penalizes non-renewable dispatch."""

from __future__ import annotations

from app.infrastructure.simulation.objectives.base import OptimizationStrategy

_RENEWABLE_CARRIERS = frozenset({"wind", "solar"})
_PENALTY_COST = 1000.0


class MaxRenewableStrategy(OptimizationStrategy):
    """Forces the solver to prefer renewables by making non-renewables very expensive.

    - Renewable carriers (wind, solar): marginal_cost = 0.0
    - Everything else: marginal_cost = 1000.0 (high enough to be avoided)
    """

    def apply_marginal_cost(
        self,
        params: dict,
        carrier: str,
        supply_overrides: dict,
    ) -> dict:
        result = dict(params)
        result["marginal_cost"] = 0.0 if carrier in _RENEWABLE_CARRIERS else _PENALTY_COST
        return result
