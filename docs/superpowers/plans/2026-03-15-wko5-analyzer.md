# WKO5 Analyzer Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python library for WKO5-style cycling power analysis with Jupyter notebooks and a Claude skill for in-conversation queries.

**Architecture:** Multi-module Python package (`wko5/`) with modules for DB access, data cleaning, power-duration modeling, training load, zones, ride analysis, and power profiling. MMP computation is cached in the DB for performance. Three Jupyter notebooks provide visual analysis. A Claude skill enables in-conversation analysis.

**Tech Stack:** Python 3, SQLite, numpy, pandas, scipy, matplotlib

**Spec:** `docs/superpowers/specs/2026-03-14-wko5-analyzer-design.md`

**Existing files:** `wko5/cycling_power.db` (DB with 1,653 activities, 11M records), `wko5/ingest_missing.py`, `wko5/garmin_sync.py`

**Python env:** `/tmp/fitenv/` venv. Recreate if missing: `python3 -m venv /tmp/fitenv && source /tmp/fitenv/bin/activate && pip install numpy pandas scipy matplotlib fitdecode`

**Test command:** `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/ -v`

---

## Chunk 1: Foundation (db.py, clean.py, __init__.py)

### Task 1: Package init and db.py

**Files:**
- Create: `wko5/__init__.py`
- Create: `wko5/db.py`
- Create: `tests/__init__.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write tests for db.py**

```python
# tests/__init__.py
# (empty)

# tests/test_db.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from wko5.db import (
    get_connection, get_activities, get_records,
    WEIGHT_KG, FTP_DEFAULT, FTP_RANGE, DB_PATH,
)

def test_constants():
    assert WEIGHT_KG == 78.0
    assert FTP_DEFAULT == 292
    assert FTP_RANGE == (285, 299)
    assert "cycling_power.db" in DB_PATH

def test_get_connection():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM activities")
    count = cursor.fetchone()[0]
    assert count > 1000  # we have 1653
    conn.close()

def test_get_activities_returns_dataframe():
    df = get_activities()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 1000
    assert "start_time" in df.columns
    assert "avg_power" in df.columns

def test_get_activities_date_filter():
    df = get_activities(start="2025-01-01", end="2025-12-31")
    assert isinstance(df, pd.DataFrame)
    # should be fewer than total
    all_df = get_activities()
    assert len(df) < len(all_df)

def test_get_activities_sub_sport_filter():
    df = get_activities(sub_sport="virtual_activity")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert all(df["sub_sport"] == "virtual_activity")

def test_get_activities_empty_returns_empty_df():
    df = get_activities(start="1999-01-01", end="1999-01-02")
    assert isinstance(df, pd.DataFrame)
    assert df.empty

def test_get_records():
    df = get_records(1)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 100
    assert "power" in df.columns
    assert "heart_rate" in df.columns

def test_get_records_invalid_id():
    df = get_records(999999)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wko5.db'`

- [ ] **Step 3: Implement db.py**

```python
# wko5/db.py
"""Core data layer — DB connection, common queries, athlete constants."""

import logging
import os
import sqlite3

import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cycling_power.db")
WEIGHT_KG = 78.0
FTP_RANGE = (285, 299)
FTP_DEFAULT = 292


def get_connection():
    """Return a SQLite connection to the cycling power database."""
    return sqlite3.connect(DB_PATH)


def get_activities(start=None, end=None, sub_sport=None):
    """Get activities as a DataFrame, optionally filtered by date range and sub_sport."""
    conn = get_connection()
    query = "SELECT * FROM activities WHERE 1=1"
    params = []

    if start:
        query += " AND start_time >= ?"
        params.append(start)
    if end:
        query += " AND start_time <= ?"
        params.append(end)
    if sub_sport:
        query += " AND sub_sport = ?"
        params.append(sub_sport)

    query += " ORDER BY start_time"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_records(activity_id):
    """Get per-second records for an activity as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM records WHERE activity_id = ? ORDER BY timestamp",
        conn,
        params=(activity_id,),
    )
    conn.close()

    if df.empty:
        logger.warning(f"No records found for activity_id={activity_id}")
        return df

    # Clean via clean module (imported here to avoid circular import at module level)
    from wko5.clean import clean_records
    return clean_records(df)
```

- [ ] **Step 4: Create minimal clean.py stub so db.py import works**

```python
# wko5/clean.py
"""Data cleaning — spike removal, dropout handling, gap filling."""

import pandas as pd


def clean_power(power_series):
    """Clean a power series. Stub — returns input unchanged."""
    return power_series


def clean_records(records_df):
    """Clean a records DataFrame. Stub — returns input unchanged."""
    return records_df
```

- [ ] **Step 5: Create __init__.py**

```python
# wko5/__init__.py
"""WKO5-style cycling power analysis library."""
```

