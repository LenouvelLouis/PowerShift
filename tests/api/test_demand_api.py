"""API tests for /api/v1/demands endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestListDemands:
    def test_returns_200(self, client: TestClient):
        response = client.get("/api/v1/demands")
        assert response.status_code == 200

    def test_returns_paginated_response(self, client: TestClient):
        data = client.get("/api/v1/demands").json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert isinstance(data["items"], list)

    def test_default_pagination(self, client: TestClient):
        data = client.get("/api/v1/demands").json()
        assert data["page"] == 1
        assert data["size"] == 20

    def test_custom_page_and_size(self, client: TestClient):
        data = client.get("/api/v1/demands?page=1&size=5").json()
        assert data["page"] == 1
        assert data["size"] == 5

    def test_page_zero_returns_422(self, client: TestClient):
        response = client.get("/api/v1/demands?page=0")
        assert response.status_code == 422

    def test_size_over_100_returns_422(self, client: TestClient):
        response = client.get("/api/v1/demands?size=101")
        assert response.status_code == 422


class TestCreateDemand:
    def test_create_house(self, client: TestClient):
        payload = {
            "name": "Test House",
            "type": "house",
            "load_mw": 10.0,
            "status": "active",
            "unit": "MW",
            "description": "Test house for US-01",
        }
        response = client.post("/api/v1/demands", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test House"
        assert data["type"] == "house"
        assert data["load_mw"] == 10.0

    def test_create_10_houses_for_equal_distribution(self, client: TestClient):
        """US-02: Verify we can create all 10 houses needed for equal distribution."""
        houses = []
        for i in range(10):
            payload = {
                "name": f"House {i}",
                "type": "house",
                "load_mw": 10.0,
            }
            response = client.post("/api/v1/demands", json=payload)
            assert response.status_code == 201
            houses.append(response.json())

        assert len(houses) == 10
        assert all(h["load_mw"] == 10.0 for h in houses)


class TestGetDemand:
    def test_get_nonexistent_returns_404(self, client: TestClient):
        response = client.get(
            "/api/v1/demands/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


class TestDeleteDemand:
    def test_delete_nonexistent_returns_404(self, client: TestClient):
        response = client.delete(
            "/api/v1/demands/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
