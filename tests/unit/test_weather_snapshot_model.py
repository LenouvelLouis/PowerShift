"""Unit tests for WeatherSnapshotORM model structure."""
from __future__ import annotations


def test_weather_snapshot_table_name():
    from app.infrastructure.db.models.weather_snapshot_model import WeatherSnapshotORM
    assert WeatherSnapshotORM.__tablename__ == "weather_snapshot"


def test_weather_snapshot_has_required_columns():
    from app.infrastructure.db.models.weather_snapshot_model import WeatherSnapshotORM

    cols = {c.name for c in WeatherSnapshotORM.__table__.columns}
    required = {
        "id",
        "timestamp",
        "source",
        # station metadata
        "station_code",
        "station_name",
        "latitude",
        "longitude",
        # solar fields
        "solar_power_west_w",
        "solar_power_east_w",
        "sun_elevation_west_deg",
        "sun_elevation_east_deg",
        "irradiance_west_wm2",
        "irradiance_east_wm2",
        "intensity_west",
        "intensity_east",
        # wind + meteo fields
        "wind_speed_ms",
        "wind_direction_deg",
        "temperature_c",
        "air_pressure_hpa",
    }
    assert required.issubset(cols), f"Missing columns: {required - cols}"


def test_weather_snapshot_has_no_old_pv_column_names():
    """Old pv_hourly column names must not appear — they are renamed or dropped."""
    from app.infrastructure.db.models.weather_snapshot_model import WeatherSnapshotORM

    cols = {c.name for c in WeatherSnapshotORM.__table__.columns}
    old_names = {"t2m", "ws10m", "g(i)_west", "g(i)_east", "int_west", "int_east",
                 "p_west", "p_east", "h_sun_west", "h_sun_east"}
    assert old_names.isdisjoint(cols), f"Old column names found (should be renamed): {old_names & cols}"


def test_weather_snapshot_unique_constraint():
    from app.infrastructure.db.models.weather_snapshot_model import WeatherSnapshotORM

    constraint_names = {
        c.name
        for c in WeatherSnapshotORM.__table__.constraints
    }
    assert "uq_weather_snapshot_source_ts" in constraint_names
