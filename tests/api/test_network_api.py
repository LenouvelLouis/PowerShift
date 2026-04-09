"""API tests for /api/v1/network endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestListNetwork:
    def test_returns_200(self, client: TestClient):
        response = client.get("/api/v1/network")
        assert response.status_code == 200

    def test_returns_list(self, client: TestClient):
        data = client.get("/api/v1/network").json()
        assert isinstance(data, list)


class TestCreateTransformer:
    def test_create_transformer(self, client: TestClient):
        payload = {
            "name": "Test Transformer",
            "type": "transformer",
            "voltage_kv": 10.0,
            "capacity_mva": 200.0,
            "voltage_hv_kv": 10.0,
            "voltage_lv_kv": 0.4,
            "status": "active",
            "unit": "MVA",
            "description": "Test transformer for US-02",
        }
        response = client.post("/api/v1/network", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Transformer"
        assert data["type"] == "transformer"
        assert data["capacity_mva"] == 200.0

    def test_create_cable(self, client: TestClient):
        payload = {
            "name": "Test Cable",
            "type": "cable",
            "voltage_kv": 10.0,
            "length_km": 5.0,
            "resistance_ohm_per_km": 0.1,
            "reactance_ohm_per_km": 0.05,
        }
        response = client.post("/api/v1/network", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "cable"
        assert data["length_km"] == 5.0


class TestGetNetwork:
    def test_get_nonexistent_returns_404(self, client: TestClient):
        response = client.get(
            "/api/v1/network/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


class TestDeleteNetwork:
    def test_delete_nonexistent_returns_404(self, client: TestClient):
        response = client.delete(
            "/api/v1/network/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
