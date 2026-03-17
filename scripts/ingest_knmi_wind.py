"""KNMI 10-minute wind data ingestion — Actuele10mindataKNMIstations → PostgreSQL.

Downloads NetCDF files from the KNMI Open Data API, extracts observations for a
target station (default: 280 / Groningen Eelde), and bulk-inserts them into the
``wind_measurement`` table on Neon.

Usage:
    python scripts/ingest_knmi_wind.py --months 6 --station 280

Prerequisites:
    pip install netCDF4 requests
    Set KNMI_API_KEY and DATABASE_URL in your .env file (or pass via CLI).

This script is designed to be run **once** to backfill history.  Re-running is
safe (idempotent) because the table has a UNIQUE(station_code, timestamp)
constraint and inserts use ON CONFLICT DO NOTHING.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
_log = logging.getLogger("knmi_ingest")

# ── Constants ─────────────────────────────────────────────────────────────────

_KNMI_BASE = "https://api.dataplatform.knmi.nl/open-data/v1"
_DATASET   = "Actuele10mindataKNMIstations"
_VERSION   = "2"
_LIST_URL  = f"{_KNMI_BASE}/datasets/{_DATASET}/versions/{_VERSION}/files"

# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest KNMI 10-min wind data into PostgreSQL.")
    p.add_argument("--months",        type=int,   default=6,     help="Months of history to fetch (default: 6)")
    p.add_argument("--station",       type=str,   default="06280", help="KNMI station code (default: 06280 = Eelde)")
    p.add_argument("--batch-size",    type=int,   default=500,   help="DB insert batch size (default: 500)")
    p.add_argument("--api-key",       type=str,   default=None,  help="KNMI API key (or set KNMI_API_KEY env var)")
    p.add_argument("--database-url",  type=str,   default=None,  help="PostgreSQL URL (or set DATABASE_URL env var)")
    p.add_argument("--delay",         type=float, default=0.05,  help="Seconds to wait between file downloads (default: 0.05)")
    p.add_argument("--dry-run",       action="store_true",       help="List files to download without actually inserting")
    return p.parse_args()


# ── KNMI HTTP helpers ─────────────────────────────────────────────────────────

def _knmi_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": api_key}


def _list_files(api_key: str, params: dict) -> dict:
    """Fetch one page of the KNMI file listing."""
    r = requests.get(_LIST_URL, headers=_knmi_headers(api_key), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _get_download_url(api_key: str, filename: str) -> str:
    """Resolve the temporary download URL for a single file."""
    url = f"{_LIST_URL}/{filename}/url"
    for attempt in range(4):
        try:
            r = requests.get(url, headers=_knmi_headers(api_key), timeout=30)
            if r.status_code == 429:
                wait = 2 ** attempt
                _log.warning("Rate limited; waiting %ds before retry…", wait)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()["temporaryDownloadUrl"]
        except requests.RequestException as exc:
            if attempt == 3:
                raise
            _log.warning("Download-URL fetch failed (%s); retrying…", exc)
            time.sleep(1)
    raise RuntimeError(f"Could not get download URL for {filename}")


def _download_file(download_url: str, dest: Path) -> None:
    """Stream a file from a temporary download URL to disk."""
    for attempt in range(4):
        try:
            with requests.get(download_url, stream=True, timeout=60) as r:
                if r.status_code == 429:
                    wait = 2 ** attempt
                    time.sleep(wait)
                    continue
                r.raise_for_status()
                with open(dest, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=65_536):
                        fh.write(chunk)
            return
        except requests.RequestException as exc:
            if attempt == 3:
                raise
            _log.warning("Download failed (%s); retrying…", exc)
            time.sleep(1)


# ── NetCDF parsing ────────────────────────────────────────────────────────────

def _safe_float(val) -> Optional[float]:  # type: ignore[return]
    """Convert a netCDF4 masked/scalar value to float or None."""
    try:
        import numpy as np  # noqa: PLC0415
        if val is None:
            return None
        if hasattr(val, "mask") and np.ma.is_masked(val):
            return None
        f = float(val)
        if f != f:  # NaN
            return None
        return f
    except (TypeError, ValueError):
        return None


def _parse_nc_file(
    nc_path: Path,
    target_station: str,
) -> list[dict]:
    """Extract measurements for target_station from a KNMI NetCDF file.

    Returns a list of dicts matching the wind_measurement table columns.
    Returns an empty list if the station is not found or data is missing.
    """
    import netCDF4 as nc  # noqa: PLC0415
    import numpy as np    # noqa: PLC0415

    rows: list[dict] = []
    try:
        with nc.Dataset(nc_path, "r") as ds:
            # ── Find station index ────────────────────────────────────────────
            station_var = ds.variables.get("station") or ds.variables.get("STN")
            if station_var is None:
                _log.debug("No 'station' variable in %s", nc_path.name)
                return rows

            raw_stations = station_var[:]
            # Stations may be stored as bytes, ints, or strings
            station_idx: Optional[int] = None
            for i, s in enumerate(raw_stations):
                # Handle numpy bytes, str, or masked array
                try:
                    decoded = (
                        s.tobytes().decode("utf-8").strip("\x00").strip()
                        if isinstance(s, (bytes, np.bytes_))
                        else str(int(s)).strip()
                        if hasattr(s, "item")
                        else str(s).strip()
                    )
                except Exception:
                    decoded = str(s).strip()
                if decoded == target_station:
                    station_idx = i
                    break

            if station_idx is None:
                _log.debug("Station %s not found in %s", target_station, nc_path.name)
                return rows

            # ── Station metadata ──────────────────────────────────────────────
            station_name = target_station
            for name_var in ("stationname", "STNAME", "name"):
                if name_var in ds.variables:
                    try:
                        raw = ds.variables[name_var][station_idx]
                        station_name = (
                            raw.tobytes().decode("utf-8").strip("\x00").strip()
                            if isinstance(raw, (bytes, np.bytes_))
                            else str(raw).strip()
                        )
                    except Exception:
                        pass
                    break

            lat = _safe_float(ds.variables["lat"][station_idx]) if "lat" in ds.variables else None
            lon = _safe_float(ds.variables["lon"][station_idx]) if "lon" in ds.variables else None

            # ── Timestamps ───────────────────────────────────────────────────
            time_var = ds.variables["time"]
            times = nc.num2date(
                time_var[:],
                units=time_var.units,
                calendar=getattr(time_var, "calendar", "standard"),
            )

            # ── Measurement variables ─────────────────────────────────────────
            def _get(vname: str, idx: int, t_idx: int) -> Optional[float]:
                if vname not in ds.variables:
                    return None
                v = ds.variables[vname]
                # Shape can be (time,) or (time, station) or (station, time)
                shape = v.shape
                try:
                    if len(shape) == 1:
                        return _safe_float(v[t_idx])
                    elif shape == (len(raw_stations), len(times)):
                        return _safe_float(v[idx, t_idx])
                    else:
                        return _safe_float(v[t_idx, idx])
                except (IndexError, Exception):
                    return None

            for t_idx, cftime_obj in enumerate(times):
                # Convert cftime → Python datetime (UTC)
                try:
                    ts = datetime(
                        cftime_obj.year, cftime_obj.month, cftime_obj.day,
                        cftime_obj.hour, cftime_obj.minute, cftime_obj.second,
                        tzinfo=timezone.utc,
                    )
                except Exception:
                    continue

                rows.append({
                    "station_code": target_station,
                    "station_name": station_name,
                    "timestamp": ts,
                    "wind_speed_ms": _get("ff", station_idx, t_idx),
                    "wind_direction_deg": _get("dd", station_idx, t_idx),
                    "temperature_c": _get("ta", station_idx, t_idx),
                    "air_pressure_hpa": _get("pp", station_idx, t_idx),
                    "latitude": lat,
                    "longitude": lon,
                })
    except Exception as exc:
        _log.warning("Failed to parse %s: %s", nc_path.name, exc)

    return rows


# ── DB helpers ────────────────────────────────────────────────────────────────

def _build_db_url(raw_url: str) -> str:
    """Convert any PostgreSQL URL to asyncpg-compatible format."""
    url = raw_url
    # Strip NeonDB params incompatible with asyncpg
    for param in ("channel_binding=require", "sslmode=require"):
        url = url.replace(f"&{param}", "").replace(f"?{param}&", "?").replace(f"?{param}", "")
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


async def _get_latest_ts(db_url: str, station_code: str) -> Optional[datetime]:
    """Check the DB for the most recent measurement timestamp for this station."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: PLC0415
    from sqlalchemy import text  # noqa: PLC0415
    engine = create_async_engine(db_url, connect_args={"ssl": "require"}, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT MAX(timestamp) FROM wind_measurement WHERE station_code = :s"
                ),
                {"s": station_code},
            )
            row = result.fetchone()
            val = row[0] if row else None
            if val is not None and val.tzinfo is None:
                val = val.replace(tzinfo=timezone.utc)
            return val
    except Exception as exc:
        _log.warning("Could not check latest timestamp (table may not exist yet): %s", exc)
        return None
    finally:
        await engine.dispose()


