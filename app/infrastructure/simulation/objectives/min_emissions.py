"""Minimize emissions strategy — replaces marginal costs with emissions factors."""

from __future__ import annotations

from app.infrastructure.simulation.objectives.base import OptimizationStrategy

_RENEWABLE_CARRIERS = frozenset({"wind", "solar"})


class MinEmissionsStrategy(OptimizationStrategy):
    """Replaces marginal_cost with an emissions proxy so PyPSA minimizes CO₂.

    Priority order:
    1. Use ``emissions_factor`` from supply_overrides if provided.
    2. Set 0.0 for renewable carriers (wind, solar).
    3. Set 1.0 for all other carriers (arbitrary unit, higher = more emissions).
    """

    def apply_marginal_cost(
        self,
        params: dict,
        carrier: str,
        supply_overrides: dict,
    ) -> dict:
        result = dict(params)
        emissions_factor = supply_overrides.get("emissions_factor")
        if emissions_factor is not None:
            result["marginal_cost"] = float(emissions_factor)
        elif carrier in _RENEWABLE_CARRIERS:
            result["marginal_cost"] = 0.0
        else:
            result["marginal_cost"] = 1.0
        return result
