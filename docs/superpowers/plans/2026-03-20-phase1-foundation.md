# Phase 1: Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all hardcoded athlete constants with a config table, fix the altitude/speed data gap on 2024+ rides, fix the VO2max equation, add a FastAPI layer with auth, and secure Garmin tokens.

**Architecture:** Single-row `athlete_config` table in SQLite replaces hardcoded constants in `db.py`. All library modules read from config. A re-ingestion script backfills `enhanced_altitude` and `enhanced_speed` for rides missing those fields. FastAPI wraps the existing library with bearer token auth. Garmin tokens move to macOS Keychain.

**Tech Stack:** Python 3, SQLite, FastAPI, uvicorn, defusedxml, keyring, pytest

**Spec:** `docs/superpowers/specs/2026-03-20-wko5-desktop-design.md` (Phase 1 section)

**Existing codebase:** `wko5/` package with 10 Python files, 58 passing tests. DB at `wko5/cycling_power.db`.

**Python env:** `/tmp/fitenv/`. Recreate: `rm -rf /tmp/fitenv && python3 -m venv /tmp/fitenv && source /tmp/fitenv/bin/activate && pip install numpy pandas scipy matplotlib fitdecode pytest fastapi uvicorn defusedxml keyring`

**Test command:** `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && pytest tests/ -v`

---

## Task 1: Create athlete_config table and config module

**Files:**
- Create: `wko5/config.py`
- Create: `tests/test_config.py`
- Modify: `wko5/db.py`

- [ ] **Step 1: Write tests for config.py**

```python
# tests/test_config.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wko5.config import get_config, set_config, init_config_table


def test_init_config_table():
    """Config table should be created with default values."""
    init_config_table()
    cfg = get_config()
    assert cfg is not None
    assert cfg["weight_kg"] == 78.0
    assert cfg["ftp_manual"] == 292
    assert cfg["bike_weight_kg"] == 9.0
    assert cfg["cda"] == 0.35
    assert cfg["crr"] == 0.005
    assert cfg["spike_threshold_watts"] == 2000


def test_get_config_returns_dict():
    cfg = get_config()
    assert isinstance(cfg, dict)
    assert "weight_kg" in cfg
    assert "pd_pmax_low" in cfg
    assert "ctl_time_constant" in cfg


def test_set_config():
    set_config("weight_kg", 80.0)
    cfg = get_config()
    assert cfg["weight_kg"] == 80.0
    # Reset
    set_config("weight_kg", 78.0)


def test_set_config_invalid_key():
    """Setting a non-existent key should raise ValueError."""
    try:
        set_config("nonexistent_key", 999)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wko5.config'`

- [ ] **Step 3: Implement config.py**

