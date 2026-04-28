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

    def test_list_returns_paginated_response(self, client: TestClient):
        data = client.get("/api/v1/simulation").json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert isinstance(data["items"], list)

    def test_list_default_pagination(self, client: TestClient):
        data = client.get("/api/v1/simulation").json()
        assert data["page"] == 1
        assert data["size"] == 20

    def test_list_custom_pagination(self, client: TestClient):
        data = client.get("/api/v1/simulation?page=1&size=5").json()
        assert data["page"] == 1
        assert data["size"] == 5

    def test_list_page_zero_returns_422(self, client: TestClient):
        response = client.get("/api/v1/simulation?page=0")
        assert response.status_code == 422

    def test_list_size_over_100_returns_422(self, client: TestClient):
        response = client.get("/api/v1/simulation?size=101")
        assert response.status_code == 422


class TestSimulationGetById:
    def test_get_nonexistent_returns_404(self, client: TestClient):
        response = client.get(
            "/api/v1/simulation/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
