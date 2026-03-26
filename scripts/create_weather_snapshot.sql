-- scripts/create_weather_snapshot.sql
-- Idempotent: safe to run multiple times.

CREATE TABLE IF NOT EXISTS weather_snapshot (
    id                     UUID          NOT NULL DEFAULT gen_random_uuid(),
    "timestamp"            TIMESTAMPTZ   NOT NULL,
    source                 VARCHAR       NOT NULL,

    -- Station metadata (wind / KNMI sources)
    station_code           VARCHAR,
    station_name           VARCHAR,
    latitude               DOUBLE PRECISION,
    longitude              DOUBLE PRECISION,

    -- Solar fields (source = 'pv_2023')
    solar_power_west_w     REAL,
    solar_power_east_w     REAL,
    sun_elevation_west_deg REAL,
    sun_elevation_east_deg REAL,
    irradiance_west_wm2    REAL,
    irradiance_east_wm2    REAL,
    intensity_west         REAL,
    intensity_east         REAL,

    -- Wind & meteorology (shared)
    wind_speed_ms          DOUBLE PRECISION,
    wind_direction_deg     DOUBLE PRECISION,
    temperature_c          DOUBLE PRECISION,
    air_pressure_hpa       DOUBLE PRECISION,

    CONSTRAINT weather_snapshot_pkey              PRIMARY KEY (id),
    CONSTRAINT uq_weather_snapshot_source_ts      UNIQUE (source, "timestamp")
);

CREATE INDEX IF NOT EXISTS ix_weather_snapshot_timestamp
    ON weather_snapshot ("timestamp");

CREATE INDEX IF NOT EXISTS ix_weather_snapshot_source
    ON weather_snapshot (source);

CREATE INDEX IF NOT EXISTS ix_weather_snapshot_source_ts
    ON weather_snapshot (source, "timestamp");
