"""Unit tests for ExportService — CSV and PDF generation logic."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.application.services.export_service import ExportService


SAMPLE_RESULT_JSON = {
    "generators_t": {
        "solar_panel_1": [0.0, 0.5, 1.2, 0.8],
        "wind_turbine_1": [1.0, 1.5, 0.9, 1.1],
    },
    "loads_t": {
        "house_1": [0.8, 0.9, 1.0, 0.7],
    },
    "capacity_factors": {
        "solar_panel_1": 0.18,
        "wind_turbine_1": 0.35,
    },
    "grid_exchange": {
        "total_import_mwh": 2.5,
        "total_export_mwh": 1.2,
    },
}

SIM_ID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
CREATED = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)


class TestBuildCsv:
    def test_csv_contains_summary(self):
        csv_text = ExportService.build_csv(
            simulation_id=SIM_ID,
            status="optimal",
            solver="highs",
            total_supply_mwh=10.5,
            total_demand_mwh=9.8,
            balance_mwh=0.7,
            result_json=SAMPLE_RESULT_JSON,
            created_at=CREATED,
        )
        assert "# PowerShift Simulation Export" in csv_text
        assert "# total_supply_mwh" in csv_text
        assert "10.5000" in csv_text

    def test_csv_has_header_row(self):
        csv_text = ExportService.build_csv(
            simulation_id=SIM_ID,
            status="optimal",
            solver="highs",
            total_supply_mwh=10.5,
            total_demand_mwh=9.8,
            balance_mwh=0.7,
            result_json=SAMPLE_RESULT_JSON,
            created_at=CREATED,
        )
        assert "hour" in csv_text
        assert "solar_panel_1 (MW)" in csv_text
        assert "wind_turbine_1 (MW)" in csv_text
        assert "house_1 (MW)" in csv_text

    def test_csv_has_correct_row_count(self):
        csv_text = ExportService.build_csv(
            simulation_id=SIM_ID,
            status="optimal",
            solver="highs",
            total_supply_mwh=10.5,
            total_demand_mwh=9.8,
            balance_mwh=0.7,
            result_json=SAMPLE_RESULT_JSON,
            created_at=CREATED,
        )
        lines = [l for l in csv_text.strip().split("\n") if l and not l.startswith("#") and l != ""]
        # header + 4 data rows (but filter out blank lines)
        data_lines = [l for l in lines if "hour" in l or l[0].isdigit()]
        assert len(data_lines) == 5  # 1 header + 4 data rows

    def test_csv_handles_none_result_json(self):
        csv_text = ExportService.build_csv(
            simulation_id=SIM_ID,
            status="error",
            solver="highs",
            total_supply_mwh=None,
            total_demand_mwh=None,
            balance_mwh=None,
            result_json=None,
            created_at=CREATED,
        )
        assert "# No time-series data available." in csv_text

    def test_csv_handles_empty_generators(self):
        csv_text = ExportService.build_csv(
            simulation_id=SIM_ID,
            status="optimal",
            solver="highs",
            total_supply_mwh=0.0,
            total_demand_mwh=0.0,
            balance_mwh=0.0,
            result_json={"generators_t": {}, "loads_t": {}},
            created_at=CREATED,
        )
        assert "# No time-series data available." in csv_text

    def test_csv_includes_capacity_factors(self):
        csv_text = ExportService.build_csv(
            simulation_id=SIM_ID,
            status="optimal",
            solver="highs",
            total_supply_mwh=10.5,
            total_demand_mwh=9.8,
            balance_mwh=0.7,
            result_json=SAMPLE_RESULT_JSON,
            created_at=CREATED,
        )
        assert "# Capacity Factors" in csv_text
        assert "0.1800" in csv_text
        assert "0.3500" in csv_text

    def test_csv_includes_dates(self):
        csv_text = ExportService.build_csv(
            simulation_id=SIM_ID,
            status="optimal",
            solver="highs",
            total_supply_mwh=10.5,
            total_demand_mwh=9.8,
            balance_mwh=0.7,
            result_json=SAMPLE_RESULT_JSON,
            created_at=CREATED,
            start_date="2025-01-01",
            end_date="2025-01-02",
        )
        assert "# start_date,2025-01-01" in csv_text
        assert "# end_date,2025-01-02" in csv_text


class TestBuildPdf:
    def test_pdf_returns_bytes(self):
        pdf_bytes = ExportService.build_pdf(
            simulation_id=SIM_ID,
            status="optimal",
            solver="highs",
            total_supply_mwh=10.5,
            total_demand_mwh=9.8,
            balance_mwh=0.7,
            objective_value=42.0,
            result_json=SAMPLE_RESULT_JSON,
            created_at=CREATED,
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100

    def test_pdf_starts_with_magic_bytes(self):
        pdf_bytes = ExportService.build_pdf(
            simulation_id=SIM_ID,
            status="optimal",
            solver="highs",
            total_supply_mwh=10.5,
            total_demand_mwh=9.8,
            balance_mwh=0.7,
            objective_value=42.0,
            result_json=SAMPLE_RESULT_JSON,
            created_at=CREATED,
        )
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_handles_none_values(self):
        pdf_bytes = ExportService.build_pdf(
            simulation_id=SIM_ID,
            status="error",
            solver="highs",
            total_supply_mwh=None,
            total_demand_mwh=None,
            balance_mwh=None,
            objective_value=None,
            result_json=None,
            created_at=CREATED,
        )
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_handles_empty_result_json(self):
        pdf_bytes = ExportService.build_pdf(
            simulation_id=SIM_ID,
            status="optimal",
            solver="highs",
            total_supply_mwh=0.0,
            total_demand_mwh=0.0,
            balance_mwh=0.0,
            objective_value=0.0,
            result_json={},
            created_at=CREATED,
        )
        assert pdf_bytes[:5] == b"%PDF-"