```python
# wko5/config.py
"""Athlete configuration — single-row config table replacing hardcoded constants."""

import logging
import sqlite3
from wko5.db import get_connection

logger = logging.getLogger(__name__)

# Default values for initial config row
DEFAULTS = {
    "name": "default",
    "sex": "male",
    "weight_kg": 78.0,
    "max_hr": 186,
    "lthr": None,
    "ftp_manual": 292,
    "bike_weight_kg": 9.0,
    "cda": 0.35,
    "crr": 0.005,
    "pd_pmax_low": 800,
    "pd_pmax_high": 2500,
    "pd_mftp_low": 150,
    "pd_mftp_high": 400,
    "pd_frc_low": 5,
    "pd_frc_high": 30,
    "pd_tau_low": 5,
    "pd_tau_high": 30,
    "pd_t0_low": 1,
    "pd_t0_high": 15,
    "spike_threshold_watts": 2000,
    "resting_hr_baseline": None,
    "hrv_baseline": None,
    "resting_hr_alert_delta": 5,
    "ctl_ramp_rate_yellow": 7,
    "ctl_ramp_rate_red": 10,
    "tsb_floor_alert": -30,
    "collapse_kj_threshold": None,
    "intensity_ceiling_if": 0.70,
    "fueling_rate_g_hr": 75,
    "energy_deficit_alert_kcal": 3000,
    "ctl_time_constant": 42,
    "atl_time_constant": 7,
}

_config_cache = None


def init_config_table():
    """Create the athlete_config table if it doesn't exist and insert defaults."""
    conn = get_connection()
    columns = ", ".join(f"{k} REAL" if isinstance(v, (int, float)) and v is not None
                        else f"{k} TEXT" if isinstance(v, str)
                        else f"{k} REAL"
                        for k, v in DEFAULTS.items())
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS athlete_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            {columns}
        )
    """)
    # Insert defaults only if table is empty
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM athlete_config")
    if cursor.fetchone()[0] == 0:
        cols = ", ".join(DEFAULTS.keys())
        placeholders = ", ".join("?" for _ in DEFAULTS)
        conn.execute(
            f"INSERT INTO athlete_config (id, {cols}) VALUES (1, {placeholders})",
            list(DEFAULTS.values()),
        )
    conn.commit()
    conn.close()
    global _config_cache
    _config_cache = None


def get_config():
    """Get the athlete config as a dict. Cached after first read."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache.copy()

    conn = get_connection()
    # Ensure table exists
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM athlete_config WHERE id = 1")
        row = cursor.fetchone()
        if row is None:
            conn.close()
            init_config_table()
            return get_config()
        columns = [desc[0] for desc in cursor.description]
        _config_cache = dict(zip(columns, row))
    except sqlite3.OperationalError:
        conn.close()
        init_config_table()
        return get_config()
    conn.close()
    return _config_cache.copy()


def set_config(key, value):
    """Set a single config value."""
    if key not in DEFAULTS and key != "id":
        raise ValueError(f"Unknown config key: {key}")
    conn = get_connection()
    init_config_table()  # ensure table exists
    conn.execute(f"UPDATE athlete_config SET {key} = ? WHERE id = 1", (value,))
    conn.commit()
    conn.close()
    global _config_cache
    _config_cache = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_config.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add wko5/config.py tests/test_config.py
git commit -m "feat: add athlete_config table and config module"
```

---

## Task 2: Refactor db.py to use config instead of hardcoded constants

**Files:**
- Modify: `wko5/db.py`
- Modify: `tests/test_db.py`

- [ ] **Step 1: Update db.py**

Replace the hardcoded constants with config lookups. Keep `WEIGHT_KG`, `FTP_DEFAULT` as module-level properties that read from config for backward compatibility:

```python
# wko5/db.py — updated top section
"""Core data layer — DB connection, common queries, athlete config."""

import logging
import os
import sqlite3

import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cycling_power.db")


def get_connection():
    """Return a SQLite connection to the cycling power database."""
    return sqlite3.connect(DB_PATH)


def _get_config_value(key):
    """Lazy config lookup — avoids circular import at module load time."""
    from wko5.config import get_config
    return get_config()[key]


# Backward-compatible accessors — read from config, not hardcoded
def _weight_kg():
    return _get_config_value("weight_kg")

def _ftp_default():
    return _get_config_value("ftp_manual")

# Module-level constants for backward compat (used by other modules importing these)
# These are now functions disguised as constants via property-like access
class _ConfigProxy:
    @property
    def WEIGHT_KG(self):
        return _get_config_value("weight_kg")
    @property
    def FTP_DEFAULT(self):
        return _get_config_value("ftp_manual")
    @property
    def FTP_RANGE(self):
        ftp = _get_config_value("ftp_manual")
        return (ftp - 7, ftp + 7)

_proxy = _ConfigProxy()

# Keep these as module-level for import compatibility
# Other modules do: from wko5.db import WEIGHT_KG, FTP_DEFAULT
# We can't make these dynamic without breaking imports, so we keep them
# as initial values and add a get_weight_kg() / get_ftp() function pair
WEIGHT_KG = 78.0  # DEPRECATED — use get_config()["weight_kg"]
FTP_RANGE = (285, 299)  # DEPRECATED
FTP_DEFAULT = 292  # DEPRECATED — use get_config()["ftp_manual"]
```

