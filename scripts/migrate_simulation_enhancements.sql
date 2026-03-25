-- Migration: add new columns to simulation_requests
-- Run once against the NeonDB database.

ALTER TABLE simulation_requests
    ADD COLUMN IF NOT EXISTS start_date             DATE         DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS end_date               DATE         DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS hourly_load_overrides  JSONB        DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS optimization_objective VARCHAR(32)  DEFAULT 'min_cost' NOT NULL;
