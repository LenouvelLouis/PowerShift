"""API tests for /api/v1/network endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestListNetwork:
    def test_returns_200(self, client: TestClient):
        response = client.get("/api/v1/network")
        assert response.status_code == 200

    def test_returns_paginated_response(self, client: TestClient):
        data = client.get("/api/v1/network").json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert isinstance(data["items"], list)

    def test_default_pagination(self, client: TestClient):
        data = client.get("/api/v1/network").json()
        assert data["page"] == 1
        assert data["size"] == 20

    def test_custom_page_and_size(self, client: TestClient):
        data = client.get("/api/v1/network?page=1&size=5").json()
        assert data["page"] == 1
        assert data["size"] == 5

    def test_page_zero_returns_422(self, client: TestClient):
        response = client.get("/api/v1/network?page=0")
        assert response.status_code == 422

    def test_size_over_100_returns_422(self, client: TestClient):
        response = client.get("/api/v1/network?size=101")
        assert response.status_code == 422


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
