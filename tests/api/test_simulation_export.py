"""API tests for CSV and PDF export endpoints.

Tests:
  - GET /api/v1/simulation/{id}/export/csv  -> 200 text/csv or 404
  - GET /api/v1/simulation/{id}/export/pdf  -> 200 application/pdf or 404
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestExportCsv:
    def test_csv_nonexistent_returns_404(self, client: TestClient):
        response = client.get(
            "/api/v1/simulation/00000000-0000-0000-0000-000000000000/export/csv"
        )
        assert response.status_code == 404

    def test_csv_returns_200_with_correct_content_type(self, client: TestClient):
        """Save a simulation first, then export as CSV."""
        save_resp = client.post(
            "/api/v1/simulation/save",
            json={"snapshot_hours": 24},
        )
        assert save_resp.status_code == 200
        sim_id = save_resp.json()["id"]

        response = client.get(f"/api/v1/simulation/{sim_id}/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers.get("content-disposition", "")
        assert f"simulation_{sim_id}.csv" in response.headers.get("content-disposition", "")

    def test_csv_contains_header_and_data(self, client: TestClient):
        save_resp = client.post(
            "/api/v1/simulation/save",
            json={"snapshot_hours": 24},
        )
        sim_id = save_resp.json()["id"]

        response = client.get(f"/api/v1/simulation/{sim_id}/export/csv")
        text = response.text
        assert "# PowerShift Simulation Export" in text
        assert "# total_supply_mwh" in text
        assert "# total_demand_mwh" in text
        assert "# balance_mwh" in text


class TestExportPdf:
    def test_pdf_nonexistent_returns_404(self, client: TestClient):
        response = client.get(
            "/api/v1/simulation/00000000-0000-0000-0000-000000000000/export/pdf"
        )
        assert response.status_code == 404

    def test_pdf_returns_200_with_correct_content_type(self, client: TestClient):
        save_resp = client.post(
            "/api/v1/simulation/save",
            json={"snapshot_hours": 24},
        )
        assert save_resp.status_code == 200
        sim_id = save_resp.json()["id"]

        response = client.get(f"/api/v1/simulation/{sim_id}/export/pdf")
        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]
        assert "attachment" in response.headers.get("content-disposition", "")
        assert f"simulation_{sim_id}.pdf" in response.headers.get("content-disposition", "")

    def test_pdf_starts_with_pdf_magic_bytes(self, client: TestClient):
        save_resp = client.post(
            "/api/v1/simulation/save",
            json={"snapshot_hours": 24},
        )
        sim_id = save_resp.json()["id"]

        response = client.get(f"/api/v1/simulation/{sim_id}/export/pdf")
        assert response.content[:5] == b"%PDF-"
