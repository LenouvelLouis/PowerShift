"""API tests for /api/v1/supplies endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestListSupplies:
    def test_returns_200(self, client: TestClient):
        response = client.get("/api/v1/supplies")
        assert response.status_code == 200

    def test_returns_paginated_response(self, client: TestClient):
        data = client.get("/api/v1/supplies").json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert isinstance(data["items"], list)

    def test_default_pagination(self, client: TestClient):
        data = client.get("/api/v1/supplies").json()
        assert data["page"] == 1
        assert data["size"] == 20

    def test_custom_page_and_size(self, client: TestClient):
        data = client.get("/api/v1/supplies?page=1&size=5").json()
        assert data["page"] == 1
        assert data["size"] == 5

    def test_page_zero_returns_422(self, client: TestClient):
        response = client.get("/api/v1/supplies?page=0")
        assert response.status_code == 422

    def test_size_over_100_returns_422(self, client: TestClient):
        response = client.get("/api/v1/supplies?size=101")
        assert response.status_code == 422

    def test_size_zero_returns_422(self, client: TestClient):
        response = client.get("/api/v1/supplies?size=0")
        assert response.status_code == 422

    def test_pages_field_computed(self, client: TestClient):
        data = client.get("/api/v1/supplies?size=1").json()
        total = data["total"]
        assert data["pages"] >= 1
        if total > 0:
            assert data["pages"] == (total + 0) // 1  # ceil(total/1) == total


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