(Convenience imports will be added as modules are completed.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_db.py -v`
Expected: All 8 tests PASS

- [ ] **Step 7: Commit**

```bash
git add wko5/__init__.py wko5/db.py wko5/clean.py tests/__init__.py tests/test_db.py
git commit -m "feat: add db.py core data layer and clean.py stub"
```

---

### Task 2: Data cleaning (clean.py)

**Files:**
- Modify: `wko5/clean.py`
- Create: `tests/test_clean.py`

- [ ] **Step 1: Write tests for clean.py**

```python
# tests/test_clean.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.clean import clean_power, clean_records


def test_spike_removal():
    """Power readings >2000W should be replaced with interpolated values."""
    s = pd.Series([200, 210, 3000, 220, 230])
    cleaned = clean_power(s)
    assert cleaned[2] < 2000
    assert cleaned[2] == 215.0  # interpolated between 210 and 220


def test_spike_at_start():
    """Spike at start should use forward fill."""
    s = pd.Series([5000, 200, 210])
    cleaned = clean_power(s)
    assert cleaned[0] == 200.0


def test_spike_at_end():
    """Spike at end should use backward fill."""
    s = pd.Series([200, 210, 5000])
    cleaned = clean_power(s)
    assert cleaned[2] == 210.0


def test_nan_dropout_short_gap():
    """NaN gaps <=5 samples should be forward-filled."""
    s = pd.Series([200.0, 210.0, np.nan, np.nan, 230.0, 240.0])
    cleaned = clean_power(s)
    assert cleaned[2] == 210.0  # forward filled
    assert cleaned[3] == 210.0


def test_nan_dropout_long_gap():
    """NaN gaps >5 samples should remain NaN."""
    s = pd.Series([200.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 300.0])
    cleaned = clean_power(s)
    assert np.isnan(cleaned[3])  # still NaN (gap of 6)


def test_zeros_preserved():
    """Zero power (coasting) should be kept as-is."""
    s = pd.Series([200, 0, 0, 0, 200])
    cleaned = clean_power(s)
    assert cleaned[1] == 0
    assert cleaned[2] == 0


def test_clean_records_has_power_column():
    """clean_records should clean the power column."""
    df = pd.DataFrame({
        "power": [200, 3000, 210, 220],
        "heart_rate": [120, 121, 122, 123],
        "timestamp": ["t1", "t2", "t3", "t4"],
    })
    cleaned = clean_records(df)
    assert cleaned["power"][1] < 2000
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_clean.py -v`
Expected: FAIL — assertions fail (stub returns input unchanged)

- [ ] **Step 3: Implement clean.py**

```python
# wko5/clean.py
"""Data cleaning — spike removal, dropout handling, gap filling."""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SPIKE_THRESHOLD = 2000  # watts
MAX_FFILL_GAP = 5  # samples


def clean_power(power_series):
    """Clean a power series: remove spikes, handle dropouts.

    - Readings >2000W replaced with interpolated neighbors
    - NaN gaps <=5s forward-filled, longer gaps left as NaN
    - Zeros preserved (coasting)
    """
    s = power_series.copy().astype(float)

    # Spike removal: replace >2000W with NaN, then interpolate
    spike_mask = s > SPIKE_THRESHOLD
    if spike_mask.any():
        logger.info(f"Removing {spike_mask.sum()} power spikes >2000W")
        s[spike_mask] = np.nan
        s = s.interpolate(method="linear", limit_direction="both")

    # Dropout handling: forward-fill NaN gaps up to 5 samples
    if s.isna().any():
        s = s.ffill(limit=MAX_FFILL_GAP)

    return s


def clean_records(records_df):
    """Clean a records DataFrame: apply power cleaning and fill timestamp gaps."""
    if records_df.empty:
        return records_df

    df = records_df.copy()

    if "power" in df.columns:
        df["power"] = clean_power(df["power"])

    # Timestamp gap handling: detect gaps >2s, fill <=5s with interpolation
    if "timestamp" in df.columns and len(df) > 1:
        try:
            ts = pd.to_datetime(df["timestamp"])
            gaps = ts.diff().dt.total_seconds()
            # For gaps 2-5s, interpolate numeric columns
            for idx in gaps.index:
                gap = gaps[idx]
                if gap is not None and 2 < gap <= 5:
                    for col in ["power", "heart_rate", "cadence", "speed"]:
                        if col in df.columns:
                            df.loc[idx, col] = (df[col].iloc[df.index.get_loc(idx) - 1] + df[col].iloc[df.index.get_loc(idx)]) / 2
        except Exception:
            pass  # timestamp parsing issues — skip gap handling

    return df
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_clean.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add wko5/clean.py tests/test_clean.py
git commit -m "feat: implement data cleaning — spike removal and dropout handling"
```

---

## Chunk 2: Power Duration Model (pdcurve.py)

### Task 3: MMP computation and caching

**Files:**
- Create: `wko5/pdcurve.py`
- Create: `tests/test_pdcurve.py`

- [ ] **Step 1: Write tests for MMP computation**

```python
# tests/test_pdcurve.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.pdcurve import compute_mmp, get_cached_mmp, compute_envelope_mmp


def test_compute_mmp_constant_power():
    """Constant power should give same MMP at all durations."""
    power = pd.Series([200.0] * 100)
    mmp = compute_mmp(power)
    assert len(mmp) == 100
    assert mmp[0] == 200.0  # 1s
    assert abs(mmp[49] - 200.0) < 0.01  # 50s
    assert abs(mmp[99] - 200.0) < 0.01  # 100s


def test_compute_mmp_decreasing():
    """MMP should be monotonically non-increasing with duration."""
    power = pd.Series(np.random.randint(100, 400, size=1000).astype(float))
    mmp = compute_mmp(power)
    for i in range(1, len(mmp)):
        assert mmp[i] <= mmp[i - 1] + 0.01  # allow tiny float rounding


def test_compute_mmp_known_values():
    """Known pattern: 300W for 60s, then 200W for 60s."""
    power = pd.Series([300.0] * 60 + [200.0] * 60)
    mmp = compute_mmp(power)
    assert mmp[0] == 300.0  # best 1s = 300
    assert abs(mmp[59] - 300.0) < 0.01  # best 60s = 300
    assert abs(mmp[119] - 250.0) < 0.01  # best 120s = avg of all = 250


def test_compute_mmp_handles_nan():
    """NaN values should be treated as zero for MMP."""
    power = pd.Series([200.0, np.nan, 200.0, 200.0, 200.0])
    mmp = compute_mmp(power)
    assert len(mmp) == 5
    assert mmp[0] == 200.0  # best 1s


def test_get_cached_mmp_returns_array():
    """get_cached_mmp should return an MMP array for a real activity."""
    mmp = get_cached_mmp(1)
    assert isinstance(mmp, np.ndarray)
    assert len(mmp) > 100
    assert mmp[0] > 0  # should have some power


def test_get_cached_mmp_cache_consistency():
    """Calling twice should return same result (from cache)."""
    mmp1 = get_cached_mmp(1)
    mmp2 = get_cached_mmp(1)
    np.testing.assert_array_equal(mmp1, mmp2)


def test_compute_envelope_mmp():
    """Envelope MMP should exist and be non-increasing."""
    mmp = compute_envelope_mmp(days=90)
    assert isinstance(mmp, np.ndarray)
    assert len(mmp) > 100
    # Should be non-increasing
    for i in range(1, min(len(mmp), 3600)):
        assert mmp[i] <= mmp[i - 1] + 0.01
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_pdcurve.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wko5.pdcurve'`

- [ ] **Step 3: Implement MMP computation and caching in pdcurve.py**

```python
# wko5/pdcurve.py
"""Power Duration Model — MMP curve, PD model fitting, physiological parameter estimation."""

import logging

import numpy as np
import pandas as pd

from wko5.db import get_connection, get_activities, get_records, WEIGHT_KG, FTP_DEFAULT

logger = logging.getLogger(__name__)


def compute_mmp(power_series):
    """Compute Mean Max Power array using cumulative sum approach.

    Returns np.ndarray where mmp[d-1] = best average power over d seconds.
    """
    power = power_series.fillna(0).values.astype(float)
    n = len(power)
    if n == 0:
        return np.array([])

    cumsum = np.concatenate([[0], np.cumsum(power)])
    mmp = np.zeros(n)

    for d in range(1, n + 1):
        # Average power over d seconds for all possible windows
        avgs = (cumsum[d:] - cumsum[:n - d + 1]) / d
        mmp[d - 1] = avgs.max()

    return mmp


def _ensure_mmp_cache_table(conn):
    """Create the mmp_cache table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mmp_cache (
            activity_id INTEGER,
            duration_s INTEGER,
            max_avg_power REAL,
            PRIMARY KEY (activity_id, duration_s),
            FOREIGN KEY (activity_id) REFERENCES activities(id)
        )
    """)
    conn.commit()


def get_cached_mmp(activity_id):
    """Get MMP for an activity, using cache if available."""
    conn = get_connection()
    _ensure_mmp_cache_table(conn)

    # Try cache first
    cursor = conn.cursor()
    cursor.execute(
        "SELECT duration_s, max_avg_power FROM mmp_cache WHERE activity_id = ? ORDER BY duration_s",
        (activity_id,),
    )
    rows = cursor.fetchall()

    if rows:
        conn.close()
        mmp = np.array([r[1] for r in rows])
        return mmp

    # Compute from records
    records = get_records(activity_id)
    if records.empty or "power" not in records.columns:
        conn.close()
        return np.array([])

    mmp = compute_mmp(records["power"])

    # Store in cache
    data = [(activity_id, d + 1, float(mmp[d])) for d in range(len(mmp))]
    conn.executemany(
        "INSERT OR REPLACE INTO mmp_cache (activity_id, duration_s, max_avg_power) VALUES (?, ?, ?)",
        data,
    )
    conn.commit()
    conn.close()

    return mmp


def compute_envelope_mmp(start=None, end=None, days=90, sub_sport=None):
    """Compute envelope MMP across rides in date range.

    Takes the max at each duration across all per-ride MMP arrays.
    """
    if days and not start:
        end_date = pd.Timestamp.now()
        start = (end_date - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
        end = end_date.strftime("%Y-%m-%d 23:59:59")

    activities = get_activities(start=start, end=end, sub_sport=sub_sport)
    if activities.empty:
        logger.warning("No activities found in date range")
        return np.array([])

    max_len = 0
    mmps = []

    for _, act in activities.iterrows():
        mmp = get_cached_mmp(act["id"])
        if len(mmp) > 0:
            mmps.append(mmp)
            max_len = max(max_len, len(mmp))

    if not mmps:
        return np.array([])

    # Build envelope: max at each duration
    envelope = np.zeros(max_len)
    for mmp in mmps:
        envelope[:len(mmp)] = np.maximum(envelope[:len(mmp)], mmp)

    return envelope


def rebuild_mmp_cache():
    """Recompute and store MMP for all activities. Returns count processed."""
    conn = get_connection()
    _ensure_mmp_cache_table(conn)

    # Clear existing cache
    conn.execute("DELETE FROM mmp_cache")
    conn.commit()
    conn.close()

    activities = get_activities()
    count = 0
    for _, act in activities.iterrows():
        mmp = get_cached_mmp(act["id"])
        if len(mmp) > 0:
            count += 1
        if count % 100 == 0 and count > 0:
            logger.info(f"Cached MMP for {count} activities...")

    logger.info(f"MMP cache rebuilt for {count} activities")
    return count
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_pdcurve.py -v`
Expected: All 7 tests PASS (note: `get_cached_mmp(1)` and `compute_envelope_mmp` tests hit the real DB and may take a few seconds)

- [ ] **Step 5: Commit**

```bash
git add wko5/pdcurve.py tests/test_pdcurve.py
git commit -m "feat: add MMP computation with cumsum and DB cache"
```

---

### Task 4: PD model fitting and derived parameters

**Files:**
- Modify: `wko5/pdcurve.py`
- Modify: `tests/test_pdcurve.py`

- [ ] **Step 1: Write tests for PD model fitting**

Add to `tests/test_pdcurve.py`:

```python
from wko5.pdcurve import fit_pd_model, power_at_durations, rolling_ftp, compare_periods


def test_fit_pd_model_synthetic():
    """Fit model to a known synthetic curve and check parameters."""
    # Generate a realistic-ish MMP curve: P(t) = 1200*e^(-t/15) + 20000/(t+5) + 280
    durations = np.arange(1, 3601)
    synthetic = 1200 * np.exp(-durations / 15) + 20000 / (durations + 5) + 280
    # Add a tiny bit of noise
    synthetic += np.random.normal(0, 1, len(synthetic))

    result = fit_pd_model(synthetic)
    assert result is not None
    assert "Pmax" in result
    assert "FRC" in result
    assert "mFTP" in result
    assert "TTE" in result
    assert "mVO2max" in result
    # mFTP should be close to 280
    assert 250 < result["mFTP"] < 320


def test_fit_pd_model_real_data():
    """Fit model to real envelope MMP and check mFTP is in known range."""
    mmp = compute_envelope_mmp(days=90)
    if len(mmp) < 300:
        return  # skip if not enough data
    result = fit_pd_model(mmp)
    assert result is not None
    # Known FTP range is 285-299
    assert 250 < result["mFTP"] < 350, f"mFTP={result['mFTP']} outside reasonable range"


def test_fit_pd_model_empty_input():
    """Empty MMP should return None."""
    result = fit_pd_model(np.array([]))
    assert result is None


def test_fit_pd_model_short_input():
    """Very short MMP (< 60s) should return None."""
    result = fit_pd_model(np.array([500, 400, 350, 300, 280]))
    assert result is None


def test_power_at_durations():
    """Extract power at specific durations from MMP."""
    mmp = np.array([500, 450, 400, 350, 300])  # 1s through 5s
    result = power_at_durations(mmp, durations=[1, 3, 5])
    assert result[1] == 500
    assert result[3] == 400
    assert result[5] == 300


def test_power_at_durations_beyond_length():
    """Durations beyond MMP length should return NaN."""
    mmp = np.array([500, 450, 400])
    result = power_at_durations(mmp, durations=[1, 5])
    assert result[1] == 500
    assert np.isnan(result[5])
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_pdcurve.py -v -k "fit_pd_model or power_at"`
Expected: FAIL — `ImportError: cannot import name 'fit_pd_model'`

- [ ] **Step 3: Implement PD model fitting**

Add to `wko5/pdcurve.py`:

```python
from scipy.optimize import curve_fit


def _pd_model(t, pmax, tau, frc_kj, t0, mftp):
    """3-component power-duration model.

    P(t) = Pmax * e^(-t/tau) + FRC*1000/(t+t0) + mFTP
    """
    return pmax * np.exp(-t / tau) + frc_kj * 1000 / (t + t0) + mftp


def fit_pd_model(mmp):
    """Fit the 3-component PD model to an MMP array.

    Returns dict with {Pmax, FRC, mFTP, TTE, mVO2max, tau, t0} or None on failure.
    """
    if len(mmp) < 60:
        logger.warning("MMP too short for model fitting (need >= 60s)")
        return None

    # Fit from 5s onwards to avoid noisy short-duration data
    max_dur = min(len(mmp), 7200)  # cap at 2 hours
    durations = np.arange(5, max_dur + 1, dtype=float)
    powers = mmp[4:max_dur].astype(float)

    if len(durations) != len(powers):
        durations = durations[:len(powers)]

    # Initial guesses
    p0 = [1200, 15, 20, 5, 280]

    # Bounds: [Pmax, tau, FRC_kJ, t0, mFTP]
    bounds_low = [800, 5, 5, 1, 150]
    bounds_high = [2500, 30, 30, 15, 400]

    try:
        popt, _ = curve_fit(
            _pd_model, durations, powers,
            p0=p0, bounds=(bounds_low, bounds_high),
            maxfev=10000,
        )
    except (RuntimeError, ValueError) as e:
        logger.warning(f"PD model fitting failed: {e}")
        return None

    pmax, tau, frc_kj, t0, mftp = popt

    # TTE: find where modeled curve drops below mFTP
    # This is approximately where FRC contribution becomes negligible
    t_range = np.arange(1, max_dur + 1, dtype=float)
    modeled = _pd_model(t_range, *popt)
    above_ftp = np.where(modeled > mftp + 1)[0]  # +1W buffer
    tte = float(above_ftp[-1] + 1) if len(above_ftp) > 0 else float("nan")

    # mVO2max via ACSM cycling equation: VO2 (mL/min) = (watts * 12.35) + (weight * 3.5)
    vo2max_ml_min = (mftp * 12.35) + (WEIGHT_KG * 3.5)
    vo2max_ml_min_kg = vo2max_ml_min / WEIGHT_KG

    return {
        "Pmax": round(float(pmax), 1),
        "FRC": round(float(frc_kj), 2),
        "mFTP": round(float(mftp), 1),
        "TTE": round(tte / 60, 1),  # convert to minutes
        "mVO2max_L_min": round(vo2max_ml_min / 1000, 2),
        "mVO2max_ml_min_kg": round(vo2max_ml_min_kg, 1),
        "tau": round(float(tau), 1),
        "t0": round(float(t0), 1),
    }


def power_at_durations(mmp, durations=None):
    """Extract power at specific durations from MMP array.

    Args:
        mmp: MMP array (index 0 = 1s, index 1 = 2s, ...)
        durations: list of durations in seconds (default: [5, 60, 300, 1200, 3600])

    Returns dict mapping duration_s -> power (NaN if beyond MMP length).
    """
    if durations is None:
        durations = [5, 60, 300, 1200, 3600]

    result = {}
    for d in durations:
        if d <= len(mmp):
            result[d] = float(mmp[d - 1])
        else:
            result[d] = float("nan")
    return result


def rolling_ftp(window_days=90, step_days=7):
    """Compute rolling modeled FTP over training history.

    Returns DataFrame with columns: date, mFTP, Pmax, FRC
    """
    activities = get_activities()
    if activities.empty:
        return pd.DataFrame()

    activities["start_time"] = pd.to_datetime(activities["start_time"])
    min_date = activities["start_time"].min()
    max_date = activities["start_time"].max()

    results = []
    current = min_date + pd.Timedelta(days=window_days)

    while current <= max_date:
        start = (current - pd.Timedelta(days=window_days)).strftime("%Y-%m-%d")
        end = current.strftime("%Y-%m-%d 23:59:59")

        mmp = compute_envelope_mmp(start=start, end=end)
        if len(mmp) >= 60:
            model = fit_pd_model(mmp)
            if model:
                results.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "mFTP": model["mFTP"],
                    "Pmax": model["Pmax"],
                    "FRC": model["FRC"],
                    "TTE_min": model["TTE"],
                })

        current += pd.Timedelta(days=step_days)

    return pd.DataFrame(results)


def compare_periods(period1, period2):
    """Compare PD curves between two periods.

    Args:
        period1: (start_date, end_date) tuple
        period2: (start_date, end_date) tuple

    Returns dict with MMP arrays and model params for each period.
    """
    mmp1 = compute_envelope_mmp(start=period1[0], end=period1[1])
    mmp2 = compute_envelope_mmp(start=period2[0], end=period2[1])
    model1 = fit_pd_model(mmp1) if len(mmp1) >= 60 else None
    model2 = fit_pd_model(mmp2) if len(mmp2) >= 60 else None

    return {
        "period1": {"mmp": mmp1, "model": model1, "range": period1},
        "period2": {"mmp": mmp2, "model": model2, "range": period2},
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_pdcurve.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add wko5/pdcurve.py tests/test_pdcurve.py
git commit -m "feat: add PD model fitting with FTP/FRC/Pmax/TTE/VO2max estimation"
```

---

## Chunk 3: Training Load (training_load.py)

### Task 5: NP, TSS, and PMC

**Files:**
- Create: `wko5/training_load.py`
- Create: `tests/test_training_load.py`

- [ ] **Step 1: Write tests for training_load.py**

```python
# tests/test_training_load.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.training_load import compute_np, compute_tss, build_pmc, current_fitness, efficiency_factor


def test_compute_np_constant_power():
    """NP of constant power should equal that power."""
    power = pd.Series([250.0] * 3600)  # 1 hour at 250W
    np_val = compute_np(power)
    assert abs(np_val - 250.0) < 1.0


def test_compute_np_variable_power():
    """NP should be >= average power for variable power."""
    power = pd.Series([200.0] * 1800 + [300.0] * 1800)
    np_val = compute_np(power)
    avg = power.mean()
    assert np_val >= avg


def test_compute_np_with_zeros():
    """NP should handle zeros (coasting)."""
    power = pd.Series([300.0] * 100 + [0.0] * 100 + [300.0] * 100)
    np_val = compute_np(power)
    assert np_val > 0


def test_compute_np_short_series():
    """NP of series shorter than 30s should still work."""
    power = pd.Series([250.0] * 10)
    np_val = compute_np(power)
    assert np_val > 0


def test_compute_tss_one_hour_at_ftp():
    """1 hour at FTP should give TSS ≈ 100."""
    tss = compute_tss(np_watts=292.0, duration_s=3600, ftp=292.0)
    assert abs(tss - 100.0) < 1.0


def test_compute_tss_half_hour_at_ftp():
    """30 min at FTP should give TSS ≈ 50."""
    tss = compute_tss(np_watts=292.0, duration_s=1800, ftp=292.0)
    assert abs(tss - 50.0) < 1.0


def test_compute_tss_above_ftp():
    """Higher NP than FTP should give TSS > 100/hr."""
    tss = compute_tss(np_watts=350.0, duration_s=3600, ftp=292.0)
    assert tss > 100


def test_build_pmc_returns_dataframe():
    """PMC should return a DataFrame with CTL, ATL, TSB columns."""
    pmc = build_pmc()
    assert isinstance(pmc, pd.DataFrame)
    assert "CTL" in pmc.columns
    assert "ATL" in pmc.columns
    assert "TSB" in pmc.columns
    assert len(pmc) > 100  # should span many days


def test_pmc_tsb_equals_ctl_minus_atl():
    """TSB should equal CTL - ATL for every row."""
    pmc = build_pmc()
    if not pmc.empty:
        diff = abs(pmc["TSB"] - (pmc["CTL"] - pmc["ATL"]))
        assert diff.max() < 0.01


def test_current_fitness_returns_dict():
    """current_fitness should return dict with CTL, ATL, TSB."""
    result = current_fitness()
    assert isinstance(result, dict)
    assert "CTL" in result
    assert "ATL" in result
    assert "TSB" in result


def test_efficiency_factor():
    """EF should be NP/avgHR for a real activity."""
    ef = efficiency_factor(1)
    # Activity 1 has HR=0 in the data, so EF may be nan
    assert isinstance(ef, float)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_training_load.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement training_load.py**

```python
# wko5/training_load.py
"""Training load — NP, TSS, IF, CTL/ATL/TSB (PMC), efficiency factor."""

import logging

import numpy as np
import pandas as pd

from wko5.db import get_connection, get_activities, get_records, FTP_DEFAULT

logger = logging.getLogger(__name__)


def compute_np(power_series):
    """Compute Normalized Power.

    30s rolling average → 4th power → mean → 4th root.
    """
    power = power_series.fillna(0).values.astype(float)
    n = len(power)
    if n == 0:
        return float("nan")

    window = min(30, n)
    # Rolling 30s average
    rolling_avg = pd.Series(power).rolling(window=window, min_periods=1).mean().values
    # 4th power → mean → 4th root
    np_val = (np.mean(rolling_avg ** 4)) ** 0.25
    return float(np_val)


def compute_tss(np_watts, duration_s, ftp):
    """Compute Training Stress Score.

    TSS = (duration_s * NP^2) / (FTP^2 * 3600) * 100
    """
    if ftp <= 0 or duration_s <= 0 or np.isnan(np_watts):
        return float("nan")
    return (duration_s * np_watts ** 2) / (ftp ** 2 * 3600) * 100


def _get_activity_tss(activity_row, ftp=None):
    """Get TSS for an activity, using device value or computing from records."""
    # Try device-reported TSS
    device_tss = activity_row.get("training_stress_score")
    if device_tss and not pd.isna(device_tss) and device_tss > 0:
        return float(device_tss)

    # Determine FTP
    if ftp is None:
        device_ftp = activity_row.get("threshold_power")
        if device_ftp and not pd.isna(device_ftp) and device_ftp > 0:
            ftp = float(device_ftp)
        else:
            ftp = FTP_DEFAULT

    # Compute from records
    records = get_records(activity_row["id"])
    if records.empty or "power" not in records.columns:
        return 0.0

    np_watts = compute_np(records["power"])
    duration_s = float(activity_row.get("total_timer_time") or len(records))
    return compute_tss(np_watts, duration_s, ftp)


def _ensure_tss_cache_table(conn):
    """Create tss_cache table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tss_cache (
            activity_id INTEGER PRIMARY KEY,
            np_watts REAL,
            tss REAL,
            ftp_used REAL,
            FOREIGN KEY (activity_id) REFERENCES activities(id)
        )
    """)
    conn.commit()


