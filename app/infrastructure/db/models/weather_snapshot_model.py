"""SQLModel ORM for weather_snapshot — unified meteorological data table."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, Index, UniqueConstraint
from sqlmodel import Field, SQLModel


class WeatherSnapshotORM(SQLModel, table=True):
    """Unified meteorological snapshot from any source.

    Replaces the split between ``pv_hourly`` (static 2023 solar reference) and
    ``wind_measurement`` (live KNMI station data).

    Column mapping from pv_hourly:
      p_west        -> solar_power_west_w      (W, electrical output)
      p_east        -> solar_power_east_w      (W, electrical output)
      h_sun_west    -> sun_elevation_west_deg  (degrees, for night filtering)
      h_sun_east    -> sun_elevation_east_deg  (degrees, for night filtering)
      t2m           -> temperature_c           (Celsius, shared with KNMI)
      g(i)_west     -> irradiance_west_wm2     (W/m2, tilted surface)
      g(i)_east     -> irradiance_east_wm2     (W/m2, tilted surface)
      int_west      -> intensity_west          (unknown unit, kept as-is)
      int_east      -> intensity_east          (unknown unit, kept as-is)
      ws10m         -> dropped                 (redundant with wind_speed_ms)
    """

    __tablename__ = "weather_snapshot"
    __table_args__ = (
        UniqueConstraint("source", "timestamp", name="uq_weather_snapshot_source_ts"),
        Index("ix_weather_snapshot_source_ts", "source", "timestamp"),
        Index("ix_weather_snapshot_timestamp", "timestamp"),
    )

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    # Origin identifier — e.g. "pv_2023", "knmi_06280", "knmi_06260"
    source: str = Field(nullable=False, index=True)

    # Station metadata (wind / KNMI sources)
    station_code: Optional[str] = Field(default=None)
    station_name: Optional[str] = Field(default=None)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)

    # Solar fields (pv_2023 source)
    solar_power_west_w: Optional[float] = Field(default=None)
    solar_power_east_w: Optional[float] = Field(default=None)
    sun_elevation_west_deg: Optional[float] = Field(default=None)
    sun_elevation_east_deg: Optional[float] = Field(default=None)
    # Global irradiance on inclined surface (W/m2) — needed for variable-panel models
    irradiance_west_wm2: Optional[float] = Field(default=None)
    irradiance_east_wm2: Optional[float] = Field(default=None)
    # Intensity values from pv_hourly — exact meaning TBC
    intensity_west: Optional[float] = Field(default=None)
    intensity_east: Optional[float] = Field(default=None)

    # Wind & meteorology (shared / KNMI sources)
    wind_speed_ms: Optional[float] = Field(default=None)
    wind_direction_deg: Optional[float] = Field(default=None)
    # temperature_c used by both sources: t2m (pv_2023) and temperature_c (KNMI)
    temperature_c: Optional[float] = Field(default=None)
    air_pressure_hpa: Optional[float] = Field(default=None)