NOTE: The hardcoded constants stay for now as deprecated fallbacks — they're imported by 6 modules and 7 test files. Task 3 will migrate each module to use `get_config()` directly. This task just establishes the config system.

- [ ] **Step 2: Run all existing tests to verify nothing broke**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -v`
Expected: All 58 tests + 4 config tests PASS (62 total)

- [ ] **Step 3: Commit**

```bash
git add wko5/db.py tests/test_db.py
git commit -m "feat: add config-based accessors to db.py alongside deprecated constants"
```

---

## Task 3: Migrate all modules from hardcoded constants to config

**Files:**
- Modify: `wko5/pdcurve.py`
- Modify: `wko5/training_load.py`
- Modify: `wko5/zones.py`
- Modify: `wko5/ride.py`
- Modify: `wko5/profile.py`
- Modify: `wko5/clean.py`
- Modify: `wko5/__init__.py`

For each module, replace `from wko5.db import WEIGHT_KG, FTP_DEFAULT` with `from wko5.config import get_config` and read values at call time. This is mechanical — same pattern in each file.

- [ ] **Step 1: Migrate pdcurve.py**

Replace:
```python
from wko5.db import get_connection, get_activities, get_records, WEIGHT_KG, FTP_DEFAULT
```
With:
```python
from wko5.db import get_connection, get_activities, get_records
from wko5.config import get_config
```

Then in every function that uses `WEIGHT_KG`:
```python
cfg = get_config()
weight_kg = cfg["weight_kg"]
```

And for PD model bounds in `fit_pd_model()`:
```python
cfg = get_config()
bounds_low = [cfg["pd_pmax_low"], cfg["pd_tau_low"], cfg["pd_frc_low"], cfg["pd_t0_low"], cfg["pd_mftp_low"]]
bounds_high = [cfg["pd_pmax_high"], cfg["pd_tau_high"], cfg["pd_frc_high"], cfg["pd_t0_high"], cfg["pd_mftp_high"]]
```

- [ ] **Step 2: Migrate training_load.py**

Replace `FTP_DEFAULT` references with `get_config()["ftp_manual"]`. Replace CTL/ATL time constants:
```python
cfg = get_config()
ctl_decay = 1 - np.exp(-1 / cfg["ctl_time_constant"])
atl_decay = 1 - np.exp(-1 / cfg["atl_time_constant"])
```

- [ ] **Step 3: Migrate zones.py, ride.py, profile.py, clean.py**

Same pattern: replace imported constants with `get_config()` lookups. For `clean.py`, replace `SPIKE_THRESHOLD = 2000` with `get_config()["spike_threshold_watts"]`.

- [ ] **Step 4: Update __init__.py**

```python
# wko5/__init__.py
"""WKO5-style cycling power analysis library."""

from wko5.config import get_config, set_config, init_config_table
from wko5.db import get_connection, get_activities, get_records
from wko5.pdcurve import compute_envelope_mmp, fit_pd_model, rolling_ftp
from wko5.training_load import build_pmc, current_fitness, compute_np
from wko5.zones import coggan_zones, ilevels, time_in_zones
from wko5.ride import ride_summary, detect_intervals
from wko5.profile import power_profile, strengths_limiters, phenotype
```

- [ ] **Step 5: Run all tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -v`
Expected: All 62 tests PASS. The tests still use the deprecated constants for assertions but the modules now read from config (which has the same default values).

- [ ] **Step 6: Commit**

```bash
git add wko5/pdcurve.py wko5/training_load.py wko5/zones.py wko5/ride.py wko5/profile.py wko5/clean.py wko5/__init__.py
git commit -m "refactor: migrate all modules from hardcoded constants to athlete config"
```

---

## Task 4: Fix altitude and speed data gap for 2024+ rides