async def _create_table_if_needed(db_url: str) -> None:
    """Ensure wind_measurement table and its index/constraint exist."""
    from sqlalchemy.ext.asyncio import create_async_engine  # noqa: PLC0415
    from sqlmodel import SQLModel  # noqa: PLC0415
    # Import all ORM models so metadata is complete
    from app.infrastructure.db.models.asset_parameters_model import AssetParametersModel  # noqa: F401, PLC0415
    from app.infrastructure.wind.models import WindMeasurementORM  # noqa: F401, PLC0415

    engine = create_async_engine(db_url, connect_args={"ssl": "require"}, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        _log.info("Tables verified / created.")
    finally:
        await engine.dispose()


async def _bulk_insert(db_url: str, rows: list[dict]) -> int:
    """Insert a batch of rows with ON CONFLICT DO NOTHING.  Returns rows inserted."""
    if not rows:
        return 0
    from uuid import uuid4  # noqa: PLC0415
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: PLC0415
    from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: PLC0415
    from app.infrastructure.wind.models import WindMeasurementORM  # noqa: PLC0415

    # Attach UUIDs
    for r in rows:
        r["id"] = uuid4()

    engine = create_async_engine(db_url, connect_args={"ssl": "require"}, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    inserted = 0
    try:
        async with factory() as session:
            stmt = (
                pg_insert(WindMeasurementORM)
                .values(rows)
                .on_conflict_do_nothing(constraint="uq_wind_measurement_station_ts")
            )
            result = await session.execute(stmt)
            await session.commit()
            inserted = result.rowcount if result.rowcount >= 0 else 0
    finally:
        await engine.dispose()
    return inserted


# ── Main ingestion loop ───────────────────────────────────────────────────────

def _filename_to_dt(filename: str) -> Optional[datetime]:
    """Try to extract a UTC datetime from the KNMI filename.

    KNMI 10-min files are typically named like:
        KNMI_202501150000.nc  or  KNMI_20250115_0000.nc
    We extract 12 digits (YYYYMMDDHHmm) from the name.
    """
    import re  # noqa: PLC0415
    m = re.search(r"(\d{12})", filename.replace("_", ""))
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def main() -> None:
    args = _parse_args()

    # ── Resolve credentials ───────────────────────────────────────────────────
    api_key = args.api_key or os.environ.get("KNMI_API_KEY", "")
    raw_db  = args.database_url or os.environ.get("DATABASE_URL", "")

    if not api_key:
        _log.error(
            "No KNMI API key found.  Set KNMI_API_KEY in your .env or pass --api-key."
        )
        sys.exit(1)
    if not raw_db:
        _log.error(
            "No DATABASE_URL found.  Set DATABASE_URL in your .env or pass --database-url."
        )
        sys.exit(1)

    db_url = _build_db_url(raw_db)
    station = args.station
    batch_size = args.batch_size
    delay = args.delay
    dry_run = args.dry_run

    if dry_run:
        _log.info("DRY RUN mode — no data will be downloaded or inserted.")

    # ── Ensure table exists ───────────────────────────────────────────────────
    if not dry_run:
        asyncio.run(_create_table_if_needed(db_url))

    # ── Determine fetch window ────────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=args.months * 30)

    if not dry_run:
        latest = asyncio.run(_get_latest_ts(db_url, station))
        if latest is not None and latest > window_start:
            _log.info(
                "Resuming from %s (latest in DB: %s)",
                latest.isoformat(), latest.isoformat(),
            )
            window_start = latest
        else:
            _log.info("Starting fresh from %s", window_start.isoformat())
    else:
        _log.info("Dry-run window: %s → %s", window_start.isoformat(), now.isoformat())

    # ── Paginate KNMI file listing ────────────────────────────────────────────
    # Use startAfterFilename alone (API rejects mixing it with orderBy/sorting).
    # Files are returned in ascending chronological order from window_start.
    _start_fname = f"KMDS__OPER_P___10M_OBS_L2_{window_start.strftime('%Y%m%d%H%M')}.nc"
    all_filenames: list[str] = []
    done = False

    _log.info("Fetching file listing from KNMI…")
    page_num = 0
    next_start: str = _start_fname
    while not done:
        page_num += 1
        try:
            resp = _list_files(api_key, {"maxKeys": 100, "startAfterFilename": next_start})
        except requests.HTTPError as exc:
            _log.error("KNMI list_files error: %s", exc)
            sys.exit(1)

        files = resp.get("files", [])
        if not files:
            break

        for f in files:
            fname = f.get("filename", "")
            file_dt = _filename_to_dt(fname)
            if file_dt is not None and file_dt > now:
                done = True
                break
            all_filenames.append(fname)

        if page_num % 10 == 0:
            _log.info("  Listing page %d — %d files collected so far…", page_num, len(all_filenames))

        if not resp.get("isTruncated", False):
            break
        next_start = files[-1]["filename"]

    _log.info("Found %d files to process.", len(all_filenames))

    if dry_run:
        for i, fn in enumerate(all_filenames[:20], 1):
            print(f"  [{i:4d}] {fn}")
        if len(all_filenames) > 20:
            print(f"  … and {len(all_filenames) - 20} more")
        return

    # ── Download, parse, insert ───────────────────────────────────────────────
    total_files     = len(all_filenames)
    total_inserted  = 0
    total_skipped   = 0
    total_errors    = 0
    batch_buffer: list[dict] = []
    t_start = time.monotonic()

    with tempfile.TemporaryDirectory() as tmpdir:
        for file_idx, filename in enumerate(all_filenames, 1):
            # Progress log every 100 files
            if file_idx % 100 == 0 or file_idx == 1:
                elapsed = time.monotonic() - t_start
                rate = file_idx / elapsed if elapsed > 0 else 0
                eta_s  = (total_files - file_idx) / rate if rate > 0 else 0
                _log.info(
                    "[%d/%d] inserted=%d skipped=%d  rate=%.1f f/s  ETA≈%.0fs",
                    file_idx, total_files, total_inserted, total_skipped, rate, eta_s,
                )

            nc_path = Path(tmpdir) / filename
            try:
                dl_url = _get_download_url(api_key, filename)
                _download_file(dl_url, nc_path)
            except Exception as exc:
                _log.warning("Skip %s — download error: %s", filename, exc)
                total_errors += 1
                continue

            rows = _parse_nc_file(nc_path, station)
            nc_path.unlink(missing_ok=True)

            if not rows:
                continue

            batch_buffer.extend(rows)

            if len(batch_buffer) >= batch_size:
                n = asyncio.run(_bulk_insert(db_url, batch_buffer))
                total_inserted += n
                total_skipped  += len(batch_buffer) - n
                batch_buffer.clear()

            if delay > 0:
                time.sleep(delay)

        # Flush remaining buffer
        if batch_buffer:
            n = asyncio.run(_bulk_insert(db_url, batch_buffer))
            total_inserted += n
            total_skipped  += len(batch_buffer) - n
            batch_buffer.clear()

    elapsed = time.monotonic() - t_start
    _log.info(
        "Done in %.0fs.  Files: %d processed / %d errors.  "
        "Rows: %d inserted / %d skipped (duplicates).",
        elapsed, total_files - total_errors, total_errors,
        total_inserted, total_skipped,
    )


if __name__ == "__main__":
    # Load .env automatically so DATABASE_URL and KNMI_API_KEY are available
    _env_file = Path(__file__).parent.parent / ".env"
    if _env_file.exists():
        from dotenv import load_dotenv  # type: ignore[import-untyped]
        load_dotenv(_env_file)
    main()