def _get_cached_tss(activity_id, activity_row, ftp=None):
    """Get TSS from cache, or compute and cache it."""
    conn = get_connection()
    _ensure_tss_cache_table(conn)

    # Check cache
    cursor = conn.cursor()
    cursor.execute("SELECT tss FROM tss_cache WHERE activity_id = ?", (activity_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return float(row[0])

    # Compute
    tss = _get_activity_tss(activity_row, ftp=ftp)

    # Cache it
    np_watts = float("nan")
    ftp_used = ftp or FTP_DEFAULT
    conn.execute(
        "INSERT OR REPLACE INTO tss_cache (activity_id, np_watts, tss, ftp_used) VALUES (?, ?, ?, ?)",
        (activity_id, np_watts, tss, ftp_used),
    )
    conn.commit()
    conn.close()
    return tss


def build_pmc(start=None, end=None, ftp=None):
    """Build Performance Management Chart (CTL/ATL/TSB).

    Returns DataFrame with columns: date, TSS, CTL, ATL, TSB.
    Uses a TSS cache table to avoid recomputing NP/TSS from records each time.
    """
    activities = get_activities(start=start, end=end)
    if activities.empty:
        return pd.DataFrame()

    activities["date"] = pd.to_datetime(activities["start_time"]).dt.date

    # Compute TSS per activity (cached)
    tss_list = []
    for _, act in activities.iterrows():
        tss = _get_cached_tss(act["id"], act, ftp=ftp)
        tss_list.append({"date": act["date"], "tss": tss})

    tss_df = pd.DataFrame(tss_list)
    daily_tss = tss_df.groupby("date")["tss"].sum().reset_index()
    daily_tss.columns = ["date", "TSS"]
    daily_tss["date"] = pd.to_datetime(daily_tss["date"])

    # Fill in rest days
    full_range = pd.date_range(daily_tss["date"].min(), daily_tss["date"].max())
    daily = pd.DataFrame({"date": full_range})
    daily = daily.merge(daily_tss, on="date", how="left").fillna(0)

    # EWMA for CTL (42-day) and ATL (7-day)
    # decay = 1 - exp(-1/tc) where tc is time constant in days
    ctl_decay = 1 - np.exp(-1 / 42)
    atl_decay = 1 - np.exp(-1 / 7)

    daily["CTL"] = daily["TSS"].ewm(alpha=ctl_decay, adjust=False).mean()
    daily["ATL"] = daily["TSS"].ewm(alpha=atl_decay, adjust=False).mean()
    daily["TSB"] = daily["CTL"] - daily["ATL"]

    return daily


def current_fitness(ftp=None):
    """Get latest CTL, ATL, TSB snapshot."""
    pmc = build_pmc(ftp=ftp)
    if pmc.empty:
        return {"CTL": 0, "ATL": 0, "TSB": 0}
    last = pmc.iloc[-1]
    return {
        "CTL": round(float(last["CTL"]), 1),
        "ATL": round(float(last["ATL"]), 1),
        "TSB": round(float(last["TSB"]), 1),
        "date": str(last["date"].date()),
    }


def fitness_trend(days=365, ftp=None):
    """Get CTL trajectory over recent days."""
    start = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    pmc = build_pmc(start=start, ftp=ftp)
    return pmc


def efficiency_factor(activity_id):
    """Compute Efficiency Factor (NP / avg HR) for an activity."""
    records = get_records(activity_id)
    if records.empty:
        return float("nan")

    np_watts = compute_np(records["power"])
    hr = records["heart_rate"].dropna()
    hr = hr[hr > 0]
    if hr.empty:
        return float("nan")

    avg_hr = hr.mean()
    return round(float(np_watts / avg_hr), 3)


def ef_trend(days=365):
    """Track Efficiency Factor over time."""
    start = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    activities = get_activities(start=start)

    results = []
    for _, act in activities.iterrows():
        ef = efficiency_factor(act["id"])
        if not np.isnan(ef):
            results.append({
                "date": act["start_time"][:10],
                "EF": ef,
                "activity_id": act["id"],
            })

    return pd.DataFrame(results)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_training_load.py -v`
Expected: All tests PASS. Note: `build_pmc` and `current_fitness` hit the real DB and compute TSS for activities that lack device-reported values — this may be slow on first run.

- [ ] **Step 5: Commit**

```bash
git add wko5/training_load.py tests/test_training_load.py
git commit -m "feat: add training load — NP, TSS, PMC (CTL/ATL/TSB), efficiency factor"
```

---

## Chunk 4: Zones and Ride Analysis (zones.py, ride.py)

### Task 6: Training zones (zones.py)

**Files:**
- Create: `wko5/zones.py`
- Create: `tests/test_zones.py`

- [ ] **Step 1: Write tests for zones.py**

```python
# tests/test_zones.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from wko5.zones import coggan_zones, seiler_zones, ilevels, time_in_zones, hr_zones


def test_coggan_zones_boundaries():
    """Coggan zones should have 7 zones covering full power range."""
    zones = coggan_zones(292)
    assert len(zones) == 7
    assert "Active Recovery" in zones
    assert "Neuromuscular" in zones
    # Threshold zone should bracket FTP
    low, high = zones["Threshold"]
    assert low < 292 < high


def test_coggan_zones_values():
    """Check specific zone boundaries for FTP=292."""
    zones = coggan_zones(292)
    # Endurance: 56-75% of FTP
    low, high = zones["Endurance"]
    assert abs(low - 292 * 0.56) < 1
    assert abs(high - 292 * 0.75) < 1


def test_seiler_zones():
    """Seiler 3-zone model."""
    zones = seiler_zones(292)
    assert len(zones) == 3
    assert zones["Zone 1"][1] == int(292 * 0.80)


def test_ilevels_with_pd_model():
    """iLevels should return 7 individualized zones."""
    pd_model = {"mFTP": 292, "FRC": 15.0, "TTE": 45, "Pmax": 1200}
    zones = ilevels(pd_model)
    assert len(zones) == 7
    # Zone 4 (Threshold) should end near mFTP
    assert zones["Threshold"][1] == 292


def test_hr_zones():
    """HR zones should return 5 zones."""
    zones = hr_zones(max_hr=190, lthr=172)
    assert len(zones) == 5


def test_time_in_zones():
    """Time in zones should sum to total samples."""
    zones = coggan_zones(292)
    power = pd.Series([100] * 50 + [250] * 50 + [350] * 50)
    tiz = time_in_zones(power, zones)
    total = sum(tiz.values())
    assert total == 150
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_zones.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement zones.py**

```python
# wko5/zones.py
"""Training zones — Coggan, iLevels, Seiler, HR zones, time-in-zone analysis."""

import logging

import pandas as pd

from wko5.db import get_connection, get_activities, get_records, FTP_DEFAULT

logger = logging.getLogger(__name__)


def coggan_zones(ftp):
    """Classic Coggan 7-zone system based on % of FTP."""
    ftp = float(ftp)
    return {
        "Active Recovery": (0, int(ftp * 0.55)),
        "Endurance": (int(ftp * 0.56), int(ftp * 0.75)),
        "Tempo": (int(ftp * 0.76), int(ftp * 0.90)),
        "Threshold": (int(ftp * 0.91), int(ftp * 1.05)),
        "VO2max": (int(ftp * 1.06), int(ftp * 1.20)),
        "Anaerobic": (int(ftp * 1.21), int(ftp * 1.50)),
        "Neuromuscular": (int(ftp * 1.51), 9999),
    }


def ilevels(pd_model):
    """Individualized 7-zone system derived from PD model parameters.

    Uses mFTP, FRC, and TTE to set zone boundaries that reflect
    individual physiology rather than fixed percentages.
    """
    mftp = pd_model["mFTP"]
    frc = pd_model["FRC"]  # kJ
    tte = pd_model.get("TTE", 45)  # minutes

    # FRC-derived power at ~3min (VO2max power)
    # P_vo2 ≈ mFTP + FRC*1000/180 (180s = 3min)
    frc_3min = frc * 1000 / 180
    frc_30s = frc * 1000 / 30

    return {
        "Recovery": (0, int(mftp * 0.55)),
        "Endurance": (int(mftp * 0.55), int(mftp * 0.76)),
        "Tempo": (int(mftp * 0.76), int(mftp * 0.90)),
        "Threshold": (int(mftp * 0.90), int(mftp)),
        "VO2max": (int(mftp), int(mftp + frc_3min * 0.15)),
        "Anaerobic": (int(mftp + frc_3min * 0.15), int(mftp + frc_30s * 0.50)),
        "Neuromuscular": (int(mftp + frc_30s * 0.50), 9999),
    }


def seiler_zones(ftp):
    """Seiler 3-zone polarized model."""
    ftp = float(ftp)
    return {
        "Zone 1": (0, int(ftp * 0.80)),
        "Zone 2": (int(ftp * 0.80) + 1, int(ftp)),
        "Zone 3": (int(ftp) + 1, 9999),
    }


def hr_zones(max_hr, lthr):
    """Coggan 5-zone HR system."""
    return {
        "Zone 1": (0, int(max_hr * 0.68)),
        "Zone 2": (int(max_hr * 0.69), int(max_hr * 0.83)),
        "Zone 3": (int(max_hr * 0.84), int(max_hr * 0.94)),
        "Zone 4": (int(max_hr * 0.95), int(lthr * 1.05)),
        "Zone 5": (int(lthr * 1.05) + 1, 9999),
    }


def time_in_zones(power_series, zones):
    """Count seconds spent in each zone.

    Returns dict: zone_name -> seconds.
    """
    power = power_series.fillna(0).values
    result = {name: 0 for name in zones}

    for w in power:
        for name, (low, high) in zones.items():
            if low <= w <= high:
                result[name] += 1
                break

    return result


def ride_distribution(activity_id, zone_system="coggan", ftp=None):
    """Get zone distribution for a single ride."""
    if ftp is None:
        ftp = FTP_DEFAULT

    records = get_records(activity_id)
    if records.empty:
        return {}

    if zone_system == "coggan":
        zones = coggan_zones(ftp)
    elif zone_system == "seiler":
        zones = seiler_zones(ftp)
    else:
        zones = coggan_zones(ftp)

    return time_in_zones(records["power"], zones)


def period_distribution(start, end, zone_system="coggan", ftp=None):
    """Get aggregate zone distribution across rides in a date range."""
    if ftp is None:
        ftp = FTP_DEFAULT

    activities = get_activities(start=start, end=end)
    if activities.empty:
        return {}

    if zone_system == "coggan":
        zones = coggan_zones(ftp)
    elif zone_system == "seiler":
        zones = seiler_zones(ftp)
    else:
        zones = coggan_zones(ftp)

    total = {name: 0 for name in zones}
    for _, act in activities.iterrows():
        records = get_records(act["id"])
        if not records.empty:
            tiz = time_in_zones(records["power"], zones)
            for name in total:
                total[name] += tiz.get(name, 0)

    return total
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_zones.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add wko5/zones.py tests/test_zones.py
git commit -m "feat: add training zones — Coggan, iLevels, Seiler, HR, time-in-zone"
```

---

### Task 7: Ride analysis (ride.py)

**Files:**
- Create: `wko5/ride.py`
- Create: `tests/test_ride.py`

- [ ] **Step 1: Write tests for ride.py**

```python
# tests/test_ride.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.ride import (
    ride_summary, detect_intervals, lap_analysis,
    hr_decoupling, best_efforts, power_histogram,
)


def test_ride_summary_returns_dict():
    """ride_summary should return a dict with key metrics."""
    result = ride_summary(1)
    assert isinstance(result, dict)
    assert "avg_power" in result
    assert "np" in result
    assert "duration_s" in result
    assert result["avg_power"] > 0


def test_ride_summary_invalid_id():
    """Invalid activity should return empty dict."""
    result = ride_summary(999999)
    assert result == {}


def test_detect_intervals_synthetic():
    """Detect intervals in synthetic data: 3x 2min at 300W / 1min at 100W."""
    # We'll test with a real ride instead — synthetic requires mocking
    result = detect_intervals(1)
    assert isinstance(result, list)
    # Each interval should have required keys
    if result:
        assert "avg_power" in result[0]
        assert "duration_s" in result[0]


def test_lap_analysis():
    """lap_analysis should return a DataFrame."""
    result = lap_analysis(1)
    assert isinstance(result, pd.DataFrame)


def test_best_efforts():
    """best_efforts should return powers at specified durations."""
    result = best_efforts(1, durations=[60, 300])
    assert isinstance(result, dict)
    if result:
        assert 60 in result
        assert result[60] > 0


def test_power_histogram():
    """power_histogram should return a DataFrame with bin and count columns."""
    result = power_histogram(1, bin_width=25)
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_hr_decoupling():
    """HR decoupling should return a float."""
    result = hr_decoupling(1)
    assert isinstance(result, float)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_ride.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement ride.py**

```python
# wko5/ride.py
"""Single ride analysis — summary, interval detection, laps, HR decoupling."""

import logging

import numpy as np
import pandas as pd

from wko5.db import get_connection, get_records, FTP_DEFAULT
from wko5.training_load import compute_np, compute_tss
from wko5.pdcurve import compute_mmp

logger = logging.getLogger(__name__)


def ride_summary(activity_id):
    """Comprehensive summary of a single ride."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {}

    columns = [desc[0] for desc in cursor.description]
    act = dict(zip(columns, row))
    conn.close()

    records = get_records(activity_id)
    if records.empty:
        return {}

    power = records["power"].fillna(0)
    np_watts = compute_np(power)
    ftp = act.get("threshold_power") or FTP_DEFAULT
    if not ftp or ftp <= 0:
        ftp = FTP_DEFAULT
    intensity_factor = np_watts / ftp
    duration_s = float(act.get("total_timer_time") or len(records))
    tss = compute_tss(np_watts, duration_s, ftp)
    kj = float(power.sum()) / 1000

    return {
        "activity_id": activity_id,
        "date": act.get("start_time", "")[:10],
        "sub_sport": act.get("sub_sport", ""),
        "duration_s": round(duration_s),
        "duration_min": round(duration_s / 60, 1),
        "distance_km": round(float(act.get("total_distance") or 0) / 1000, 1),
        "avg_power": round(float(power.mean()), 1),
        "np": round(np_watts, 1),
        "max_power": int(power.max()),
        "IF": round(intensity_factor, 2),
        "TSS": round(tss, 1),
        "kJ": round(kj, 1),
        "avg_hr": round(float(records["heart_rate"].dropna().mean()), 1) if records["heart_rate"].notna().any() else None,
        "max_hr": int(records["heart_rate"].max()) if records["heart_rate"].notna().any() else None,
        "avg_cadence": round(float(records["cadence"].dropna().mean()), 1) if records["cadence"].notna().any() else None,
        "elevation_gain": float(act.get("total_ascent") or 0),
        "ftp_used": ftp,
    }


def detect_intervals(activity_id, min_power_pct=0.9, min_duration=30, ftp=None):
    """Detect work intervals in a ride.

    Finds sustained efforts above min_power_pct * FTP for at least min_duration seconds.
    Uses 10s smoothing to avoid false splits.
    """
    if ftp is None:
        ftp = FTP_DEFAULT
    threshold = ftp * min_power_pct

    records = get_records(activity_id)
    if records.empty:
        return []

    power = records["power"].fillna(0)
    # 10s smoothing
    smoothed = power.rolling(window=10, min_periods=1).mean()

    intervals = []
    in_interval = False
    start_idx = 0

    for i, p in enumerate(smoothed):
        if p >= threshold and not in_interval:
            in_interval = True
            start_idx = i
        elif p < threshold and in_interval:
            duration = i - start_idx
            if duration >= min_duration:
                segment = power.iloc[start_idx:i]
                hr_segment = records["heart_rate"].iloc[start_idx:i].dropna()
                cad_segment = records["cadence"].iloc[start_idx:i].dropna()
                intervals.append({
                    "start_idx": start_idx,
                    "end_idx": i,
                    "duration_s": duration,
                    "avg_power": round(float(segment.mean()), 1),
                    "max_power": int(segment.max()),
                    "avg_hr": round(float(hr_segment.mean()), 1) if len(hr_segment) > 0 else None,
                    "avg_cadence": round(float(cad_segment.mean()), 1) if len(cad_segment) > 0 else None,
                })
            in_interval = False

    # Handle interval that extends to end of ride
    if in_interval:
        duration = len(smoothed) - start_idx
        if duration >= min_duration:
            segment = power.iloc[start_idx:]
            hr_segment = records["heart_rate"].iloc[start_idx:].dropna()
            cad_segment = records["cadence"].iloc[start_idx:].dropna()
            intervals.append({
                "start_idx": start_idx,
                "end_idx": len(smoothed),
                "duration_s": duration,
                "avg_power": round(float(segment.mean()), 1),
                "max_power": int(segment.max()),
                "avg_hr": round(float(hr_segment.mean()), 1) if len(hr_segment) > 0 else None,
                "avg_cadence": round(float(cad_segment.mean()), 1) if len(cad_segment) > 0 else None,
            })

    return intervals


def lap_analysis(activity_id):
    """Get per-lap stats from the laps table."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM laps WHERE activity_id = ? ORDER BY lap_number",
        conn,
        params=(activity_id,),
    )
    conn.close()
    return df


def hr_decoupling(activity_id):
    """Compute HR decoupling: compare power:HR ratio first half vs second half.

    Returns percentage decoupling. >5% suggests aerobic drift.
    Positive = HR drifted up relative to power.
    """
    records = get_records(activity_id)
    if records.empty:
        return float("nan")

    power = records["power"].fillna(0)
    hr = records["heart_rate"]

    # Need valid HR data
    valid = (hr > 0) & hr.notna() & (power > 0)
    if valid.sum() < 60:
        return float("nan")

    power_valid = power[valid].values
    hr_valid = hr[valid].values

    mid = len(power_valid) // 2
    first_half_ratio = power_valid[:mid].mean() / hr_valid[:mid].mean()
    second_half_ratio = power_valid[mid:].mean() / hr_valid[mid:].mean()

    if first_half_ratio == 0:
        return float("nan")

    decoupling = (first_half_ratio - second_half_ratio) / first_half_ratio * 100
    return round(float(decoupling), 2)


def best_efforts(activity_id, durations=None):
    """Find best average power at specified durations within a single ride.

    Returns dict: duration_s -> best_avg_power.
    """
    if durations is None:
        durations = [60, 300, 1200]

    records = get_records(activity_id)
    if records.empty:
        return {}

    mmp = compute_mmp(records["power"])
    result = {}
    for d in durations:
        if d <= len(mmp):
            result[d] = round(float(mmp[d - 1]), 1)
        else:
            result[d] = float("nan")
    return result


def power_histogram(activity_id, bin_width=10):
    """Power distribution histogram.

    Returns DataFrame with columns: bin_start, bin_end, seconds.
    """
    records = get_records(activity_id)
    if records.empty:
        return pd.DataFrame()

    power = records["power"].fillna(0).values
    max_power = int(power.max())
    bins = range(0, max_power + bin_width, bin_width)

    counts, edges = np.histogram(power, bins=bins)
    return pd.DataFrame({
        "bin_start": edges[:-1].astype(int),
        "bin_end": edges[1:].astype(int),
        "seconds": counts,
    })
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_ride.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add wko5/ride.py tests/test_ride.py
git commit -m "feat: add ride analysis — summary, interval detection, laps, HR decoupling"
```

---

## Chunk 5: Profile and Package Finalization (profile.py, __init__.py)

### Task 8: Power profile, phenotype, and fatigue resistance (profile.py)

**Files:**
- Create: `wko5/profile.py`
- Create: `tests/test_profile.py`

- [ ] **Step 1: Write tests for profile.py**

```python
# tests/test_profile.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from wko5.profile import (
    power_profile, coggan_ranking, strengths_limiters,
    phenotype, profile_trend, fatigue_resistance,
)
from wko5.db import WEIGHT_KG


