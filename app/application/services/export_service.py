"""Export service — generates CSV and PDF representations of simulation results.

No framework dependency (no fastapi / sqlalchemy imports).
Units: power in MW, energy in MWh.
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ExportService:
    """Pure application service — transforms a SimulationRunResponse dict into CSV / PDF bytes."""

    # ── CSV ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def build_csv(
        *,
        simulation_id: uuid.UUID,
        status: str,
        solver: str,
        total_supply_mwh: float | None,
        total_demand_mwh: float | None,
        balance_mwh: float | None,
        result_json: dict | None,
        created_at: datetime,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """Return CSV text with a summary header section followed by hourly time-series.

        Columns: hour, <generator_name (MW)>..., <load_name (MW)>...
        """
        buf = io.StringIO()
        writer = csv.writer(buf)

        # ── Summary section ──────────────────────────────────────────────────────
        writer.writerow(["# PowerShift Simulation Export"])
        writer.writerow(["# id", str(simulation_id)])
        writer.writerow(["# status", status])
        writer.writerow(["# solver", solver])
        writer.writerow(["# created_at", str(created_at)])
        if start_date:
            writer.writerow(["# start_date", start_date])
        if end_date:
            writer.writerow(["# end_date", end_date])
        writer.writerow(["# total_supply_mwh", _fmt(total_supply_mwh)])
        writer.writerow(["# total_demand_mwh", _fmt(total_demand_mwh)])
        writer.writerow(["# balance_mwh", _fmt(balance_mwh)])

        # Capacity factors
        capacity_factors: dict = (result_json or {}).get("capacity_factors", {})
        if capacity_factors:
            writer.writerow([])
            writer.writerow(["# Capacity Factors"])
            for name, value in capacity_factors.items():
                writer.writerow([f"# {name}", _fmt(value)])

        writer.writerow([])

        # ── Time-series section ──────────────────────────────────────────────────
        generators_t: dict[str, list] = (result_json or {}).get("generators_t", {})
        loads_t: dict[str, list] = (result_json or {}).get("loads_t", {})

        if not generators_t and not loads_t:
            writer.writerow(["# No time-series data available."])
            return buf.getvalue()

        gen_names = sorted(generators_t.keys())
        load_names = sorted(loads_t.keys())

        header = ["hour"]
        header += [f"{n} (MW)" for n in gen_names]
        header += [f"{n} (MW)" for n in load_names]
        writer.writerow(header)

        # Determine number of hours from longest series.
        # Each entry is either a dict {"p": [...]} or a raw list.
        n_hours = 0
        for series in (*generators_t.values(), *loads_t.values()):
            values = series.get("p", series) if isinstance(series, dict) else series
            if isinstance(values, list) and len(values) > n_hours:
                n_hours = len(values)

        for h in range(n_hours):
            row: list[str | int | float] = [h]
            for name in gen_names:
                series = generators_t.get(name, {})
                values = series.get("p", series) if isinstance(series, dict) else series
                row.append(_fmt(values[h]) if isinstance(values, list) and h < len(values) else "")
            for name in load_names:
                series = loads_t.get(name, {})
                values = series.get("p", series) if isinstance(series, dict) else series
                row.append(_fmt(values[h]) if isinstance(values, list) and h < len(values) else "")
            writer.writerow(row)

        return buf.getvalue()

    # ── PDF ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def build_pdf(
        *,
        simulation_id: uuid.UUID,
        status: str,
        solver: str,
        total_supply_mwh: float | None,
        total_demand_mwh: float | None,
        balance_mwh: float | None,
        objective_value: float | None,
        result_json: dict | None,
        created_at: datetime,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> bytes:
        """Return PDF bytes with simulation metadata and KPI summary tables."""
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
        styles = getSampleStyleSheet()
        elements: list = []

        # ── Title ────────────────────────────────────────────────────────────────
        elements.append(Paragraph("PowerShift Simulation Report", styles["Title"]))
        elements.append(Spacer(1, 6 * mm))

        # ── Metadata table ───────────────────────────────────────────────────────
        meta_data = [
            ["Property", "Value"],
            ["Simulation ID", str(simulation_id)],
            ["Status", status],
            ["Solver", solver],
            ["Created at", str(created_at)],
        ]
        if start_date:
            meta_data.append(["Start date", str(start_date)])
        if end_date:
            meta_data.append(["End date", str(end_date)])

        meta_table = Table(meta_data, colWidths=[50 * mm, 110 * mm])
        meta_table.setStyle(_table_style())
        elements.append(Paragraph("Simulation Metadata", styles["Heading2"]))
        elements.append(Spacer(1, 3 * mm))
        elements.append(meta_table)
        elements.append(Spacer(1, 8 * mm))

        # ── KPI summary ─────────────────────────────────────────────────────────
        kpi_data = [
            ["KPI", "Value"],
            ["Total Supply (MWh)", _fmt(total_supply_mwh)],
            ["Total Demand (MWh)", _fmt(total_demand_mwh)],
            ["Balance (MWh)", _fmt(balance_mwh)],
            ["Objective Value", _fmt(objective_value)],
        ]
        kpi_table = Table(kpi_data, colWidths=[60 * mm, 60 * mm])
        kpi_table.setStyle(_table_style())
        elements.append(Paragraph("Key Performance Indicators", styles["Heading2"]))
        elements.append(Spacer(1, 3 * mm))
        elements.append(kpi_table)
        elements.append(Spacer(1, 8 * mm))

        # ── Capacity factors ─────────────────────────────────────────────────────
        capacity_factors: dict = (result_json or {}).get("capacity_factors", {})
        if capacity_factors:
            cf_data = [["Generator", "Capacity Factor"]]
            for name, value in sorted(capacity_factors.items()):
                cf_data.append([name, _fmt(value)])
            cf_table = Table(cf_data, colWidths=[80 * mm, 50 * mm])
            cf_table.setStyle(_table_style())
            elements.append(Paragraph("Capacity Factors", styles["Heading2"]))
            elements.append(Spacer(1, 3 * mm))
            elements.append(cf_table)
            elements.append(Spacer(1, 8 * mm))

        # ── Grid exchange summary ────────────────────────────────────────────────
        grid_exchange: dict = (result_json or {}).get("grid_exchange", {})
        ge_data = [["Metric", "Value"]]
        for key in ("total_import_mwh", "total_export_mwh"):
            value = grid_exchange.get(key)
            if value is not None:
                ge_data.append([key.replace("_", " ").title(), _fmt(value)])
        if len(ge_data) > 1:
            ge_table = Table(ge_data, colWidths=[80 * mm, 50 * mm])
            ge_table.setStyle(_table_style())
            elements.append(Paragraph("Grid Exchange", styles["Heading2"]))
            elements.append(Spacer(1, 3 * mm))
            elements.append(ge_table)

        doc.build(elements)
        return buf.getvalue()


# ── Helpers ──────────────────────────────────────────────────────────────────────


def _fmt(value: float | int | None) -> str:
    """Format a numeric value for display; return empty string for None."""
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecf0f1")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])
