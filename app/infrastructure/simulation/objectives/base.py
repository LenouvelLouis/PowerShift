"""Base interface for optimization strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod


class OptimizationStrategy(ABC):
    """Adjusts PyPSA marginal costs to steer the optimizer toward a given objective."""

    @abstractmethod
    def apply_marginal_cost(
        self,
        params: dict,
        carrier: str,
        supply_overrides: dict,
    ) -> dict:
        """Return a copy of *params* with marginal_cost set according to this strategy.

        Args:
            params: PyPSA generator params dict (as returned by supply.to_pypsa_params()).
            carrier: Energy carrier string (e.g. "wind", "solar", "nuclear").
            supply_overrides: User-provided pypsa_params overrides for this asset.

        Returns:
            New dict with marginal_cost adjusted. Original dict is never mutated.
        """
