"""SQLModel ORM model for pv_hourly table (read-only)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, Float
from sqlmodel import Field, SQLModel


class PVHourlyModel(SQLModel, table=True):
    __tablename__ = "pv_hourly"

    time: str = Field(primary_key=True)  # format YYYYMMDD:HHMM
    t2m: Optional[float] = None
    ws10m: Optional[float] = None
    p_west: Optional[float] = None
    g_i_west: Optional[float] = Field(default=None, sa_column=Column("g(i)_west", Float))
    h_sun_west: Optional[float] = None
    int_west: Optional[float] = None
    p_east: Optional[float] = None
    g_i_east: Optional[float] = Field(default=None, sa_column=Column("g(i)_east", Float))
    h_sun_east: Optional[float] = None
    int_east: Optional[float] = None
