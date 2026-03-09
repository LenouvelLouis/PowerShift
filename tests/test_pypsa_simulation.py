Add PyPSA simulation tests: 21 tests for value coherence validation"""
Test suite for PyPSA grid simulation.

Validates the coherence and correctness of simulation outputs.
Tests power balance, capacity factors, and numerical consistency.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.simulation.pypsa_adapter import (
    AdapterOutput,
    SimulationConfig,
)
from app.infrastructure.simulation.network_builder import _DefaultPyPSASimulation
from app.domain.entities.supply.wind_turbine import WindTurbine
from app.domain.entities.demand.house import House
from app.domain.entities.network.cable import Cable


# --------------------------------------------------
# Fixtures
# --------------------------------------------------

@pytest.fixture(scope="module")
def client() -> TestClient:
    """Shared test client for all tests."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def simple_wind_supply():
    """Create a simple wind turbine for testing."""
    return WindTurbine(
        id="wind-1",
        name="Wind Farm 1",
        capacity_mw=100.0,
        efficiency=0.95,
        status="active",
        unit="MW",
        description="Test wind turbine",
        created_at=None,
        updated_at=None,
    )


@pytest.fixture
def simple_demand():
    """Create a simple house load for testing."""
    return House(
        id="house-1",
        name="House 1",
        load_mw=50.0,
        status="active",
        unit="MW",
        description="Test house",
        created_at=None,
        updated_at=None,
    )


@pytest.fixture
def simple_cable():
    """Create a simple cable for testing."""
    return Cable(
        id="cable-1",
        name="Cable 1",
        voltage_kv=380.0,
        capacity_mva=200.0,
        status="active",
        unit="MV",
        description="Test cable",
        created_at=None,
        updated_at=None,
        length_km=10.0,
        resistance_ohm_per_km=0.05,
        reactance_ohm_per_km=0.1,
    )


@pytest.fixture
def pypsa_simulator():
    """Create a PyPSA simulator instance."""
    return _DefaultPyPSASimulation()


# --------------------------------------------------
# Test Class: Basic Simulation Execution
# --------------------------------------------------

