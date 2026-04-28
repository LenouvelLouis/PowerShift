"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-28

Baseline migration generated from existing SQLModel definitions.
Tables: demands, supplies, network_components, simulation_requests,
        simulation_results, asset_parameters, weather_profile.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── demands ──────────────────────────────────────────────────────────────
    op.create_table(
        "demands",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("load_mw", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── supplies ─────────────────────────────────────────────────────────────
    op.create_table(
        "supplies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("capacity_mw", sa.Float(), nullable=False),
        sa.Column("efficiency", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── network_components ───────────────────────────────────────────────────
    op.create_table(
        "network_components",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("voltage_kv", sa.Float(), nullable=False),
        sa.Column("capacity_mva", sa.Float(), nullable=True),
        sa.Column("losses_kw", sa.Float(), nullable=True),
        sa.Column("voltage_hv_kv", sa.Float(), nullable=True),
        sa.Column("voltage_lv_kv", sa.Float(), nullable=True),
        sa.Column("length_km", sa.Float(), nullable=True),
        sa.Column("resistance_ohm_per_km", sa.Float(), nullable=True),
        sa.Column("reactance_ohm_per_km", sa.Float(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── simulation_requests ──────────────────────────────────────────────────
    op.create_table(
        "simulation_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("snapshot_hours", sa.Integer(), nullable=False),
        sa.Column("solver", sa.String(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("pypsa_params", sa.JSON(), nullable=True),
        sa.Column("asset_overrides", sa.JSON(), nullable=True),
        sa.Column("supply_ids", sa.JSON(), nullable=False),
        sa.Column("demand_ids", sa.JSON(), nullable=False),
        sa.Column("network_ids", sa.JSON(), nullable=False),
        sa.Column("hourly_load_overrides", sa.JSON(), nullable=True),
        sa.Column("optimization_objective", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── simulation_results ───────────────────────────────────────────────────
    op.create_table(
        "simulation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("total_supply_mwh", sa.Float(), nullable=True),
        sa.Column("total_demand_mwh", sa.Float(), nullable=True),
        sa.Column("balance_mwh", sa.Float(), nullable=True),
        sa.Column("objective_value", sa.Float(), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["request_id"], ["simulation_requests.id"], ondelete="CASCADE"),
    )

    # ── asset_parameters ─────────────────────────────────────────────────────
    op.create_table(
        "asset_parameters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── weather_profile ──────────────────────────────────────────────────────
    op.create_table(
        "weather_profile",
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("wind_speed_ms", sa.Float(), nullable=True),
        sa.Column("wind_dir_deg", sa.Float(), nullable=True),
        sa.Column("wind_gust_ms", sa.Float(), nullable=True),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("air_pressure_hpa", sa.Float(), nullable=True),
        sa.Column("humidity_pct", sa.Float(), nullable=True),
        sa.Column("radiation_wm2", sa.Float(), nullable=True),
        sa.Column("sunshine_min", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("timestamp"),
    )
    op.create_index("ix_weather_profile_timestamp", "weather_profile", ["timestamp"])


def downgrade() -> None:
    op.drop_index("ix_weather_profile_timestamp", table_name="weather_profile")
    op.drop_table("weather_profile")
    op.drop_table("asset_parameters")
    op.drop_table("simulation_results")
    op.drop_table("simulation_requests")
    op.drop_table("network_components")
    op.drop_table("supplies")
    op.drop_table("demands")