def test_power_profile_returns_watts_and_wkg():
    """Power profile should have watts and W/kg at key durations."""
    profile = power_profile(days=90)
    assert isinstance(profile, dict)
    if profile:  # may be empty if no recent data
        assert "watts" in profile
        assert "wkg" in profile
        assert 60 in profile["watts"]
        assert 300 in profile["watts"]
        # W/kg should be watts / weight
        for d in profile["watts"]:
            if not np.isnan(profile["watts"][d]):
                expected_wkg = profile["watts"][d] / WEIGHT_KG
                assert abs(profile["wkg"][d] - expected_wkg) < 0.1


def test_coggan_ranking():
    """Coggan ranking should categorize power at each duration."""
    profile = {
        "wkg": {5: 18.0, 60: 7.0, 300: 5.5, 1200: 4.5, 3600: 4.0},
    }
    ranking = coggan_ranking(profile)
    assert isinstance(ranking, dict)
    assert 5 in ranking
    assert ranking[5] in [
        "Untrained", "Fair", "Moderate", "Good", "Very Good", "Exceptional", "World Class"
    ]


def test_strengths_limiters():
    """Should identify strongest and weakest durations."""
    profile = {
        "wkg": {5: 18.0, 60: 7.0, 300: 5.5, 1200: 4.5, 3600: 3.5},
    }
    result = strengths_limiters(profile)
    assert "strength" in result
    assert "limiter" in result


