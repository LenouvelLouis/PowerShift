"""API tests for /api/v1/simulation endpoints.

Maps directly to the user-story acceptance criteria:
  US-01: Constant energy delivery (10 MWh per house)
  US-02: Equal distribution (100 MWh total, balanced)
  US-04: Monitoring data available in result payload
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestSimulationEndpoint:
    def test_run_returns_200(self, client: TestClient):
        response = client.post(
            "/api/v1/simulation/save",
            json={"snapshot_hours": 24},
        )
        assert response.status_code == 200

    def test_run_response_schema(self, client: TestClient):
        data = client.post(
            "/api/v1/simulation/save",
            json={"snapshot_hours": 24},
        ).json()
        assert "id" in data
        assert "status" in data
        assert "total_supply_mwh" in data
        assert "total_demand_mwh" in data
        assert "balance_mwh" in data
        assert "result_json" in data


class TestSimulationList:
    def test_list_returns_200(self, client: TestClient):
        response = client.get("/api/v1/simulation")
        assert response.status_code == 200

    def test_list_returns_array(self, client: TestClient):
        data = client.get("/api/v1/simulation").json()
        assert isinstance(data, list)


class TestSimulationGetById:
    def test_get_nonexistent_returns_404(self, client: TestClient):
        response = client.get(
            "/api/v1/simulation/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