**Files:**
- Create: `wko5/backfill_altitude.py`

The issue: `ingest_missing.py` reads `altitude` and `speed` from FIT records, but newer Garmin files use `enhanced_altitude` and `enhanced_speed`. ~261 road rides (2024-2026) have NULL altitude.

- [ ] **Step 1: Write the backfill script**

```python
#!/usr/bin/env python3
"""Backfill altitude and speed for rides where enhanced_altitude/enhanced_speed exists in FIT files."""

import os
import sys
import gzip
import sqlite3
import io
import fitdecode

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cycling_power.db")
FIT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fit-files")


def safe_get(msg, field, default=None):
    try:
        val = msg.get_value(field)
        return val if val is not None else default
    except (KeyError, TypeError):
        return default


def backfill():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find activities with NULL altitude in records
    cursor.execute("""
        SELECT DISTINCT a.id, a.filename
        FROM activities a
        JOIN records r ON r.activity_id = a.id
        WHERE r.altitude IS NULL
        AND a.sub_sport != 'virtual_activity'
    """)
    candidates = cursor.fetchall()
    print(f"Found {len(candidates)} activities with missing altitude data")

    updated = 0
    for activity_id, filename in candidates:
        # Find the FIT file
        gz_path = os.path.join(FIT_DIR, filename + ".gz")
        fit_path = os.path.join(FIT_DIR, filename)

        if os.path.exists(gz_path):
            with gzip.open(gz_path, "rb") as f:
                data = f.read()
        elif os.path.exists(fit_path):
            with open(fit_path, "rb") as f:
                data = f.read()
        else:
            continue

        # Parse and collect enhanced fields
        records_data = []
        try:
            with fitdecode.FitReader(io.BytesIO(data)) as fit:
                for frame in fit:
                    if not isinstance(frame, fitdecode.FitDataMessage) or frame.name != "record":
                        continue
                    ts = str(safe_get(frame, "timestamp", ""))
                    alt = safe_get(frame, "enhanced_altitude") or safe_get(frame, "altitude")
                    spd = safe_get(frame, "enhanced_speed") or safe_get(frame, "speed")
                    if ts:
                        records_data.append((alt, spd, activity_id, ts))
        except Exception as e:
            print(f"  Error reading {filename}: {e}")
            continue

        if not records_data:
            continue

        # Update records
        conn.executemany(
            "UPDATE records SET altitude = ?, speed = ? WHERE activity_id = ? AND timestamp = ?",
            records_data,
        )
        conn.commit()

        # Verify
        cursor.execute(
            "SELECT COUNT(*) FROM records WHERE activity_id = ? AND altitude IS NOT NULL",
            (activity_id,),
        )
        alt_count = cursor.fetchone()[0]
        if alt_count > 0:
            updated += 1

        if updated % 50 == 0 and updated > 0:
            print(f"  Updated {updated} activities...")

    print(f"\nDone: {updated} activities backfilled with altitude/speed data")

    # Also invalidate MMP cache for these activities (altitude change doesn't affect MMP
    # but speed does, and we want clean data)

    conn.close()


if __name__ == "__main__":
    backfill()
```

- [ ] **Step 2: Run the backfill**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python wko5/backfill_altitude.py`
Expected: ~261 activities updated with altitude/speed data. May take several minutes.

- [ ] **Step 3: Verify the fix**

Run: `source /tmp/fitenv/bin/activate && python3 -c "
import sqlite3
conn = sqlite3.connect('wko5/cycling_power.db')
c = conn.cursor()
for year in ['2024', '2025', '2026']:
    c.execute('''SELECT COUNT(DISTINCT a.id) FROM activities a JOIN records r ON r.activity_id=a.id WHERE a.start_time LIKE ? AND a.sub_sport='road' AND r.altitude IS NOT NULL''', (f'{year}%',))
    print(f'{year} road rides with altitude: {c.fetchone()[0]}')