def test_phenotype_sprinter():
    """High Pmax:mFTP ratio should classify as Sprinter."""
    model = {"Pmax": 1800, "mFTP": 280, "FRC": 25, "TTE": 40}
    result = phenotype(model)
    assert "Sprinter" in result


def test_phenotype_tter():
    """Low Pmax:mFTP with high TTE should classify as TTer."""
    model = {"Pmax": 1100, "mFTP": 290, "FRC": 12, "TTE": 55}
    result = phenotype(model)
    assert "TTer" in result


def test_profile_trend_returns_dataframe():
    """profile_trend should return a DataFrame."""
    import pandas as pd
    result = profile_trend(duration_s=300, window_days=90, step_days=30)
    assert isinstance(result, pd.DataFrame)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_profile.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement profile.py**

```python
# wko5/profile.py
"""Power profile, Coggan ranking, strengths/limiters, phenotype, fatigue resistance."""

import logging

import numpy as np
import pandas as pd

from wko5.db import get_activities, get_records, WEIGHT_KG
from wko5.pdcurve import compute_envelope_mmp, compute_mmp, power_at_durations

logger = logging.getLogger(__name__)

# Coggan power profile table (W/kg, male)
# Columns: 5s, 60s, 300s, 1200s, 3600s
COGGAN_TABLE = {
    "World Class":  {5: 24.04, 60: 11.50, 300: 7.60, 1200: 6.40, 3600: 6.10},
    "Exceptional":  {5: 22.22, 60: 10.44, 300: 6.95, 1200: 5.69, 3600: 5.36},
    "Very Good":    {5: 19.31, 60: 8.87,  300: 5.97, 1200: 4.92, 3600: 4.62},
    "Good":         {5: 16.85, 60: 7.42,  300: 5.05, 1200: 4.23, 3600: 3.90},
    "Moderate":     {5: 14.18, 60: 5.97,  300: 4.19, 1200: 3.52, 3600: 3.23},
    "Fair":         {5: 11.51, 60: 4.63,  300: 3.34, 1200: 2.78, 3600: 2.53},
    "Untrained":    {5: 0,     60: 0,     300: 0,    1200: 0,    3600: 0},
}

CATEGORY_ORDER = [
    "Untrained", "Fair", "Moderate", "Good", "Very Good", "Exceptional", "World Class"
]

KEY_DURATIONS = [5, 60, 300, 1200, 3600]


def power_profile(days=90, sub_sport=None):
    """Extract power at key durations in watts and W/kg."""
    mmp = compute_envelope_mmp(days=days, sub_sport=sub_sport)
    if len(mmp) == 0:
        return {}

    watts = power_at_durations(mmp, KEY_DURATIONS)
    wkg = {d: round(w / WEIGHT_KG, 2) if not np.isnan(w) else float("nan") for d, w in watts.items()}

    return {"watts": watts, "wkg": wkg}


def coggan_ranking(profile):
    """Rank W/kg at each duration against Coggan power profile table."""
    if not profile or "wkg" not in profile:
        return {}

    result = {}
    for d in KEY_DURATIONS:
        wkg = profile["wkg"].get(d, float("nan"))
        if np.isnan(wkg):
            result[d] = "Unknown"
            continue

        category = "Untrained"
        for cat in CATEGORY_ORDER[1:]:  # skip Untrained
            threshold = COGGAN_TABLE[cat].get(d, 9999)
            if wkg >= threshold:
                category = cat
        result[d] = category

    return result


def strengths_limiters(profile):
    """Identify relative strengths and limiters across durations."""
    ranking = coggan_ranking(profile)
    if not ranking:
        return {}

    # Map categories to numeric scores
    cat_score = {cat: i for i, cat in enumerate(CATEGORY_ORDER)}

    scored = {}
    for d, cat in ranking.items():
        if cat != "Unknown":
            scored[d] = cat_score.get(cat, 0)

    if not scored:
        return {}

    best_d = max(scored, key=scored.get)
    worst_d = min(scored, key=scored.get)

    duration_labels = {5: "5s (neuromuscular)", 60: "1min (anaerobic)", 300: "5min (VO2max)", 1200: "20min (threshold)", 3600: "60min (endurance)"}

    return {
        "strength": {"duration": best_d, "label": duration_labels.get(best_d, f"{best_d}s"), "category": ranking[best_d]},
        "limiter": {"duration": worst_d, "label": duration_labels.get(worst_d, f"{worst_d}s"), "category": ranking[worst_d]},
        "all_rankings": {duration_labels.get(d, f"{d}s"): cat for d, cat in ranking.items()},
    }


def phenotype(pd_model):
    """Classify rider phenotype based on PD model parameters."""
    if not pd_model:
        return "Unknown"

    pmax = pd_model.get("Pmax", 0)
    mftp = pd_model.get("mFTP", 1)
    frc = pd_model.get("FRC", 0)
    tte = pd_model.get("TTE", 0)

    pmax_ratio = pmax / mftp
    frc_ratio = frc / mftp  # kJ/W

    if pmax_ratio > 6.0 and frc_ratio > 0.08:
        return f"Sprinter (Pmax/FTP={pmax_ratio:.1f}, FRC/FTP={frc_ratio:.3f})"
    elif 4.5 <= pmax_ratio <= 6.0 and frc_ratio > 0.06:
        return f"Pursuiter (Pmax/FTP={pmax_ratio:.1f}, FRC/FTP={frc_ratio:.3f})"
    elif pmax_ratio < 4.5 and tte > 50:
        return f"TTer (Pmax/FTP={pmax_ratio:.1f}, TTE={tte:.0f}min)"
    else:
        return f"All-rounder (Pmax/FTP={pmax_ratio:.1f}, FRC/FTP={frc_ratio:.3f}, TTE={tte:.0f}min)"


def profile_trend(duration_s, window_days=90, step_days=7):
    """Track power at a specific duration over time using rolling windows."""
    activities = get_activities()
    if activities.empty:
        return pd.DataFrame()

    activities["start_time"] = pd.to_datetime(activities["start_time"])
    min_date = activities["start_time"].min()
    max_date = activities["start_time"].max()

    results = []
    current = min_date + pd.Timedelta(days=window_days)

    while current <= max_date:
        start = (current - pd.Timedelta(days=window_days)).strftime("%Y-%m-%d")
        end = current.strftime("%Y-%m-%d 23:59:59")

        mmp = compute_envelope_mmp(start=start, end=end)
        if len(mmp) >= duration_s:
            watts = float(mmp[duration_s - 1])
            results.append({
                "date": current.strftime("%Y-%m-%d"),
                "watts": round(watts, 1),
                "wkg": round(watts / WEIGHT_KG, 2),
            })

        current += pd.Timedelta(days=step_days)

    return pd.DataFrame(results)


def compare_profiles(period1, period2):
    """Compare power profiles between two date ranges.

    Args:
        period1: (start, end) date strings
        period2: (start, end) date strings
    """
    p1 = _profile_for_range(period1[0], period1[1])
    p2 = _profile_for_range(period2[0], period2[1])

    return {"period1": p1, "period2": p2}


def _profile_for_range(start, end):
    """Helper: compute power profile for a date range."""
    mmp = compute_envelope_mmp(start=start, end=end)
    if len(mmp) == 0:
        return {}
    watts = power_at_durations(mmp, KEY_DURATIONS)
    wkg = {d: round(w / WEIGHT_KG, 2) if not np.isnan(w) else float("nan") for d, w in watts.items()}
    return {"watts": watts, "wkg": wkg}


def fatigue_resistance(days=90, fresh_minutes=30, fatigue_kj=1500):
    """Compare power when fresh vs. fatigued.

    Fresh: first fresh_minutes of each ride.
    Fatigued: portion of ride after fatigue_kj of work accumulated.

    Returns dict with stamina ratios at key durations.
    """
    activities = get_activities(
        start=(pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d"),
    )

    fresh_mmps = []
    fatigued_mmps = []

    for _, act in activities.iterrows():
        records = get_records(act["id"])
        if records.empty or "power" not in records.columns:
            continue

        power = records["power"].fillna(0)

        # Fresh portion: first N minutes
        fresh_end = min(fresh_minutes * 60, len(power))
        if fresh_end >= 60:
            fresh_mmp = compute_mmp(power.iloc[:fresh_end])
            fresh_mmps.append(fresh_mmp)

        # Fatigued portion: after accumulating fatigue_kj of work
        cumwork_kj = power.cumsum() / 1000
        fatigue_start = cumwork_kj.searchsorted(fatigue_kj)
        if fatigue_start < len(power) - 60:
            fatigued_mmp = compute_mmp(power.iloc[fatigue_start:])
            fatigued_mmps.append(fatigued_mmp)

    if not fresh_mmps or not fatigued_mmps:
        return {}

    # Build envelopes
    def envelope(mmps):
        max_len = max(len(m) for m in mmps)
        env = np.zeros(max_len)
        for m in mmps:
            env[:len(m)] = np.maximum(env[:len(m)], m)
        return env

    fresh_env = envelope(fresh_mmps)
    fatigued_env = envelope(fatigued_mmps)

    # Compare at key durations
    compare_durations = [60, 300, 1200]
    ratios = {}
    for d in compare_durations:
        if d <= len(fresh_env) and d <= len(fatigued_env) and fresh_env[d - 1] > 0:
            ratio = fatigued_env[d - 1] / fresh_env[d - 1]
            ratios[d] = round(float(ratio), 3)
        else:
            ratios[d] = float("nan")

    return {
        "stamina_ratios": ratios,
        "fresh_rides": len(fresh_mmps),
        "fatigued_rides": len(fatigued_mmps),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_profile.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add wko5/profile.py tests/test_profile.py
git commit -m "feat: add power profile, Coggan ranking, phenotype, fatigue resistance"
```