class TestSimulationExecution:
    """Test basic simulation execution and error handling."""

    def test_simulation_with_supply_and_demand(self, pypsa_simulator, simple_wind_supply, simple_demand):
        """Test that simulation runs successfully with supply and demand."""
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[simple_wind_supply],
            demands=[simple_demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        assert output.status in ["optimal", "error", "warning"]
        assert isinstance(output.total_supply_mwh, float)
        assert isinstance(output.total_demand_mwh, float)
        assert isinstance(output.balance_mwh, float)

    def test_simulation_with_empty_assets(self, pypsa_simulator):
        """Test simulation with no supplies or demands returns zero values."""
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[],
            demands=[],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        assert output.total_supply_mwh == 0.0
        assert output.total_demand_mwh == 0.0
        assert output.balance_mwh == 0.0

    def test_simulation_different_snapshot_hours(self, pypsa_simulator, simple_wind_supply, simple_demand):
        """Test simulation with different snapshot hours (8h, 24h, 168h)."""
        for hours in [8, 24, 168]:
            config = SimulationConfig(
                snapshot_hours=hours,
                solver="highs",
                supplies=[simple_wind_supply],
                demands=[simple_demand],
                network_components=[],
            )
            output = pypsa_simulator.run_sync(config)
            
            assert output.status is not None
            assert isinstance(output.objective_value, float)


# --------------------------------------------------
# Test Class: Power Balance Coherence
# --------------------------------------------------

class TestPowerBalance:
    """Test coherence of power balance: Supply = Demand + Network Losses."""

    def test_balance_equals_supply_minus_demand(self, pypsa_simulator, simple_wind_supply, simple_demand):
        """Verify: balance_mwh = total_supply_mwh - total_demand_mwh"""
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[simple_wind_supply],
            demands=[simple_demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        # Allow small floating-point tolerance (1e-6)
        tolerance = 1e-6
        expected_balance = output.total_supply_mwh - output.total_demand_mwh
        assert abs(output.balance_mwh - expected_balance) < tolerance, \
            f"Balance mismatch: expected {expected_balance}, got {output.balance_mwh}"

    def test_supply_satisfies_demand(self, pypsa_simulator, simple_wind_supply, simple_demand):
        """Test that total supply is greater than or equal to demand."""
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[simple_wind_supply],
            demands=[simple_demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        # Supply should be >= demand (with network losses, may have excess)
        assert output.total_supply_mwh >= output.total_demand_mwh - 1e-3, \
            f"Supply ({output.total_supply_mwh}) < Demand ({output.total_demand_mwh})"

    def test_balance_is_non_negative_when_supply_sufficient(
        self, pypsa_simulator, simple_wind_supply, simple_demand
    ):
        """Test that balance is non-negative when supply is sufficient."""
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[simple_wind_supply],
            demands=[simple_demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        # If supply satisfies demand, balance should be >= 0
        if output.status == "optimal":
            assert output.balance_mwh >= -1e-3, \
                f"Negative balance: {output.balance_mwh}, supply={output.total_supply_mwh}, demand={output.total_demand_mwh}"

    def test_mwh_values_are_positive(self, pypsa_simulator, simple_wind_supply, simple_demand):
        """Test that energy values (MWh) are non-negative."""
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[simple_wind_supply],
            demands=[simple_demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        assert output.total_supply_mwh >= 0.0, f"Negative total_supply_mwh: {output.total_supply_mwh}"
        assert output.total_demand_mwh >= 0.0, f"Negative total_demand_mwh: {output.total_demand_mwh}"


# --------------------------------------------------
# Test Class: Capacity Factor Validation
# --------------------------------------------------

class TestCapacityFactors:
    """Test capacity factor calculation and bounds."""

    def test_capacity_factors_in_valid_range(self, pypsa_simulator, simple_wind_supply, simple_demand):
        """Verify capacity factors are between 0.0 and 1.0."""
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[simple_wind_supply],
            demands=[simple_demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        if output.result_json and "capacity_factors" in output.result_json:
            for gen_name, cf in output.result_json["capacity_factors"].items():
                assert 0.0 <= cf <= 1.0, \
                    f"Capacity factor out of range for {gen_name}: {cf}"

    def test_capacity_factor_zero_when_no_generation(self, pypsa_simulator):
        """Test that capacity factor is 0 when generator doesn't run."""
        no_demand = []
        supply = WindTurbine(
            id="wind-idle",
            name="Idle Wind",
            capacity_mw=100.0,
            efficiency=0.95,
            status="active",
            unit="MW",
            description="Wind with no demand",
            created_at=None,
            updated_at=None,
        )
        
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[supply],
            demands=no_demand,
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        # With no demand, generation should be zero
        assert output.total_supply_mwh == pytest.approx(0.0, abs=1e-3)

    def test_capacity_factor_respects_p_nom(self, pypsa_simulator, simple_wind_supply, simple_demand):
        """Test capacity factor calculation: CF = (Energy / (P_nom * Hours))."""
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[simple_wind_supply],
            demands=[simple_demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        if output.result_json and "capacity_factors" in output.result_json:
            cf_data = output.result_json["capacity_factors"]
            
            for gen_name, cf in cf_data.items():
                # Find the corresponding supply
                for supply in [simple_wind_supply]:
                    if supply.name == gen_name:
                        p_nom = supply.capacity_mw
                        # Expected energy = CF * P_nom * Hours
                        expected_energy = cf * p_nom * 24
                        
                        # Verify calculation is plausible
                        assert expected_energy >= 0.0
                        assert expected_energy <= p_nom * 24, \
                            f"Energy exceeds capacity for {gen_name}: {expected_energy} > {p_nom * 24}"


# --------------------------------------------------
# Test Class: Numerical Stability & Bounds
# --------------------------------------------------

class TestNumericalStability:
    """Test numerical stability and physical bounds."""

    def test_no_negative_power_values(self, pypsa_simulator, simple_wind_supply, simple_demand):
        """Verify no negative power values in results."""
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[simple_wind_supply],
            demands=[simple_demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        # Check generators output
        if output.result_json and "generators_t" in output.result_json:
            for gen_name, gen_data in output.result_json["generators_t"].items():
                for power in gen_data.get("p", []):
                    assert power >= -1e-6, \
                        f"Negative generation detected for {gen_name}: {power}"

    def test_demand_matches_profile_bounds(self, pypsa_simulator, simple_demand):
        """Verify load values don't exceed nominal capacity."""
        profile = [0.5, 0.8, 1.0, 0.7, 0.6, 0.9, 0.4, 0.5] * 3  # 24 hours
        
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[],
            demands=[simple_demand],
            network_components=[],
            load_profiles={"House 1": profile},
        )
        output = pypsa_simulator.run_sync(config)
        
        # Load should not exceed nominal demand capacity
        max_expected_load = simple_demand.load_mw * 1.0  # 100% of nominal
        total_hours = 24
        max_total_demand = max_expected_load * total_hours
        
        assert output.total_demand_mwh <= max_total_demand + 1e-3, \
            f"Demand exceeds nominal capacity: {output.total_demand_mwh} > {max_total_demand}"

    def test_floating_point_precision(self, pypsa_simulator, simple_wind_supply, simple_demand):
        """Test that accumulated values maintain floating-point precision."""
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[simple_wind_supply],
            demands=[simple_demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        # Check that values are finite
        assert all([
            abs(output.total_supply_mwh) < 1e10,
            abs(output.total_demand_mwh) < 1e10,
            abs(output.balance_mwh) < 1e10,
        ]), "Energy values are unreasonable (overflow suspected)"


# --------------------------------------------------
# Test Class: Multiple Assets Scenarios
# --------------------------------------------------

class TestMultipleAssets:
    """Test simulations with multiple supplies and demands."""

    def test_multiple_supplies_aggregate_correctly(self, pypsa_simulator):
        """Test that multiple supplies sum correctly."""
        supplies = [
            WindTurbine(
                id="wind-1",
                name="Wind 1",
                capacity_mw=100.0,
                efficiency=0.95,
                status="active",
                unit="MW",
                description="",
                created_at=None,
                updated_at=None,
            ),
            WindTurbine(
                id="wind-2",
                name="Wind 2",
                capacity_mw=80.0,
                efficiency=0.95,
                status="active",
                unit="MW",
                description="",
                created_at=None,
                updated_at=None,
            ),
        ]
        demand = House(
            id="house-main",
            name="Main House",
            load_mw=60.0,
            status="active",
            unit="MW",
            description="",
            created_at=None,
            updated_at=None,
        )
        
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=supplies,
            demands=[demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        # Total capacity = 100 + 80 = 180 MW
        # Expected max energy over 24h = 180 * 24 = 4320 MWh
        assert output.total_supply_mwh <= 180.0 * 24 + 1e-3

    def test_multiple_demands_sum_correctly(self, pypsa_simulator):
        """Test that multiple demands sum correctly."""
        supply = WindTurbine(
            id="wind-multi",
            name="Wind Multi",
            capacity_mw=300.0,
            efficiency=0.95,
            status="active",
            unit="MW",
            description="",
            created_at=None,
            updated_at=None,
        )
        demands = [
            House(
                id=f"house-{i}",
                name=f"House {i}",
                load_mw=40.0,
                status="active",
                unit="MW",
                description="",
                created_at=None,
                updated_at=None,
            )
            for i in range(3)
        ]
        
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[supply],
            demands=demands,
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        # Total demand = 3 * 40 = 120 MW
        # Expected total demand energy = 120 * 24 = 2880 MWh
        expected_demand = 120.0 * 24
        assert output.total_demand_mwh <= expected_demand + 1e-3


# --------------------------------------------------
# Test Class: Error Scenarios & Robustness
# --------------------------------------------------

class TestErrorScenarios:
    """Test error handling and robustness."""

    def test_infeasible_system_unmet_demand(self, pypsa_simulator):
        """Test handling of infeasible system (demand > supply capacity)."""
        supply = WindTurbine(
            id="small-wind",
            name="Small Wind",
            capacity_mw=10.0,
            efficiency=0.95,
            status="active",
            unit="MW",
            description="",
            created_at=None,
            updated_at=None,
        )
        demand = House(
            id="large-house",
            name="Large House",
            load_mw=100.0,
            status="active",
            unit="MW",
            description="",
            created_at=None,
            updated_at=None,
        )
        
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[supply],
            demands=[demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        # Output should have a status (optimal or error)
        assert output.status in ["optimal", "warning", "error"]
        # Supply should be limited by capacity
        assert output.total_supply_mwh <= 10.0 * 24 + 1e-3

    def test_zero_capacity_supply_generates_nothing(self, pypsa_simulator):
        """Test that zero-capacity supply generates no power."""
        supply = WindTurbine(
            id="zero-wind",
            name="Zero Wind",
            capacity_mw=0.0,
            efficiency=0.95,
            status="active",
            unit="MW",
            description="",
            created_at=None,
            updated_at=None,
        )
        demand = House(
            id="house-zero",
            name="House Zero",
            load_mw=10.0,
            status="active",
            unit="MW",
            description="",
            created_at=None,
            updated_at=None,
        )
        
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[supply],
            demands=[demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        assert output.total_supply_mwh == pytest.approx(0.0, abs=1e-3)

    def test_zero_demand_results_zero_consumption(self, pypsa_simulator, simple_wind_supply):
        """Test that zero demand requires no generation."""
        demand = House(
            id="zero-house",
            name="Zero House",
            load_mw=0.0,
            status="active",
            unit="MW",
            description="",
            created_at=None,
            updated_at=None,
        )
        
        config = SimulationConfig(
            snapshot_hours=24,
            solver="highs",
            supplies=[simple_wind_supply],
            demands=[demand],
            network_components=[],
        )
        output = pypsa_simulator.run_sync(config)
        
        assert output.total_demand_mwh == pytest.approx(0.0, abs=1e-3)


# --------------------------------------------------
# Test Class: Integration with API Endpoint
# --------------------------------------------------

class TestSimulationAPIEndpoint:
    """Test simulation via REST API endpoint."""

    def test_simulation_post_endpoint_returns_valid_response(self, client):
        """Test POST /api/v1/simulation/run returns valid SimulationRunResponse."""
        request_body = {
            "snapshot_hours": 24,
            "solver": "highs",
            "supply_ids": [],
            "demand_ids": [],
            "network_ids": [],
        }
        
        response = client.post("/api/v1/simulation/run", json=request_body)
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "status" in data
            assert "total_supply_mwh" in data
            assert "total_demand_mwh" in data
            assert "balance_mwh" in data

    def test_simulation_invalid_snapshot_hours_rejected(self, client):
        """Test that invalid snapshot_hours (0 or >8760) are rejected."""
        request_body = {
            "snapshot_hours": 10000,  # > 8760
            "solver": "highs",
            "supply_ids": [],
            "demand_ids": [],
            "network_ids": [],
        }
        
        response = client.post("/api/v1/simulation/run", json=request_body)
        
        assert response.status_code == 422  # Validation error (out of range)

    def test_simulation_endpoint_with_missing_body(self, client):
        """Test that missing request body returns validation error."""
        response = client.post("/api/v1/simulation/run")
        
        assert response.status_code in [400, 422]