conn.close()
"`
Expected: All years show road rides with altitude data.

- [ ] **Step 4: Also fix the ingestion scripts for future rides**

Update `wko5/ingest_missing.py` line 90 and `wko5/garmin_sync.py` to read `enhanced_altitude` / `enhanced_speed` with fallback:

```python
"altitude": safe_get(frame, "enhanced_altitude") or safe_get(frame, "altitude"),
"speed": safe_get(frame, "enhanced_speed") or safe_get(frame, "speed"),
```

- [ ] **Step 5: Run all tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add wko5/backfill_altitude.py wko5/ingest_missing.py wko5/garmin_sync.py
git commit -m "fix: backfill altitude/speed from enhanced_altitude/enhanced_speed for 2024+ rides"
```

---

## Task 5: Fix VO2max equation

**Files:**
- Modify: `wko5/pdcurve.py`
- Modify: `tests/test_pdcurve.py`

The ACSM equation overestimates VO2 by 5-15% for trained cyclists (assumes 20-22% efficiency, trained cyclists are 22-25%). Replace with a trained-cyclist-specific approach: use power at ~5min from PD curve as proxy for VO2max power, then convert with 23% gross efficiency.

- [ ] **Step 1: Write the test**

Add to `tests/test_pdcurve.py`:

```python
def test_vo2max_trained_cyclist():
    """VO2max for a trained cyclist at ~290W FTP should be in 50-65 mL/min/kg range."""
    mmp = compute_envelope_mmp(days=365)
    if len(mmp) < 300:
        return
    result = fit_pd_model(mmp)
    if result is None:
        return
    # Trained cyclist at 3.7 W/kg should be ~50-65 mL/min/kg
    assert 40 < result["mVO2max_ml_min_kg"] < 75, \
        f"mVO2max={result['mVO2max_ml_min_kg']} outside trained cyclist range"
```

- [ ] **Step 2: Update fit_pd_model in pdcurve.py**

Replace the ACSM equation:
```python
# OLD: vo2max_ml_min = (mftp * 12.35) + (WEIGHT_KG * 3.5)
```

With trained-cyclist-specific approach:
```python
# VO2max estimation for trained cyclists
# Use power at ~5min (300s) from the MMP as proxy for VO2max power
# Then convert: VO2 (mL/min) = power_at_vo2max / (gross_efficiency * 1000/60)
# Gross efficiency for trained cyclists: 0.23 (22-25% range)
cfg = get_config()
weight_kg = cfg["weight_kg"]
if len(mmp) >= 300:
    p_vo2max = float(mmp[299])  # power at 5 min
else:
    p_vo2max = mftp * 1.15  # rough estimate: VO2max power ~115% of FTP

# VO2 (L/min) = power (W) / (efficiency * 1000/60)
# At 23% efficiency: VO2 = power / (0.23 * 16.667) = power / 3.833
gross_efficiency = 0.23
vo2max_L_min = p_vo2max / (gross_efficiency * 1000 / 60)
vo2max_ml_min = vo2max_L_min * 1000
vo2max_ml_min_kg = vo2max_ml_min / weight_kg
```

- [ ] **Step 3: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_pdcurve.py -v`
Expected: All tests PASS including the new one

- [ ] **Step 4: Commit**

```bash
git add wko5/pdcurve.py tests/test_pdcurve.py
git commit -m "fix: replace ACSM VO2max equation with trained-cyclist-specific estimation"
```

---

## Task 6: FastAPI skeleton with auth

**Files:**
- Create: `wko5/api/__init__.py`
- Create: `wko5/api/app.py`
- Create: `wko5/api/auth.py`
- Create: `wko5/api/routes.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write API tests**

```python
# tests/test_api.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from wko5.api.app import create_app


def _get_client():
    app = create_app(token="test-secret-token")
    return TestClient(app), "test-secret-token"


def test_health_no_auth():
    client, _ = _get_client()
    response = client.get("/api/health")
    assert response.status_code == 200