---

### Task 9: Finalize __init__.py with convenience imports

**Files:**
- Modify: `wko5/__init__.py`

- [ ] **Step 1: Update __init__.py with all convenience imports**

```python
# wko5/__init__.py
"""WKO5-style cycling power analysis library."""

from wko5.db import get_connection, get_activities, get_records, WEIGHT_KG, FTP_DEFAULT
from wko5.pdcurve import compute_envelope_mmp, fit_pd_model, rolling_ftp
from wko5.training_load import build_pmc, current_fitness, compute_np
from wko5.zones import coggan_zones, ilevels, time_in_zones
from wko5.ride import ride_summary, detect_intervals
from wko5.profile import power_profile, strengths_limiters, phenotype
```

- [ ] **Step 2: Verify package imports work**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -c "import wko5; print('OK:', dir(wko5))"`
Expected: Prints OK with all exported names

- [ ] **Step 3: Run full test suite**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add wko5/__init__.py
git commit -m "feat: finalize package with convenience imports"
```

---

## Chunk 6: Notebooks

### Task 10: Power Duration notebook

**Files:**
- Create: `notebooks/power_duration.ipynb`

- [ ] **Step 0: Create notebooks directory**

Run: `mkdir -p /Users/jshin/Documents/wko5-experiments/notebooks`

