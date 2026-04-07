"""Minimize cost strategy — uses each generator's natural marginal cost."""

from __future__ import annotations

from app.infrastructure.simulation.objectives.base import OptimizationStrategy


class MinCostStrategy(OptimizationStrategy):
    """Default strategy: do not override marginal costs.

    PyPSA minimizes the sum of (marginal_cost × dispatch) naturally,
    so leaving costs unchanged minimizes real monetary cost.
    """

    def apply_marginal_cost(
        self,
        params: dict,
        carrier: str,
        supply_overrides: dict,
    ) -> dict:
        return dict(params)
