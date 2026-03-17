"""Domain-specific exceptions for the wind turbine module."""

from __future__ import annotations

import uuid


class WindTurbineError(Exception):
    """Base exception for all wind turbine domain errors."""


class TurbineModelNotFoundError(WindTurbineError):
    """Raised when a turbine model cannot be found by ID."""

    def __init__(self, model_id: uuid.UUID) -> None:
        super().__init__(f"Turbine model '{model_id}' not found.")
        self.model_id = model_id


class WindAssetNotFoundError(WindTurbineError):
    """Raised when a wind turbine asset cannot be found by ID."""

    def __init__(self, asset_id: uuid.UUID) -> None:
        super().__init__(f"Wind turbine asset '{asset_id}' not found.")
        self.asset_id = asset_id


class InvalidPowerCurveError(WindTurbineError):
    """Raised when a power curve fails validation rules."""


class InvalidTurbineModelError(WindTurbineError):
    """Raised when turbine model parameters are logically inconsistent."""
