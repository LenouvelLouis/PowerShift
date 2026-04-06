"""KNMI 2025 weather profile ingestion — Actuele10mindataKNMIstations → weather_profile.

Downloads 10-min NetCDF files from the KNMI Open Data API, groups them into
30-min slots, aggregates observations for Groningen Eelde (station 06280),
and bulk-inserts the result into the ``weather_profile`` table on Neon.

Aggregation rules per 30-min slot (3 consecutive 10-min files):
    wind_speed_ms    → mean of ff
    wind_dir_deg     → circular mean of dd  (via unit-vector decomposition)
    wind_gust_ms     → max  of fx
    temperature_c    → mean of ta
    air_pressure_hpa → mean of pp
    humidity_pct     → mean of rh
    radiation_wm2    → mean of qg
    sunshine_min     → sum  of ss  (max 30 min)

Usage:
    python scripts/ingest_weather_profile.py --year 2025
    python scripts/ingest_weather_profile.py --year 2025 --dry-run
    python scripts/ingest_weather_profile.py --year 2025 --start-month 1 --end-month 3

Prerequisites:
    pip install netCDF4 numpy requests sqlalchemy sqlmodel asyncpg python-dotenv
    Set KNMI_API_KEY and DATABASE_URL in your .env file.

Idempotent: uses ON CONFLICT DO NOTHING on the timestamp PK.
Resumes automatically from the latest timestamp already in DB.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
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
_log = logging.getLogger("ingest_weather_profile")


def _log_separator(char: str = "─", width: int = 70) -> None:
    _log.info(char * width)


def _log_section(title: str) -> None:
    _log_separator()
    _log.info("  %s", title)
    _log_separator()


def _wait_with_spinner(seconds: int, reason: str) -> None:
    """Wait with a small terminal animation so long retries stay visible."""
    spinner = ["|", "/", "-", "\\"]
    end_time = time.monotonic() + seconds
    tick = 0
    while True:
        remaining = max(0, int(round(end_time - time.monotonic())))
        if remaining <= 0:
            sys.stderr.write(f"\r{reason}... retrying now{' ' * 20}\n")
            sys.stderr.flush()
            return
        frame = spinner[tick % len(spinner)]
        sys.stderr.write(
            f"\r{reason}... retry in {remaining:>3}s {frame}"
            + " " * 20
        )
        sys.stderr.flush()
        time.sleep(1)
        tick += 1


def _is_forbidden_response(exc: Exception | None, response=None) -> bool:
    if response is not None and getattr(response, "status_code", None) == 403:
        return True
    if exc is None:
        return False
    response = getattr(exc, "response", None)
    return getattr(response, "status_code", None) == 403


def _is_temporary_rate_limit(response=None, exc: Exception | None = None) -> bool:
    if response is not None and getattr(response, "status_code", None) == 429:
        return True
    if exc is None:
        return False
    response = getattr(exc, "response", None)
    return getattr(response, "status_code", None) == 429

# ── Constants ─────────────────────────────────────────────────────────────────

_KNMI_BASE    = "https://api.dataplatform.knmi.nl/open-data/v1"
_DATASET      = "Actuele10mindataKNMIstations"
_VERSION      = "2"
_LIST_URL     = f"{_KNMI_BASE}/datasets/{_DATASET}/versions/{_VERSION}/files"
_STATION      = "06280"   # Groningen Eelde
_STATION_NAME = "Groningen Eelde"

# Downloaded NC files are kept in this directory so they can be reused on
# subsequent runs without re-downloading. Use --clear-cache to delete them.
_CACHE_DIR = Path(__file__).parent.parent / ".knmi_cache"

# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest KNMI 2025 weather data into weather_profile.")
    p.add_argument("--year",         type=int, default=2025, help="Year to ingest (default: 2025)")
    p.add_argument("--start-month",  type=int, default=1,    help="First month to ingest (default: 1)")
    p.add_argument("--end-month",    type=int, default=12,   help="Last month to ingest inclusive (default: 12)")
    p.add_argument("--batch-size",   type=int, default=200,  help="DB insert batch size (default: 200)")
    p.add_argument("--workers",      type=int, default=6,    help="Minimum download worker count (phase 1 uses max(30, workers))")
    p.add_argument("--api-key",      type=str, default=None, help="KNMI API key (or KNMI_API_KEY env var)")
    p.add_argument("--database-url", type=str, default=None, help="PostgreSQL URL (or DATABASE_URL env var)")
    p.add_argument("--dry-run",      action="store_true",    help="List files without downloading or inserting")
    p.add_argument("--no-resume",    action="store_true",    help="Ignore the latest timestamp in DB and ingest the full requested window")
    p.add_argument("--clear-cache",  action="store_true",    help=f"Delete all cached NC files in {_CACHE_DIR} and exit")
    return p.parse_args()


# ── KNMI HTTP helpers ─────────────────────────────────────────────────────────

def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": api_key}


def _get_download_url(api_key: str, filename: str) -> str:
    url = f"{_LIST_URL}/{filename}/url"
    while True:
        try:
            r = requests.get(url, headers=_headers(api_key), timeout=30)
            if r.status_code == 403:
                _log.warning("403 Forbidden while resolving %s; retrying in 5 minutes…", filename)
                _wait_with_spinner(300, f"KNMI 403 on {filename}")
                continue
            if r.status_code == 429:
                _log.warning("429 Too Many Requests while resolving %s; retrying in 5 minutes…", filename)
                time.sleep(300)
                continue
            r.raise_for_status()
            return r.json()["temporaryDownloadUrl"]
        except requests.RequestException as exc:
            if _is_forbidden_response(exc):
                _log.warning("403 Forbidden while resolving %s; retrying in 5 minutes…", filename)
                _wait_with_spinner(300, f"KNMI 403 on {filename}")
                continue
            if _is_temporary_rate_limit(exc=exc):
                _log.warning("429 Too Many Requests while resolving %s; retrying in 5 minutes…", filename)
                time.sleep(300)
                continue
            raise
    raise RuntimeError(f"Could not get download URL for {filename}")


def _download_file(download_url: str, dest: Path) -> None:
    while True:
        try:
            with requests.get(download_url, stream=True, timeout=60) as r:
                if r.status_code == 403:
                    _log.warning("403 Forbidden while downloading %s; retrying in 5 minutes…", dest.name)
                    _wait_with_spinner(300, f"KNMI 403 on {dest.name}")
                    continue
                if r.status_code == 429:
                    _log.warning("429 Too Many Requests while downloading %s; retrying in 5 minutes…", dest.name)
                    time.sleep(300)
                    continue
                r.raise_for_status()
                with open(dest, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=65_536):
                        fh.write(chunk)
            return
        except requests.RequestException as exc:
            if _is_forbidden_response(exc):
                _log.warning("403 Forbidden while downloading %s; retrying in 5 minutes…", dest.name)
                _wait_with_spinner(300, f"KNMI 403 on {dest.name}")
                continue
            if _is_temporary_rate_limit(exc=exc):
                _log.warning("429 Too Many Requests while downloading %s; retrying in 5 minutes…", dest.name)
                time.sleep(300)
                continue
            raise


def _fetch_file(api_key: str, filename: str, dest: Path) -> None:
    """Resolve download URL and stream file to disk."""
    dl_url = _get_download_url(api_key, filename)
    _download_file(dl_url, dest)


# ── File listing ──────────────────────────────────────────────────────────────

def _list_files_for_window(
    api_key: str,
    start: datetime,
    end: datetime,
) -> list[str]:
    """Return all filenames between start (inclusive) and end (exclusive)."""
    # KNMI filename format: KMDS__OPER_P___10M_OBS_L2_YYYYMMDDHHmm.nc
    start_fname = f"KMDS__OPER_P___10M_OBS_L2_{start.strftime('%Y%m%d%H%M')}.nc"
    end_fname   = f"KMDS__OPER_P___10M_OBS_L2_{end.strftime('%Y%m%d%H%M')}.nc"

    filenames: list[str] = []
    next_start = start_fname
    while True:
        r = requests.get(
            _LIST_URL,
            headers=_headers(api_key),
            params={"maxKeys": 500, "startAfterFilename": next_start},
            timeout=30,
        )
        if r.status_code == 403:
            _log.warning("403 Forbidden while listing KNMI files; retrying in 5 minutes…")
            _wait_with_spinner(300, "KNMI 403 on file listing")
            continue
        if r.status_code == 429:
            _log.warning("429 Too Many Requests while listing KNMI files; retrying in 5 minutes…")
            time.sleep(300)
            continue
        r.raise_for_status()
        data = r.json()
        files = data.get("files", [])
        if not files:
            break
        for f in files:
            fname = f.get("filename", "")
            if fname >= end_fname:
                return filenames
            filenames.append(fname)
        if not data.get("isTruncated", False):
            break
        next_start = files[-1]["filename"]
    return filenames


# ── NetCDF parsing ────────────────────────────────────────────────────────────

def _safe_float(val) -> Optional[float]:  # type: ignore[return]
    try:
        import numpy as np  # noqa: PLC0415
        if val is None:
            return None
        if hasattr(val, "mask") and np.ma.is_masked(val):
            return None
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _find_station_idx(ds, target: str) -> Optional[int]:
    """Return the index of target station in the NetCDF station dimension."""
    import numpy as np  # noqa: PLC0415

    station_var = ds.variables.get("station") or ds.variables.get("STN")
    if station_var is None:
        return None
    for i, s in enumerate(station_var[:]):
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
        if decoded == target:
            return i
    return None


def _get_var(ds, vname: str, st_idx: int, t_idx: int) -> Optional[float]:
    if vname not in ds.variables:
        return None
    v = ds.variables[vname]
    shape = v.shape
    try:
        if len(shape) == 1:
            return _safe_float(v[st_idx])
        # Each 10-min file has 1 time step and ~50-70 stations.
        # Shape is always (n_stations, 1) → larger dim is stations (first axis).
        if shape[0] >= shape[1]:      # (station, time)
            return _safe_float(v[st_idx, t_idx])
        else:                          # (time, station)
            return _safe_float(v[t_idx, st_idx])
    except (IndexError, Exception):
        return None


def _parse_nc(nc_path: Path, station: str) -> Optional[dict[str, Optional[float]]]:
    """Parse a single 10-min NC file and return the raw observation for `station`.

    Returns None if the station is not found or the file cannot be parsed.
    Returns a dict with keys: ff, dd, fx, ta, pp, rh, qg, ss.
    """
    import netCDF4 as nc  # noqa: PLC0415

    try:
        with nc.Dataset(nc_path, "r") as ds:
            st_idx = _find_station_idx(ds, station)
            if st_idx is None:
                return None
            # Each 10-min file has exactly one time step
            t_idx = 0
            return {
                "ff": _get_var(ds, "ff",  st_idx, t_idx),
                "dd": _get_var(ds, "dd",  st_idx, t_idx),
                "fx": _get_var(ds, "fx",  st_idx, t_idx),
                "ta": _get_var(ds, "ta",  st_idx, t_idx),
                "pp": _get_var(ds, "pp",  st_idx, t_idx),
                "rh": _get_var(ds, "rh",  st_idx, t_idx),
                "qg": _get_var(ds, "qg",  st_idx, t_idx),
                "ss": _get_var(ds, "ss",  st_idx, t_idx),
            }
    except Exception as exc:
        _log.debug("Parse error %s: %s", nc_path.name, exc)
        return None


# ── Aggregation ───────────────────────────────────────────────────────────────

def _mean(values: list[float]) -> Optional[float]:
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None


def _circular_mean_deg(angles_deg: list[Optional[float]]) -> Optional[float]:
    """Compute circular mean of wind directions in degrees."""
    clean = [a for a in angles_deg if a is not None]
    if not clean:
        return None
    sin_sum = sum(math.sin(math.radians(a)) for a in clean)
    cos_sum = sum(math.cos(math.radians(a)) for a in clean)
    result = math.degrees(math.atan2(sin_sum, cos_sum))
    return result % 360.0


def _aggregate_triplet(
    obs: list[Optional[dict]],
    slot_ts: datetime,
) -> Optional[dict]:
    """Aggregate 3 × 10-min observations into one 30-min slot row.

    Returns None if no valid observations are found.
    """
    valid = [o for o in obs if o is not None]
    if not valid:
        return None

    ffs  = [o["ff"] for o in valid if o["ff"] is not None]
    dds  = [o["dd"] for o in valid if o["dd"] is not None]
    fxs  = [o["fx"] for o in valid if o["fx"] is not None]
    tas  = [o["ta"] for o in valid if o["ta"] is not None]
    pps  = [o["pp"] for o in valid if o["pp"] is not None]
    rhs  = [o["rh"] for o in valid if o["rh"] is not None]
    qgs  = [o["qg"] for o in valid if o["qg"] is not None]
    sss  = [o["ss"] for o in valid if o["ss"] is not None]

    return {
        "timestamp":        slot_ts,
        "wind_speed_ms":    _mean(ffs),
        "wind_dir_deg":     _circular_mean_deg(dds),
        "wind_gust_ms":     max(fxs) if fxs else None,
        "temperature_c":    _mean(tas),
        "air_pressure_hpa": _mean(pps),
        "humidity_pct":     _mean(rhs),
        "radiation_wm2":    _mean(qgs),
        "sunshine_min":     sum(sss) if sss else None,
    }


# ── DB helpers ────────────────────────────────────────────────────────────────

def _build_db_url(raw_url: str) -> str:
    url = raw_url
    for param in ("channel_binding=require", "sslmode=require"):
        url = url.replace(f"&{param}", "").replace(f"?{param}&", "?").replace(f"?{param}", "")
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


async def _create_table(db_url: str) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine  # noqa: PLC0415
    from sqlmodel import SQLModel  # noqa: PLC0415
    # Import all models so metadata is populated
    from app.infrastructure.db.models.weather_profile_model import WeatherProfileModel  # noqa: F401, PLC0415

    engine = create_async_engine(db_url, connect_args={"ssl": "require"}, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        _log.info("Table weather_profile verified / created.")
    finally:
        await engine.dispose()


async def _get_latest_ts(db_url: str) -> Optional[datetime]:
    from sqlalchemy import text  # noqa: PLC0415
    from sqlalchemy.ext.asyncio import create_async_engine  # noqa: PLC0415

    engine = create_async_engine(db_url, connect_args={"ssl": "require"}, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT MAX(timestamp) FROM weather_profile"))
            row = result.fetchone()
            val = row[0] if row else None
            if val is not None and val.tzinfo is None:
                val = val.replace(tzinfo=timezone.utc)
            return val
    except Exception as exc:
        _log.warning("Could not query latest timestamp: %s", exc)
        return None
    finally:
        await engine.dispose()


async def _bulk_insert_batched(db_url: str, rows: list[dict], batch_size: int) -> tuple[int, int]:
    """Insert rows in batches while reusing a single async engine and pool."""
    if not rows:
        return 0, 0

    from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: PLC0415
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: PLC0415
    from app.infrastructure.db.models.weather_profile_model import WeatherProfileModel  # noqa: PLC0415

    engine = create_async_engine(db_url, connect_args={"ssl": "require"}, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    total_inserted = 0
    total_skipped = 0
    try:
        for offset in range(0, len(rows), batch_size):
            chunk = rows[offset: offset + batch_size]
            async with factory() as session:
                stmt = (
                    pg_insert(WeatherProfileModel)
                    .values(chunk)
                    .on_conflict_do_nothing(index_elements=["timestamp"])
                )
                result = await session.execute(stmt)
                await session.commit()
                inserted = result.rowcount if result.rowcount >= 0 else 0
                total_inserted += inserted
                total_skipped += len(chunk) - inserted
    finally:
        await engine.dispose()

    return total_inserted, total_skipped


# ── 30-min slot helpers ───────────────────────────────────────────────────────

def _slot_timestamp(fname: str) -> Optional[datetime]:
    """Derive the 30-min slot end-timestamp from a KNMI filename.

    Filenames follow the pattern: …_YYYYMMDDHHNN.nc
    Files :00, :10, :20 → slot ends at :30
    Files :30, :40, :50 → slot ends at :00 of the next hour
    """
    import re  # noqa: PLC0415
    # Anchor the pattern to the underscore before the timestamp and .nc suffix
    # to avoid bleeding digits from the rest of the filename (e.g. "L2" → "2...")
    m = re.search(r"_(\d{12})\.nc$", fname)
    if not m:
        return None
    try:
        dt = datetime.strptime(m.group(1), "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    minute = dt.minute
    if minute < 30:
        return dt.replace(minute=30, second=0, microsecond=0)
    else:
        return (dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))


def _group_into_slots(filenames: list[str]) -> list[tuple[datetime, list[str]]]:
    """Group filenames into 30-min slots.

    Each slot contains exactly 3 consecutive 10-min files.
    Returns list of (slot_timestamp, [f1, f2, f3]).
    """
    # Sort chronologically (filenames already are, but be safe)
    sorted_fnames = sorted(filenames)
    groups: dict[datetime, list[str]] = {}
    for fname in sorted_fnames:
        slot_ts = _slot_timestamp(fname)
        if slot_ts is None:
            continue
        groups.setdefault(slot_ts, []).append(fname)

    # Return only complete groups (3 files per slot)
    result = []
    for ts in sorted(groups.keys()):
        fnames = groups[ts]
        if len(fnames) == 3:
            result.append((ts, fnames))
        else:
            _log.debug("Incomplete slot %s (%d files) — skipping", ts.isoformat(), len(fnames))
    return result


# ── Download only (used in thread pool — no netCDF parsing here) ─────────────
# netCDF4 / HDF5 is NOT thread-safe: parsing must happen in the main thread.

def _download_to_disk(
    api_key: str,
    filename: str,
    cache_dir: Path,
) -> Optional[Path]:
    """Download a single NC file to cache_dir. Returns the path, or None on error.

    If the file already exists in cache (from a previous run), it is reused
    without re-downloading.
    """
    nc_path = cache_dir / filename
    if nc_path.exists():
        _log.debug("Cache hit: %s", filename)
        return nc_path
    try:
        _fetch_file(api_key, filename, nc_path)
        return nc_path
    except Exception as exc:
        _log.debug("Download failed %s: %s", filename, exc)
        return None


def _parse_slot_worker(
    slot_ts: datetime,
    path_strs: list[Optional[str]],
    station: str,
) -> tuple[datetime, Optional[dict]]:
    """Parse the 3 files of a slot in a separate process.

    Using processes avoids netCDF4/HDF5 thread-safety limitations.
    """
    obs_list: list[Optional[dict]] = []
    for path_str in path_strs:
        if not path_str:
            obs_list.append(None)
            continue
        obs_list.append(_parse_nc(Path(path_str), station))

    return slot_ts, _aggregate_triplet(obs_list, slot_ts)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = _parse_args()

    api_key = args.api_key or os.environ.get("KNMI_API_KEY", "")
    raw_db  = args.database_url or os.environ.get("DATABASE_URL", "")

    if not api_key:
        _log.error("No KNMI API key. Set KNMI_API_KEY in .env or pass --api-key.")
        sys.exit(1)
    if not raw_db and not args.dry_run:
        _log.error("No DATABASE_URL. Set DATABASE_URL in .env or pass --database-url.")
        sys.exit(1)

    db_url = _build_db_url(raw_db) if raw_db else ""

    year        = args.year
    start_month = args.start_month
    end_month   = args.end_month
    batch_size  = args.batch_size
    workers     = args.workers
    dry_run     = args.dry_run

    # ── Clear cache ───────────────────────────────────────────────────────────
    if args.clear_cache:
        if _CACHE_DIR.exists():
            files = list(_CACHE_DIR.glob("*.nc"))
            total_mb = sum(f.stat().st_size for f in files) / 1_048_576
            _log.info(
                "Deleting %d cached NC files (%.1f MB) from %s…",
                len(files), total_mb, _CACHE_DIR,
            )
            for f in files:
                f.unlink()
            _CACHE_DIR.rmdir()
            _log.info("Cache cleared.")
        else:
            _log.info("Cache directory %s does not exist — nothing to clear.", _CACHE_DIR)
        return

    # ── Ensure cache directory exists ─────────────────────────────────────────
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached_count = len(list(_CACHE_DIR.glob("*.nc")))

    # ── Startup banner ────────────────────────────────────────────────────────
    _log_section("KNMI Weather Profile Ingestion")
    _log.info("  Station   : %s — %s", _STATION, _STATION_NAME)
    _log.info("  Year      : %d", year)
    _log.info("  Months    : %d → %d", start_month, end_month)
    _log.info("  Batch size: %d slots", batch_size)
    _log.info("  Workers   : %d (phase 1 downloads with max(30, workers))", workers)
    _log.info("  Cache dir : %s (%d files already cached)", _CACHE_DIR, cached_count)
    _log.info("  Mode      : %s", "DRY RUN" if dry_run else "LIVE")
    _log_separator()

    # ── Create table ──────────────────────────────────────────────────────────
    if not dry_run:
        _log.info("Verifying / creating weather_profile table…")
        asyncio.run(_create_table(db_url))

    # ── Determine resume point ────────────────────────────────────────────────
    resume_from: Optional[datetime] = None
    if not dry_run and not args.no_resume:
        _log.info("Checking latest timestamp already in DB…")
        resume_from = asyncio.run(_get_latest_ts(db_url))
        if resume_from:
            _log.info("  Latest row in DB : %s  → resuming from there", resume_from.isoformat())
        else:
            _log.info("  DB is empty — starting from scratch")
    elif args.no_resume:
        _log.info("  --no-resume: skipping resume check, ingesting full requested window")

    # ── Build time windows ────────────────────────────────────────────────────
    window_start = datetime(year, start_month, 1, 0, 0, tzinfo=timezone.utc)
    if end_month == 12:
        window_end = datetime(year + 1, 1, 1, 0, 0, tzinfo=timezone.utc)
    else:
        window_end = datetime(year, end_month + 1, 1, 0, 0, tzinfo=timezone.utc)

    if resume_from is not None and resume_from > window_start:
        window_start = resume_from
        _log.info("  Window adjusted  : %s → %s", window_start.isoformat(), window_end.isoformat())
    else:
        _log.info("  Window           : %s → %s", window_start.isoformat(), window_end.isoformat())

    # ── List files ────────────────────────────────────────────────────────────
    _log_section("Step 1 — Listing KNMI files")
    _log.info("Paginating KNMI file listing (this may take a moment)…")
    t_list = time.monotonic()
    all_filenames = _list_files_for_window(api_key, window_start, window_end)
    _log.info(
        "Found %d 10-min files  (%.1fs)",
        len(all_filenames), time.monotonic() - t_list,
    )
    if all_filenames:
        _log.info("  First file : %s", all_filenames[0])
        _log.info("  Last file  : %s", all_filenames[-1])

    # ── Group into 30-min slots ───────────────────────────────────────────────
    _log_section("Step 2 — Grouping into 30-min slots")
    slots = _group_into_slots(all_filenames)
    total_slots = len(slots)
    incomplete = len(all_filenames) - total_slots * 3  # files not in complete triplets
    _log.info("30-min slots       : %d", total_slots)
    _log.info("Expected rows in DB: %d", total_slots)
    if incomplete:
        _log.warning("  %d file(s) could not form a complete triplet — skipped", incomplete)

    if dry_run:
        _log.info("")
        _log.info("DRY RUN — first 10 slots:")
        for ts, fnames in slots[:10]:
            _log.info("  %s  ←  %s", ts.strftime("%Y-%m-%d %H:%M UTC"), " | ".join(fnames))
        if total_slots > 10:
            _log.info("  … and %d more slots", total_slots - 10)
        _log_separator()
        _log.info("DRY RUN complete. No data was inserted.")
        return

    # ── Download, parse, aggregate, insert ────────────────────────────────────
    _log_section("Step 3 — Download / Parse / Aggregate / Insert")
    _log.info("Processing %d slots with two-phase parallelism…", total_slots)
    _log.info("")

    total_inserted = 0
    total_skipped  = 0
    total_errors   = 0
    t_start = time.monotonic()

    # Phase 1 — submit all downloads at once for much higher concurrency.
    download_workers = max(30, workers)
    unique_filenames = sorted({fname for _, fnames in slots for fname in fnames})
    _log.info("Phase 1/3 — downloading %d unique files with %d workers…", len(unique_filenames), download_workers)
    downloaded_paths: dict[str, Optional[Path]] = {}
    with ThreadPoolExecutor(max_workers=download_workers) as dl_executor:
        dl_futures = {
            dl_executor.submit(_download_to_disk, api_key, fname, _CACHE_DIR): fname
            for fname in unique_filenames
        }
        completed = 0
        for future in as_completed(dl_futures):
            fname = dl_futures[future]
            completed += 1
            try:
                downloaded_paths[fname] = future.result()
            except Exception as exc:
                _log.debug("Worker error (download %s): %s", fname, exc)
                downloaded_paths[fname] = None

            if completed % 500 == 0 or completed == len(unique_filenames):
                pct = completed / len(unique_filenames) * 100 if unique_filenames else 100.0
                _log.info("  Downloads: %d/%d (%.1f%%)", completed, len(unique_filenames), pct)

    failed_downloads = sum(1 for p in downloaded_paths.values() if p is None)
    if failed_downloads:
        total_errors += failed_downloads
        _log.warning("%d files failed to download and will be treated as missing observations.", failed_downloads)

    # Phase 2 — parse all slots in parallel across processes.
    parse_workers = max(1, os.cpu_count() or 1)
    _log.info("Phase 2/3 — parsing %d slots with %d processes…", total_slots, parse_workers)
    parsed_rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=parse_workers) as parse_executor:
        parse_futures = {
            parse_executor.submit(
                _parse_slot_worker,
                slot_ts,
                [str(downloaded_paths.get(fname)) if downloaded_paths.get(fname) else None for fname in fnames],
                _STATION,
            ): slot_ts
            for slot_ts, fnames in slots
        }

        for idx, future in enumerate(as_completed(parse_futures), 1):
            slot_ts = parse_futures[future]
            try:
                _, row = future.result()
            except Exception as exc:
                total_errors += 1
                _log.debug("Parse worker failed for slot %s: %s", slot_ts.isoformat(), exc)
                continue

            if row is None:
                total_errors += 1
                continue

            _log.debug(
                "  %s  ff=%.1f  dd=%.0f°  ta=%.1f°C  qg=%.0fW/m²  ss=%.0fmin",
                slot_ts.strftime("%Y-%m-%d %H:%M"),
                row["wind_speed_ms"] or 0.0,
                row["wind_dir_deg"] or 0.0,
                row["temperature_c"] or 0.0,
                row["radiation_wm2"] or 0.0,
                row["sunshine_min"] or 0.0,
            )
            parsed_rows.append(row)

            if idx % 500 == 0 or idx == total_slots:
                elapsed = time.monotonic() - t_start
                rate = idx / elapsed if elapsed > 0 else 0
                eta_s = (total_slots - idx) / rate if rate > 0 else 0
                pct = idx / total_slots * 100 if total_slots else 100.0
                _log.info(
                    "  Parse: %5d/%d (%.1f%%)  valid=%d  errors=%d  rate=%.1f slot/s  ETA≈%dm%02ds",
                    idx,
                    total_slots,
                    pct,
                    len(parsed_rows),
                    total_errors,
                    rate,
                    int(eta_s) // 60,
                    int(eta_s) % 60,
                )

    # Keep deterministic insertion order.
    parsed_rows.sort(key=lambda row: row["timestamp"])

    # Phase 3 — insert by batch while reusing a single async engine.
    _log.info("Phase 3/3 — inserting %d rows by batches of %d…", len(parsed_rows), batch_size)
    total_inserted, total_skipped = asyncio.run(_bulk_insert_batched(db_url, parsed_rows, batch_size))

    cached_final = len(list(_CACHE_DIR.glob("*.nc")))
    cached_mb    = sum(f.stat().st_size for f in _CACHE_DIR.glob("*.nc")) / 1_048_576
    _log.info("  Cache      : %d NC files on disk (%.0f MB) — run --clear-cache to delete",
              cached_final, cached_mb)

    # ── Final summary ─────────────────────────────────────────────────────────
    elapsed = time.monotonic() - t_start
    _log_section("Summary")
    _log.info("  Total time     : %dm %02ds", int(elapsed) // 60, int(elapsed) % 60)
    _log.info("  Slots processed: %d / %d  (%d errors)",
              total_slots - total_errors, total_slots, total_errors)
    _log.info("  Rows inserted  : %d", total_inserted)
    _log.info("  Rows skipped   : %d  (already in DB)", total_skipped)
    if total_slots > 0:
        _log.info("  Coverage       : %.1f%%", total_inserted / total_slots * 100)
    _log_separator()


if __name__ == "__main__":
    _env_file = Path(__file__).parent.parent / ".env"
    if _env_file.exists():
        from dotenv import load_dotenv  # type: ignore[import-untyped]
        load_dotenv(_env_file)
    main()
