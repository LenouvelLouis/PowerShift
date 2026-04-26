"""Wind turbine domain entities — ORM-free pure Python dataclasses."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PowerCurvePoint:
    """Value object representing a single point on a turbine's power curve."""

    wind_speed_ms: float
    power_kw: float


@dataclass
class WindDataPoint:
    """Value object representing a single wind observation from a weather station."""

    timestamp: datetime
    wind_speed_ms: float
    wind_direction_deg: float | None = None
    temperature_c: float | None = None


@dataclass
class WindTurbineModel:
    """Turbine model specification (manufacturer/catalog data).

    Represents reference data shared across many deployments.
    """

    id: uuid.UUID
    manufacturer: str
    model_name: str
    rated_power_kw: float
    rotor_diameter_m: float
    hub_height_m: float
    cut_in_speed_ms: float
    cut_out_speed_ms: float
    rated_speed_ms: float
    power_curve: list[PowerCurvePoint] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class WindMeasurement:
    """Value object representing a persisted weather station observation."""

    station_code: str
    station_name: str
    timestamp: datetime
    wind_speed_ms: float | None
    wind_direction_deg: float | None
    temperature_c: float | None
    air_pressure_hpa: float | None


@dataclass
class WindTurbineAsset:
    """A specific turbine deployment in a simulation context.

    References a WindTurbineModel and adds site/deployment specifics.
    """

    id: uuid.UUID
    name: str
    turbine_model: WindTurbineModel
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    quantity: int = 1
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
