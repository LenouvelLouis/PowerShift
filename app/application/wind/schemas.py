"""Pydantic request/response schemas for the wind turbine API.

These DTOs decouple the API layer from both the domain entities and the
SQLModel ORM models.  They contain no business logic.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

# ── Power-curve ───────────────────────────────────────────────────────────────

class PowerCurvePointSchema(BaseModel):
    wind_speed_ms: float = Field(..., ge=0, description="Wind speed in m/s")
    power_kw: float = Field(..., ge=0, description="Power output in kW")


# ── Turbine Model ─────────────────────────────────────────────────────────────

class TurbineModelCreate(BaseModel):
    manufacturer: str = Field(..., min_length=1, examples=["Vestas"])
    model_name: str = Field(..., min_length=1, examples=["V110-2.0"])
    rated_power_kw: float = Field(..., gt=0, description="Rated power in kW")
    rotor_diameter_m: float = Field(..., gt=0, description="Rotor diameter in metres")
    hub_height_m: float = Field(..., gt=0, description="Hub height in metres")
    cut_in_speed_ms: float = Field(..., ge=0, description="Cut-in wind speed in m/s")
    cut_out_speed_ms: float = Field(..., gt=0, description="Cut-out wind speed in m/s")
    rated_speed_ms: float = Field(..., gt=0, description="Rated wind speed in m/s")
    power_curve: list[PowerCurvePointSchema] = Field(
        default_factory=list,
        description="Optional power curve points (sorted by wind_speed_ms)",
    )

    @field_validator("rated_speed_ms")
    @classmethod
    def rated_between_cutin_cutout(cls, v: float, info: object) -> float:  # noqa: ANN001
        data = info.data  # type: ignore[attr-defined]
        cut_in = data.get("cut_in_speed_ms", 0.0)
        cut_out = data.get("cut_out_speed_ms", float("inf"))
        if not (cut_in < v <= cut_out):
            raise ValueError(
                f"rated_speed_ms ({v}) must be between cut_in ({cut_in}) and cut_out ({cut_out})"
            )
        return v


class TurbineModelResponse(BaseModel):
    id: uuid.UUID
    manufacturer: str
    model_name: str
    rated_power_kw: float
    rotor_diameter_m: float
    hub_height_m: float
    cut_in_speed_ms: float
    cut_out_speed_ms: float
    rated_speed_ms: float
    power_curve: list[PowerCurvePointSchema]
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Wind Asset ────────────────────────────────────────────────────────────────

class WindAssetCreate(BaseModel):
    name: str = Field(..., min_length=1, examples=["Turbine North #1"])
    turbine_model_id: uuid.UUID
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    altitude_m: float | None = Field(default=None, ge=0)
    quantity: int = Field(default=1, ge=1, description="Number of identical turbines at this site")
    is_active: bool = True


class WindAssetResponse(BaseModel):
    id: uuid.UUID
    name: str
    turbine_model: TurbineModelResponse
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    quantity: int
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Power calculation ─────────────────────────────────────────────────────────

class WindDataPointSchema(BaseModel):
    timestamp: datetime
    wind_speed_ms: float = Field(..., ge=0, description="Wind speed at 10 m height in m/s")
    wind_direction_deg: float | None = Field(default=None, ge=0, lt=360)
    temperature_c: float | None = None


class CalculatePowerRequest(BaseModel):
    asset_id: uuid.UUID
    # Option A: provide wind data inline
    wind_data: Optional[list[WindDataPointSchema]] = None
    # Option B: pull from the weather_profile table
    station_code: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    availability: float = Field(default=0.97, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def check_input_mode(self) -> CalculatePowerRequest:
        has_inline = bool(self.wind_data)
        has_db = self.station_code is not None and self.start is not None and self.end is not None
        if not has_inline and not has_db:
            raise ValueError(
                "Provide either 'wind_data' (inline) or 'station_code' + 'start' + 'end' (DB query)."
            )
        return self


class PowerSeriesPoint(BaseModel):
    timestamp: datetime
    power_kw: float


# ── Wind Measurements ─────────────────────────────────────────────────────────

class WindMeasurementResponse(BaseModel):
    station_code: str
    station_name: str
    timestamp: datetime
    wind_speed_ms: float | None = None
    wind_direction_deg: float | None = None
    temperature_c: float | None = None
    air_pressure_hpa: float | None = None

    model_config = {"from_attributes": True}


class WindMeasurementStatsResponse(BaseModel):
    station_code: str
    count: int
    start: datetime | None = None
    end: datetime | None = None
    avg_wind_speed_ms: float | None = None
    min_wind_speed_ms: float | None = None
    max_wind_speed_ms: float | None = None
    avg_temperature_c: float | None = None
    missing_wind_pct: float


class CalculatePowerResponse(BaseModel):
    asset_id: uuid.UUID
    asset_name: str
    power_series: list[PowerSeriesPoint]
    capacity_factor: float
    total_energy_kwh: float
    peak_power_kw: float
