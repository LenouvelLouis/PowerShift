"""SQLModel ORM models for the wind turbine module.

Only the WindMeasurementORM table is defined here — it stores raw weather
station observations and has no equivalent in the generic supply/asset schema.

Turbine model catalog entries and turbine asset deployments are stored in the
existing ``supplies`` + ``asset_parameters`` tables (see repository.py).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, Index, UniqueConstraint
from sqlmodel import Field, SQLModel


class WindMeasurementORM(SQLModel, table=True):
    """Persisted weather station observation used as input for power calculations."""

    __tablename__ = "wind_measurement"
    __table_args__ = (
        UniqueConstraint("station_code", "timestamp", name="uq_wind_measurement_station_ts"),
        Index("ix_wind_measurement_station_ts", "station_code", "timestamp"),
    )

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    station_code: str = Field(index=True)
    station_name: str
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    temperature_c: Optional[float] = None
    air_pressure_hpa: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
