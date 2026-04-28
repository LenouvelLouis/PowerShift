"""Domain-specific exceptions for the simulation module."""

from __future__ import annotations


class SimulationError(Exception):
    """Base exception for all simulation domain errors."""


class WeatherDataEmptyError(SimulationError):
    """Raised when weather-dependent generators have all-zero capacity factor profiles.

    This typically means KNMI/weather data does not cover the requested simulation
    period, so wind/solar generators would produce nothing — leading to misleading
    results.
    """

    def __init__(self, generator_names: list[str]) -> None:
        self.generator_names = generator_names
        names_str = ", ".join(generator_names)
        super().__init__(
            f"Weather data unavailable for the requested period. "
            f"Wind/solar capacity factors are all zero for: {names_str}. "
            f"Select a date range within the KNMI data coverage (Jan\u2013Dec 2025) "
            f"or remove weather-dependent generators."
        )