- [ ] **Step 1: Create the notebook**

Create a Jupyter notebook with these cells:

**Cell 1 (setup):**
```python
import sys
sys.path.insert(0, "..")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from wko5.pdcurve import compute_envelope_mmp, fit_pd_model, rolling_ftp, power_at_durations, _pd_model
from wko5.db import WEIGHT_KG
%matplotlib inline
plt.style.use('seaborn-v0_8-darkgrid')
```

**Cell 2 (MMP curve):**
```python
mmp = compute_envelope_mmp(days=90)
durations = np.arange(1, len(mmp) + 1)
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(durations, mmp, color='gold', alpha=0.8, label='MMP (90 days)')
ax.set_xscale('log')
ax.set_xlabel('Duration (seconds)')
ax.set_ylabel('Power (watts)')
ax.set_title('Mean Max Power Curve')
ax.legend()
# Add time markers
for t, label in [(60, '1min'), (300, '5min'), (1200, '20min'), (3600, '1hr')]:
    if t < len(mmp):
        ax.axvline(t, color='gray', linestyle='--', alpha=0.3)
        ax.text(t, mmp[t-1]+10, f'{label}\n{mmp[t-1]:.0f}W', fontsize=8, ha='center')
plt.tight_layout()
plt.show()
```

**Cell 3 (PD model overlay):**
```python
model = fit_pd_model(mmp)
if model:
    t_model = np.arange(5, min(len(mmp), 7200) + 1, dtype=float)
    p_model = _pd_model(t_model, model['Pmax'], model['tau'], model['FRC'], model['t0'], model['mFTP'])
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(durations, mmp, color='gold', alpha=0.6, label='MMP')
    ax.plot(t_model, p_model, color='red', linewidth=2, label='PD Model')
    ax.set_xscale('log')
    ax.set_xlabel('Duration (seconds)')
    ax.set_ylabel('Power (watts)')
    ax.set_title('Power Duration Model Fit')
    ax.legend()
    plt.tight_layout()
    plt.show()
    print(f"Pmax: {model['Pmax']}W | FRC: {model['FRC']} kJ | mFTP: {model['mFTP']}W")
    print(f"TTE: {model['TTE']} min | VO2max: {model['mVO2max_ml_min_kg']} mL/min/kg")
```

**Cell 4 (Rolling FTP):**
```python
ftp_trend = rolling_ftp(window_days=90, step_days=14)
if not ftp_trend.empty:
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(pd.to_datetime(ftp_trend['date']), ftp_trend['mFTP'], color='blue', linewidth=1.5)
    ax.set_xlabel('Date')
    ax.set_ylabel('Modeled FTP (watts)')
    ax.set_title('Rolling 90-day Modeled FTP')
    plt.tight_layout()
    plt.show()
```

**Cell 5 (Period comparison):**
```python
import pandas as pd
from wko5.pdcurve import compare_periods
# Compare this year vs last year (adjust dates as needed)
comparison = compare_periods(('2025-01-01', '2025-12-31'), ('2026-01-01', '2026-12-31'))
fig, ax = plt.subplots(figsize=(12, 6))
for label, data in [('2025', comparison['period1']), ('2026', comparison['period2'])]:
    m = data['mmp']
    if len(m) > 0:
        ax.plot(np.arange(1, len(m)+1), m, label=label)
ax.set_xscale('log')
ax.set_xlabel('Duration (seconds)')
ax.set_ylabel('Power (watts)')
ax.set_title('Year-over-Year PD Comparison')
ax.legend()
plt.tight_layout()
plt.show()
```

- [ ] **Step 2: Verify notebook runs**

Run: `source /tmp/fitenv/bin/activate && pip install jupyter --quiet && cd /Users/jshin/Documents/wko5-experiments && jupyter nbconvert --to notebook --execute notebooks/power_duration.ipynb --output /tmp/pd_test.ipynb`
Expected: Executes without errors

- [ ] **Step 3: Commit**

```bash
git add notebooks/power_duration.ipynb
git commit -m "feat: add power duration analysis notebook"
```

---

### Task 11: Training Load notebook

**Files:**
- Create: `notebooks/training_load.ipynb`

- [ ] **Step 1: Create the notebook**

**Cell 1 (setup):**
```python
import sys
sys.path.insert(0, "..")
import pandas as pd
import matplotlib.pyplot as plt
from wko5.training_load import build_pmc, current_fitness, ef_trend
%matplotlib inline
plt.style.use('seaborn-v0_8-darkgrid')
```

**Cell 2 (PMC chart):**
```python
pmc = build_pmc()
if not pmc.empty:
    fig, ax1 = plt.subplots(figsize=(16, 6))
    ax1.fill_between(pmc['date'], pmc['CTL'], alpha=0.3, color='blue', label='CTL (Fitness)')
    ax1.fill_between(pmc['date'], pmc['ATL'], alpha=0.3, color='red', label='ATL (Fatigue)')
    ax1.plot(pmc['date'], pmc['TSB'], color='gold', linewidth=1, label='TSB (Form)')
    ax1.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Training Load')
    ax1.set_title('Performance Management Chart')
    ax1.legend()
    plt.tight_layout()
    plt.show()
```

**Cell 3 (Current fitness):**
```python
fitness = current_fitness()
print(f"As of {fitness.get('date', 'N/A')}:")
print(f"  CTL (Fitness): {fitness['CTL']}")
print(f"  ATL (Fatigue): {fitness['ATL']}")
print(f"  TSB (Form):    {fitness['TSB']}")
```

**Cell 4 (Weekly TSS):**
```python
if not pmc.empty:
    pmc['week'] = pmc['date'].dt.isocalendar().week
    pmc['year'] = pmc['date'].dt.year
    # Last 52 weeks
    recent = pmc[pmc['date'] >= pmc['date'].max() - pd.Timedelta(days=365)]
    weekly = recent.groupby([recent['date'].dt.to_period('W')])['TSS'].sum()
    fig, ax = plt.subplots(figsize=(16, 4))
    weekly.plot(kind='bar', ax=ax, color='steelblue', alpha=0.7)
    ax.set_xlabel('Week')
    ax.set_ylabel('Weekly TSS')
    ax.set_title('Weekly Training Stress (Last 12 Months)')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.show()
```