def test_fitness_requires_auth():
    client, _ = _get_client()
    response = client.get("/api/fitness")
    assert response.status_code == 401


def test_fitness_with_auth():
    client, token = _get_client()
    response = client.get("/api/fitness", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "CTL" in data
    assert "ATL" in data
    assert "TSB" in data


def test_activities_with_auth():
    client, token = _get_client()
    response = client.get("/api/activities?start=2025-01-01&end=2025-12-31",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_model_with_auth():
    client, token = _get_client()
    response = client.get("/api/model?days=90",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "mFTP" in data


def test_config_get():
    client, token = _get_client()
    response = client.get("/api/config", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "weight_kg" in data
    assert data["weight_kg"] == 78.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wko5.api'`

- [ ] **Step 3: Implement the API**

```python
# wko5/api/__init__.py
# (empty)

# wko5/api/auth.py
"""Bearer token authentication for the FastAPI server."""

from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

_token = None

def set_token(token: str):
    global _token
    _token = token

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if _token is None:
        return  # No auth configured
    if credentials is None or credentials.credentials != _token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

# wko5/api/routes.py
"""API route definitions."""

from fastapi import APIRouter, Depends, UploadFile, File
from wko5.api.auth import verify_token
from wko5.config import get_config
from wko5.training_load import current_fitness, build_pmc
from wko5.pdcurve import compute_envelope_mmp, fit_pd_model, rolling_ftp
from wko5.profile import power_profile, coggan_ranking, strengths_limiters, phenotype
from wko5.ride import ride_summary, detect_intervals, best_efforts, hr_decoupling, lap_analysis
from wko5.zones import coggan_zones, ilevels, ride_distribution
from wko5.db import get_activities, get_records

router = APIRouter(prefix="/api")

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/config", dependencies=[Depends(verify_token)])
def config():
    return get_config()

@router.get("/fitness", dependencies=[Depends(verify_token)])
def fitness():
    return current_fitness()

@router.get("/activities", dependencies=[Depends(verify_token)])
def activities(start: str = None, end: str = None, sub_sport: str = None):
    df = get_activities(start=start, end=end, sub_sport=sub_sport)
    return df.to_dict(orient="records")

@router.get("/model", dependencies=[Depends(verify_token)])
def model(days: int = 90):
    mmp = compute_envelope_mmp(days=days)
    if len(mmp) < 60:
        return {"error": "Insufficient data"}
    result = fit_pd_model(mmp)
    if result is None:
        return {"error": "Model fitting failed"}
    return result

@router.get("/profile", dependencies=[Depends(verify_token)])
def profile(days: int = 90):
    p = power_profile(days=days)
    if not p:
        return {"error": "Insufficient data"}
    ranking = coggan_ranking(p)
    sl = strengths_limiters(p)
    return {"profile": p, "ranking": ranking, "strengths_limiters": sl}

@router.get("/ride/{activity_id}", dependencies=[Depends(verify_token)])
def ride(activity_id: int):
    summary = ride_summary(activity_id)
    if not summary:
        return {"error": "Activity not found"}
    return summary

@router.get("/ride/{activity_id}/intervals", dependencies=[Depends(verify_token)])
def intervals(activity_id: int):
    return detect_intervals(activity_id)

@router.get("/ride/{activity_id}/efforts", dependencies=[Depends(verify_token)])
def efforts(activity_id: int):
    return best_efforts(activity_id)

@router.get("/rolling-ftp", dependencies=[Depends(verify_token)])
def rolling_ftp_endpoint(window: int = 90, step: int = 14):
    df = rolling_ftp(window_days=window, step_days=step)
    return df.to_dict(orient="records")

# wko5/api/app.py
"""FastAPI application factory."""

import secrets
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from wko5.api.auth import set_token
from wko5.api.routes import router


def create_app(token: str = None, allowed_origins: list = None):
    """Create the FastAPI application.

    Args:
        token: Bearer token for auth. If None, generates a random one.
        allowed_origins: CORS allowed origins. Defaults to localhost only.
    """
    if token is None:
        token = secrets.token_urlsafe(32)

    set_token(token)

    app = FastAPI(title="WKO5 Analyzer API")

    if allowed_origins is None:
        allowed_origins = ["http://localhost:*", "http://127.0.0.1:*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization"],
    )

    app.include_router(router)

    return app
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_api.py -v`
Expected: All 6 API tests PASS

- [ ] **Step 5: Run full test suite**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add wko5/api/ tests/test_api.py
git commit -m "feat: add FastAPI layer with bearer token auth and CORS"
```

---

## Task 7: Secure Garmin tokens

**Files:**
- Modify: `wko5/garmin_sync.py`

- [ ] **Step 1: Update garmin_sync.py to use keyring**

Replace the plaintext file token storage with macOS Keychain via `keyring`:

In `get_garmin_client()`, replace:
```python
os.makedirs(TOKEN_DIR, exist_ok=True)
client = Garmin()
try:
    client.login(tokenstore=TOKEN_DIR)
```

With:
```python
import keyring
import json

SERVICE_NAME = "wko5-garmin-connect"

# Try to load saved session from keychain
stored = keyring.get_password(SERVICE_NAME, "session")
if stored:
    try:
        # garminconnect uses tokenstore as a directory path
        # We store the token data in keychain but still need a temp dir for the library
        import tempfile
        token_dir = tempfile.mkdtemp()
        # Write the token from keychain to temp dir for garminconnect to read
        for fname, content in json.loads(stored).items():
            with open(os.path.join(token_dir, fname), "w") as f:
                f.write(content)
        client = Garmin()
        client.login(tokenstore=token_dir)
        print("Logged in with saved session from Keychain.")
    except Exception:
        stored = None

if not stored:
    email = input("Garmin email: ")
    password = getpass("Garmin password: ")
    client = Garmin(email=email, password=password, prompt_mfa=lambda: input("MFA code: "))
    token_dir = tempfile.mkdtemp()
    client.login(tokenstore=token_dir)
    # Save token files to keychain
    token_data = {}
    for fname in os.listdir(token_dir):
        with open(os.path.join(token_dir, fname)) as f:
            token_data[fname] = f.read()
    keyring.set_password(SERVICE_NAME, "session", json.dumps(token_data))
    print("Logged in and saved session to Keychain.")
```

- [ ] **Step 2: Remove old plaintext token directory if it exists**

Add a migration note at the top of garmin_sync.py:
```python
# Migration: if ~/.garmin_tokens/ exists, tokens have been moved to macOS Keychain.
# The old directory can be safely deleted.
```

- [ ] **Step 3: Commit**

```bash
git add wko5/garmin_sync.py
git commit -m "security: move Garmin tokens from plaintext files to macOS Keychain"
```

---

## Task 8: Create API launcher script

**Files:**
- Create: `run_api.py`

- [ ] **Step 1: Write the launcher**

```python
#!/usr/bin/env python3
"""Launch the WKO5 Analyzer API server."""

import secrets
import sys
import uvicorn
from wko5.api.app import create_app
from wko5.config import init_config_table

def main():
    init_config_table()
    token = secrets.token_urlsafe(32)
    app = create_app(token=token)

    # Find an available port
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    print(f"\n  WKO5 Analyzer API running at: http://127.0.0.1:{port}")
    print(f"  Auth token: {token}")
    print(f"\n  Example: curl -H 'Authorization: Bearer {token}' http://127.0.0.1:{port}/api/fitness\n")

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test it starts**

Run: `source /tmp/fitenv/bin/activate && timeout 5 python run_api.py || true`
Expected: Prints the URL and token, starts serving, then timeout kills it.

- [ ] **Step 3: Run full test suite one final time**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit and push**

```bash
git add run_api.py
git commit -m "feat: add API launcher with ephemeral port and token display"
git push origin main
```
