"""Optimization strategy package.

Usage::

    from app.infrastructure.simulation.objectives import get_strategy

    strategy = get_strategy(config.optimization_objective)
    params = strategy.apply_marginal_cost(params, carrier, supply_overrides)
"""

from __future__ import annotations

from app.infrastructure.simulation.objectives.base import OptimizationStrategy
from app.infrastructure.simulation.objectives.max_renewable import MaxRenewableStrategy
from app.infrastructure.simulation.objectives.min_cost import MinCostStrategy
from app.infrastructure.simulation.objectives.min_emissions import MinEmissionsStrategy

_STRATEGIES: dict[str, OptimizationStrategy] = {
    "min_cost": MinCostStrategy(),
    "min_emissions": MinEmissionsStrategy(),
    "max_renewable": MaxRenewableStrategy(),
}


def get_strategy(objective: str) -> OptimizationStrategy:
    """Return the strategy instance for *objective*.

    Raises:
        KeyError: If *objective* is not a known optimization objective.
    """
    return _STRATEGIES[objective]


__all__ = [
    "OptimizationStrategy",
    "MinCostStrategy",
    "MinEmissionsStrategy",
    "MaxRenewableStrategy",
    "get_strategy",
]