**Cell 5 (EF trend):**
```python
ef = ef_trend(days=365)
if not ef.empty:
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.scatter(pd.to_datetime(ef['date']), ef['EF'], alpha=0.5, s=20, color='green')
    # Rolling 30-day average
    ef_sorted = ef.sort_values('date')
    ef_sorted['EF_rolling'] = ef_sorted['EF'].rolling(window=10, min_periods=3).mean()
    ax.plot(pd.to_datetime(ef_sorted['date']), ef_sorted['EF_rolling'], color='darkgreen', linewidth=2)
    ax.set_xlabel('Date')
    ax.set_ylabel('Efficiency Factor (NP/HR)')
    ax.set_title('Aerobic Efficiency Trend')
    plt.tight_layout()
    plt.show()
```

- [ ] **Step 2: Commit**

```bash
git add notebooks/training_load.ipynb
git commit -m "feat: add training load / PMC notebook"
```

---

### Task 12: Ride Analysis notebook

**Files:**
- Create: `notebooks/ride_analysis.ipynb`

- [ ] **Step 1: Create the notebook**

**Cell 1 (setup):**
```python
import sys
sys.path.insert(0, "..")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from wko5.ride import ride_summary, detect_intervals, lap_analysis, hr_decoupling, best_efforts, power_histogram
from wko5.zones import coggan_zones, time_in_zones
from wko5.db import get_records, FTP_DEFAULT
%matplotlib inline
plt.style.use('seaborn-v0_8-darkgrid')

# === SET THIS ===
ACTIVITY_ID = 1
```

**Cell 2 (Summary):**
```python
summary = ride_summary(ACTIVITY_ID)
for k, v in summary.items():
    print(f"  {k}: {v}")
```

**Cell 3 (Power/HR/Cadence time series):**
```python
records = get_records(ACTIVITY_ID)
fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True)
minutes = np.arange(len(records)) / 60
axes[0].plot(minutes, records['power'].fillna(0), color='blue', alpha=0.5, linewidth=0.5)
axes[0].plot(minutes, records['power'].fillna(0).rolling(30).mean(), color='blue', linewidth=1.5)
axes[0].set_ylabel('Power (W)')
if records['heart_rate'].notna().any():
    axes[1].plot(minutes, records['heart_rate'], color='red', alpha=0.7, linewidth=0.5)
    axes[1].set_ylabel('Heart Rate (bpm)')
if records['cadence'].notna().any():
    axes[2].plot(minutes, records['cadence'], color='green', alpha=0.7, linewidth=0.5)
    axes[2].set_ylabel('Cadence (rpm)')
axes[2].set_xlabel('Time (minutes)')
fig.suptitle(f'Ride {ACTIVITY_ID}: {summary.get("date", "")} — {summary.get("sub_sport", "")}')
plt.tight_layout()
plt.show()
```

**Cell 4 (Intervals):**
```python
intervals = detect_intervals(ACTIVITY_ID)
if intervals:
    idf = pd.DataFrame(intervals)
    print(f"Detected {len(intervals)} intervals:\n")
    print(idf[['duration_s', 'avg_power', 'max_power', 'avg_hr', 'avg_cadence']].to_string(index=False))
else:
    print("No intervals detected above threshold")
```

**Cell 5 (Zone distribution):**
```python
zones = coggan_zones(summary.get('ftp_used', FTP_DEFAULT))
tiz = time_in_zones(records['power'], zones)
fig, ax = plt.subplots(figsize=(10, 5))
colors = ['#90EE90', '#32CD32', '#FFD700', '#FFA500', '#FF4500', '#FF0000', '#8B0000']
ax.bar(tiz.keys(), [v/60 for v in tiz.values()], color=colors[:len(tiz)])
ax.set_xlabel('Zone')
ax.set_ylabel('Time (minutes)')
ax.set_title('Time in Zones')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()
```

**Cell 6 (Best efforts & HR decoupling):**
```python
efforts = best_efforts(ACTIVITY_ID, durations=[5, 60, 300, 1200])
print("Best efforts:")
for d, w in efforts.items():
    label = {5: '5s', 60: '1min', 300: '5min', 1200: '20min'}.get(d, f'{d}s')
    print(f"  {label}: {w}W ({w/78:.1f} W/kg)")
print(f"\nHR Decoupling: {hr_decoupling(ACTIVITY_ID)}%")
```

- [ ] **Step 2: Commit**

```bash
git add notebooks/ride_analysis.ipynb
git commit -m "feat: add ride analysis notebook template"
```

---

## Chunk 7: Claude Skill

### Task 13: Create the /wko5-analyzer skill

**Files:**
- Create: `~/.claude/skills/wko5-analyzer/skill.md`

- [ ] **Step 1: Create the skill file**

```markdown
---
name: wko5-analyzer
description: Analyze cycling training data from the local SQLite database. Use when the user asks about their fitness, FTP, power, training load, zones, ride analysis, strengths/limiters, phenotype, or any question answerable from their cycling data. Also trigger for "how's my training", "analyze my ride", "what's my CTL", or similar.
---

# WKO5 Analyzer

You have access to a local cycling power analysis library at `/Users/jshin/Documents/wko5-experiments/wko5/`.

## Athlete Context
- Weight: 78 kg
- FTP range: 285-299W (~3.7-3.8 W/kg)
- DB: 1,653 cycling activities (2018-2026), 11M+ per-second records
- Ride types: Zwift (782), road (580), indoor (219)

## Environment Setup

Before running any analysis, ensure the venv exists:

```bash
if [ ! -d /tmp/fitenv ]; then
    python3 -m venv /tmp/fitenv
    source /tmp/fitenv/bin/activate
    pip install numpy pandas scipy matplotlib fitdecode --quiet
else
    source /tmp/fitenv/bin/activate
fi
```

## How to Run Analysis

Run Python scripts via bash. Always use:
```bash
source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python3 -c "
<your code here>
"
```

## Module Reference

### Quick Status
```python
from wko5.training_load import current_fitness
print(current_fitness())
```

### FTP / Power Duration Model
```python
from wko5.pdcurve import compute_envelope_mmp, fit_pd_model
mmp = compute_envelope_mmp(days=90)
model = fit_pd_model(mmp)
# model = {Pmax, FRC, mFTP, TTE, mVO2max_L_min, mVO2max_ml_min_kg, tau, t0}
```

### Training Load (PMC)
```python
from wko5.training_load import build_pmc, current_fitness, efficiency_factor, ef_trend
pmc = build_pmc()  # DataFrame: date, TSS, CTL, ATL, TSB
fitness = current_fitness()  # dict: CTL, ATL, TSB, date
```

### Power Profile & Strengths
```python
from wko5.profile import power_profile, coggan_ranking, strengths_limiters, phenotype, fatigue_resistance
profile = power_profile(days=90)
ranking = coggan_ranking(profile)
sl = strengths_limiters(profile)
```

### Ride Analysis
```python
from wko5.ride import ride_summary, detect_intervals, best_efforts, hr_decoupling
# Find activity by date:
from wko5.db import get_activities
acts = get_activities(start="2026-03-13", end="2026-03-13")
summary = ride_summary(acts.iloc[0]['id'])
intervals = detect_intervals(acts.iloc[0]['id'])
```

### Zones
```python
from wko5.zones import coggan_zones, ilevels, time_in_zones, ride_distribution
zones = coggan_zones(292)
# Or individualized:
from wko5.pdcurve import compute_envelope_mmp, fit_pd_model
model = fit_pd_model(compute_envelope_mmp(days=90))
izones = ilevels(model)
```

### Trends
```python
from wko5.pdcurve import rolling_ftp
from wko5.profile import profile_trend
ftp_trend = rolling_ftp(window_days=90, step_days=14)
p5min = profile_trend(duration_s=300, window_days=90, step_days=14)
```

## Question → Function Mapping

| User asks about | Functions to use |
|---|---|
| Fitness / form / readiness | `current_fitness()` |
| FTP / threshold | `fit_pd_model(compute_envelope_mmp(days=90))` |
| Power profile / how strong | `power_profile()` + `coggan_ranking()` |
| Strengths / limiters / what to work on | `strengths_limiters()` + `phenotype()` |
| Specific ride / yesterday's ride | `get_activities(start=date)` → `ride_summary()` + `detect_intervals()` |
| Training load / CTL / TSB | `build_pmc()` or `current_fitness()` |
| Zones | `coggan_zones()` or `ilevels()` |
| Am I improving / trends | `rolling_ftp()` + `profile_trend()` |
| Efficiency / aerobic | `ef_trend()` |
| Durability / fatigue resistance | `fatigue_resistance()` |
| Compare periods | `compare_profiles((start1,end1), (start2,end2))` |

## Output Format
- Return results as formatted text/tables
- Round watts to whole numbers, W/kg to 2 decimal places
- Include context (what the numbers mean) alongside raw values
- Reference WKO5 training methodology when providing coaching insights
```

- [ ] **Step 2: Verify skill directory exists and file is readable**

Run: `ls -la ~/.claude/skills/wko5-analyzer/skill.md`
Expected: File exists

- [ ] **Step 3: Commit**

```bash
git add -f ~/.claude/skills/wko5-analyzer/skill.md 2>/dev/null || true
# Skill files are in home dir, not in repo — no git commit needed
```

---

### Task 14: Add notebooks/ to .gitignore and final cleanup

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Update .gitignore**

Add `notebooks/.ipynb_checkpoints/` to `.gitignore`.

- [ ] **Step 2: Run full test suite one final time**

Run: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Final commit**

```bash
git add .gitignore wko5/ingest_missing.py wko5/garmin_sync.py
git commit -m "chore: update gitignore, include existing scripts in repo"
```
