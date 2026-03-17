"""PyPSA adapter extension — adds wind generator integration to a PyPSA network."""

from __future__ import annotations

import logging

import pandas as pd

from app.domain.wind.entities import WindTurbineAsset

_log = logging.getLogger(__name__)

# PyPSA convention: power in MW, not kW
_KW_TO_MW = 1 / 1000.0


def add_wind_generator(
    network: object,
    asset: WindTurbineAsset,
    power_series: pd.Series,
) -> None:
    """Add a wind turbine asset as a PyPSA Generator to an existing network.

    The generator is attached to ``main_bus`` following the POC single-bus
    convention used throughout this project.

    Args:
        network: A ``pypsa.Network`` instance (typed as object to avoid a
            hard import at module load time — PyPSA is imported lazily).
        asset: The WindTurbineAsset domain entity.
        power_series: Pandas Series of power output in **kW**, indexed by
            the network's snapshots.  Must align with ``network.snapshots``.

    Notes:
        - ``p_nom`` is set to the fleet rated power in **MW**.
        - ``p_max_pu`` is the normalised dispatch profile clipped to [0, 1].
        - Marginal cost is 0 (wind has zero fuel cost).
        - Carrier is ``"wind"``.
    """
    turbine = asset.turbine_model
    fleet_rated_kw = turbine.rated_power_kw * asset.quantity
    fleet_rated_mw = fleet_rated_kw * _KW_TO_MW

    # Normalise the kW series to a per-unit fraction of rated power
    if fleet_rated_kw > 0:
        p_max_pu: pd.Series = (power_series / fleet_rated_kw).clip(0.0, 1.0)
    else:
        p_max_pu = power_series.clip(0.0, 1.0)

    _log.debug(
        "Adding wind generator '%s' to PyPSA network: p_nom=%.3f MW, "
        "mean p_max_pu=%.3f",
        asset.name,
        fleet_rated_mw,
        float(p_max_pu.mean()),
    )

    network.add(  # type: ignore[attr-defined]
        "Generator",
        asset.name,
        bus="main_bus",
        carrier="wind",
        p_nom=fleet_rated_mw,
        p_max_pu=p_max_pu,
        marginal_cost=0.0,
    )
