"""Tests for multi-bus PyPSA topology.

Verifies that network_components (transformers, cables) create
proper multi-bus networks and that the LOPF stays feasible.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from datetime import datetime, UTC

from app.domain.entities.network.cable import Cable
from app.domain.entities.network.transformer import Transformer
from app.domain.entities.supply.solar_panel import SolarPanel
from app.domain.entities.supply.nuclear_plant import NuclearPlant
from app.domain.entities.demand.house import House
from app.infrastructure.simulation.network_builder import _DefaultPyPSASimulation
from app.infrastructure.simulation.pypsa_adapter import SimulationConfig

_NOW = datetime.now(UTC)


def _make_supply(name: str, capacity_mw: float, carrier: str):
    """Create a minimal supply entity."""
    if carrier == "nuclear":
        return NuclearPlant(
            id="00000000-0000-0000-0000-000000000001",
            name=name, status="active", unit="MW", description="",
            capacity_mw=capacity_mw, efficiency=1.0,
            created_at=_NOW, updated_at=_NOW,
        )
    return SolarPanel(
        id="00000000-0000-0000-0000-000000000002",
        name=name, status="active", unit="MW", description="",
        capacity_mw=capacity_mw, efficiency=1.0,
        created_at=_NOW, updated_at=_NOW,
    )


def _make_demand(name: str, load_mw: float):
    return House(
        id="00000000-0000-0000-0000-000000000010",
        name=name, status="active", unit="MW", description="",
        load_mw=load_mw,
        created_at=_NOW, updated_at=_NOW,
    )


def _make_transformer(name: str, hv: float, lv: float, mva: float):
    return Transformer(
        id=f"t-{name}", name=name, status="active", unit="MVA",
        description="", voltage_kv=hv, capacity_mva=mva, losses_kw=None,
        voltage_hv_kv=hv, voltage_lv_kv=lv,
        created_at=_NOW, updated_at=_NOW,
    )


def _make_cable(name: str, voltage: float, mva: float, length: float):
    return Cable(
        id=f"c-{name}", name=name, status="active", unit="MVA",
        description="", voltage_kv=voltage, capacity_mva=mva, losses_kw=None,
        length_km=length, resistance_ohm_per_km=0.1, reactance_ohm_per_km=0.05,
        created_at=_NOW, updated_at=_NOW,
    )


class TestSingleBusBackwardCompat:
    """When no network_components, should use single main_bus."""

    def test_single_bus_optimal(self):
        sim = _DefaultPyPSASimulation()
        config = SimulationConfig(
            snapshot_hours=24,
            supplies=[_make_supply("solar", 200, "solar")],
            demands=[_make_demand("house", 50)],
            network_components=[],
        )
        result = sim.run_sync(config)
        assert result.status == "optimized"
        assert result.total_supply_mwh > 0
        assert result.total_demand_mwh > 0


class TestTwoBusTransformer:
    """Two buses connected by a transformer."""

    def test_two_bus_optimal(self):
        sim = _DefaultPyPSASimulation()
        trafo = _make_transformer("HV/MV", hv=400, lv=20, mva=2500)
        config = SimulationConfig(
            snapshot_hours=24,
            supplies=[_make_supply("nuclear", 1600, "nuclear")],
            demands=[_make_demand("city", 120)],
            network_components=[trafo],
        )
        result = sim.run_sync(config)
        assert result.status == "optimized"
        assert result.total_demand_mwh > 0
        # Nuclear should provide energy (check it appears in generators_t)
        gen_t = result.result_json.get("generators_t", {})
        assert "nuclear" in gen_t
        nuclear_total = sum(gen_t["nuclear"]["p"])
        assert nuclear_total > 0


class TestThreeBusChain:
    """400kV → 20kV → 0.4kV via two transformers."""

    def test_three_bus_chain_optimal(self):
        sim = _DefaultPyPSASimulation()
        trafo1 = _make_transformer("HV/MV", hv=400, lv=20, mva=2500)
        trafo2 = _make_transformer("MV/LV", hv=20, lv=0.4, mva=50)
        config = SimulationConfig(
            snapshot_hours=24,
            supplies=[_make_supply("solar", 200, "solar")],
            demands=[_make_demand("house", 10)],
            network_components=[trafo1, trafo2],
        )
        result = sim.run_sync(config)
        assert result.status == "optimized"


class TestCableCreatesBus:
    """A cable should create a secondary bus and keep the model feasible."""

    def test_cable_feasible(self):
        sim = _DefaultPyPSASimulation()
        trafo = _make_transformer("MV/LV", hv=10, lv=0.4, mva=50)
        cable = _make_cable("feeder", voltage=0.4, mva=50, length=0.5)
        config = SimulationConfig(
            snapshot_hours=24,
            supplies=[_make_supply("solar", 200, "solar")],
            demands=[_make_demand("house", 10)],
            network_components=[trafo, cable],
        )
        result = sim.run_sync(config)
        assert result.status == "optimized"


class TestIsolatedBusUsesBackstop:
    """When buses are not fully connected, backstop generators keep it feasible."""

    def test_isolated_bus_still_optimal(self):
        sim = _DefaultPyPSASimulation()
        # Transformer 400→20kV but cable at 10kV (no link between 20kV and 10kV)
        trafo = _make_transformer("HV/MV", hv=400, lv=20, mva=2500)
        cable = _make_cable("orphan", voltage=10, mva=100, length=5)
        config = SimulationConfig(
            snapshot_hours=24,
            supplies=[_make_supply("solar", 200, "solar")],
            demands=[_make_demand("house", 10)],
            network_components=[trafo, cable],
        )
        result = sim.run_sync(config)
        # Should NOT be infeasible -- backstop generators handle isolated buses
        assert result.status == "optimized"


class TestResultContainsBusData:
    """result_json should contain buses_t and lines_t for multi-bus."""

    def test_buses_t_in_result(self):
        sim = _DefaultPyPSASimulation()
        trafo = _make_transformer("HV/MV", hv=400, lv=20, mva=2500)
        config = SimulationConfig(
            snapshot_hours=24,
            supplies=[_make_supply("solar", 200, "solar")],
            demands=[_make_demand("house", 10)],
            network_components=[trafo],
        )
        result = sim.run_sync(config)
        assert "buses_t" in result.result_json
        assert "lines_t" in result.result_json
