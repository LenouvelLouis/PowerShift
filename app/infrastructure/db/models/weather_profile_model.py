"""SQLModel ORM model for the unified weather_profile table.

Stores 30-minute aggregated observations for Groningen Eelde (KNMI station 06280).
Source dataset: Actuele10mindataKNMIstations v2 (NetCDF, 10-min intervals).

Each row represents one 30-min slot (timestamp = end of slot, UTC).
The table contains 17 520 rows for a full year (365 × 48 slots/day).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

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
    wind_speed_ms: Optional[float] = None       # ff  [m/s]
    wind_dir_deg: Optional[float] = None         # dd  [°]
    wind_gust_ms: Optional[float] = None         # fx  [m/s]

    # Atmospheric
    temperature_c: Optional[float] = None        # ta  [°C]
    air_pressure_hpa: Optional[float] = None     # pp  [hPa]
    humidity_pct: Optional[float] = None         # rh  [%]

    # Solar (KNMI variable: qg → average W/m², ss → summed sunshine minutes)
    radiation_wm2: Optional[float] = None        # qg  [W/m²]
    sunshine_min: Optional[float] = None         # ss  [min], max 30
