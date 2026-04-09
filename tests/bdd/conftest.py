"""Shared BDD fixtures — builds domain entities and runs PyPSA directly."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.domain.entities.base_component import ComponentStatus
from app.domain.entities.demand.house import House
from app.domain.entities.network.transformer import Transformer
from app.domain.entities.supply.nuclear_plant import NuclearPlant
from app.infrastructure.simulation.pypsa_adapter import SimulationConfig
from app.infrastructure.simulation.network_builder import _DefaultPyPSASimulation


def _now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture()
def simulation_context() -> dict:
    """Mutable bag carried across Given / When / Then steps."""
    return {}


@pytest.fixture()
def pypsa_simulation() -> _DefaultPyPSASimulation:
    return _DefaultPyPSASimulation()


@pytest.fixture()
def make_generator():
    """Factory that creates a NuclearPlant supply entity."""
    def _factory(capacity_mw: float = 100.0, name: str = "generator_1") -> NuclearPlant:
        now = _now()
        return NuclearPlant(
            id=uuid.uuid4(),
            name=name,
            status=ComponentStatus.ACTIVE,
            unit="MW",
            description="Test generator",
            created_at=now,
            updated_at=now,
            capacity_mw=capacity_mw,
            efficiency=1.0,
        )
    return _factory


@pytest.fixture()
def make_house():
    """Factory that creates a House demand entity."""
    def _factory(load_mw: float = 10.0, name: str | None = None, idx: int = 0) -> House:
        now = _now()
        return House(
            id=uuid.uuid4(),
            name=name or f"house_{idx}",
            status=ComponentStatus.ACTIVE,
            unit="MW",
            description=f"Test house {idx}",
            created_at=now,
            updated_at=now,
            load_mw=load_mw,
        )
    return _factory


@pytest.fixture()
def make_transformer():
    """Factory that creates a Transformer network entity."""
    def _factory(name: str = "transformer_1") -> Transformer:
        now = _now()
        return Transformer(
            id=uuid.uuid4(),
            name=name,
            status=ComponentStatus.ACTIVE,
            unit="MVA",
            description="Test transformer",
            created_at=now,
            updated_at=now,
            voltage_kv=10.0,
            capacity_mva=200.0,
            losses_kw=0.0,
            voltage_hv_kv=10.0,
            voltage_lv_kv=0.4,
        )
    return _factory


def run_simulation(
    simulation: _DefaultPyPSASimulation,
    supplies: list,
    demands: list,
    network_components: list,
    snapshot_hours: int = 1,
):
    """Helper to execute a PyPSA simulation and return the AdapterOutput."""
    config = SimulationConfig(
        snapshot_hours=snapshot_hours,
        solver="highs",
        supplies=supplies,
        demands=demands,
        network_components=network_components,
    )
    return simulation.run_sync(config)
