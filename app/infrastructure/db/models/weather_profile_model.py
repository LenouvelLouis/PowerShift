"""SQLModel ORM model for the unified weather_profile table.

Stores 30-minute aggregated observations for Groningen Eelde (KNMI station 06280).
Source dataset: Actuele10mindataKNMIstations v2 (NetCDF, 10-min intervals).

Each row represents one 30-min slot (timestamp = end of slot, UTC).
The table contains 17 520 rows for a full year (365 × 48 slots/day).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Index
from sqlmodel import Field, SQLModel


class WeatherProfileModel(SQLModel, table=True):
    """Unified weather profile — wind + solar + temperature at 30-min resolution."""

    __tablename__ = "weather_profile"
    __table_args__ = (
        Index("ix_weather_profile_timestamp", "timestamp"),
    )

    # Primary key: end-of-slot UTC timestamp (e.g. 2025-01-01 00:30:00+00)
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), primary_key=True, nullable=False)
    )

    # Wind (KNMI variable: ff → average, dd → circular mean, fx → max)
    wind_speed_ms: float | None = None       # ff  [m/s]
    wind_dir_deg: float | None = None         # dd  [°]
    wind_gust_ms: float | None = None         # fx  [m/s]

    # Atmospheric
    temperature_c: float | None = None        # ta  [°C]
    air_pressure_hpa: float | None = None     # pp  [hPa]
    humidity_pct: float | None = None         # rh  [%]

    # Solar (KNMI variable: qg → average W/m², ss → summed sunshine minutes)
    radiation_wm2: float | None = None        # qg  [W/m²]
    sunshine_min: float | None = None         # ss  [min], max 30
