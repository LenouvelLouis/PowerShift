"""API tests for /api/v1/supplies endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestListSupplies:
    def test_returns_200(self, client: TestClient):
        response = client.get("/api/v1/supplies")
        assert response.status_code == 200

    def test_returns_list(self, client: TestClient):
        data = client.get("/api/v1/supplies").json()
        assert isinstance(data, list)


class TestCreateSupply:
    def test_create_nuclear_plant(self, client: TestClient):
        payload = {
            "name": "Test Nuclear Plant",
            "type": "nuclear_plant",
            "capacity_mw": 100.0,
            "efficiency": 1.0,
            "status": "active",
            "unit": "MW",
            "description": "Test supply for US-01/02",
        }
        response = client.post("/api/v1/supplies", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Nuclear Plant"
        assert data["capacity_mw"] == 100.0
        assert data["carrier"] == "nuclear"

    def test_create_returns_uuid(self, client: TestClient):
        payload = {
            "name": "UUID Check Plant",
            "type": "nuclear_plant",
            "capacity_mw": 50.0,
        }
        data = client.post("/api/v1/supplies", json=payload).json()
        assert "id" in data
        assert len(data["id"]) == 36  # UUID format


class TestGetSupply:
    def test_get_nonexistent_returns_404(self, client: TestClient):
        response = client.get(
            "/api/v1/supplies/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


class TestDeleteSupply:
    def test_delete_nonexistent_returns_404(self, client: TestClient):
        response = client.delete(
            "/api/v1/supplies/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
