# Phase 4: Training Block Analysis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build training block analysis with TrainingPeaks enrichment — ingest coach-prescribed workouts, compute block-level stats (volume, intensity distribution, power changes), auto-detect training phases, compare blocks, and project feasibility for target events.

**Architecture:** Two new modules. `tp_ingest.py` ingests the TrainingPeaks CSV into a `tp_workouts` table and joins with existing activities by date. `blocks.py` computes block-level statistics, detects training phases, compares blocks, and projects feasibility. A `training_phases` table stores both auto-detected and coach-assigned phases.

**Tech Stack:** Python 3, pandas, numpy, SQLite

**Existing:** `wko5/` package with 140 passing tests. DB has 1,653 Garmin activities (2018-2026). TrainingPeaks CSV has 275 workouts (2025-03 to 2026-03) with coach prescriptions, athlete comments, RPE, zone breakdowns.

**Python env:** `/tmp/fitenv/`

**Test command:** `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && pytest tests/ -v`

---

## File Structure

```
wko5/
  tp_ingest.py     # TrainingPeaks CSV ingestion, date-matching to activities
  blocks.py        # Block stats, phase detection, block comparison, feasibility
```

- `tp_ingest.py` — ingest TrainingPeaks CSV → `tp_workouts` table, match to activities by date
- `blocks.py` — given date ranges → volume/intensity/power stats, phase classification, block diffs, CTL projection

---

## Task 1: TrainingPeaks ingestion (`tp_ingest.py`)

**Files:**
- Create: `wko5/tp_ingest.py`
- Create: `tests/test_tp_ingest.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_tp_ingest.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlite3
import pandas as pd
from wko5.tp_ingest import ingest_tp_csv, get_tp_workouts, match_tp_to_activities
from wko5.db import get_connection


def test_ingest_tp_csv():
    """Should create tp_workouts table and populate it."""
    csv_path = "/Users/jshin/Downloads/workouts.csv"
    if not os.path.exists(csv_path):
        return

    count = ingest_tp_csv(csv_path)
    assert count > 200


def test_ingest_multiple_csvs():
    """Should handle multiple CSV files and deduplicate."""
    paths = [
        "/Users/jshin/Downloads/workouts-2.csv",
        "/Users/jshin/Downloads/workouts.csv",
    ]
    if not all(os.path.exists(p) for p in paths):
        return

    count = ingest_tp_csv(paths)
    assert count > 500  # ~620 combined minus overlap

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tp_workouts")
    db_count = cursor.fetchone()[0]
    conn.close()
    assert db_count == count


def test_get_tp_workouts():
    """Should return workouts as DataFrame."""
    workouts = get_tp_workouts()
    if workouts.empty:
        return

    assert "title" in workouts.columns
    assert "workout_day" in workouts.columns
    assert "workout_description" in workouts.columns
    assert "coach_comments" in workouts.columns
    assert "athlete_comments" in workouts.columns
    assert "rpe" in workouts.columns


def test_get_tp_workouts_date_filter():
    """Should filter by date range."""
    all_workouts = get_tp_workouts()
    if all_workouts.empty:
        return

    filtered = get_tp_workouts(start="2025-06-01", end="2025-06-30")
    assert len(filtered) <= len(all_workouts)


def test_match_tp_to_activities():
    """Should match TP workouts to Garmin activities by date."""
    matched = match_tp_to_activities()
    if matched.empty:
        return

    assert "activity_id" in matched.columns
    assert "tp_title" in matched.columns
    assert "tp_description" in matched.columns
    # Most workouts should match (same athlete, same dates)
    total_tp = len(get_tp_workouts())
    match_rate = len(matched[matched["activity_id"].notna()]) / total_tp if total_tp > 0 else 0
    assert match_rate > 0.5, f"Only {match_rate:.0%} of TP workouts matched to activities"


def test_tp_workout_categories():
    """Workout titles should be categorizable."""
    from wko5.tp_ingest import categorize_workout
    assert categorize_workout("Easy") == "recovery"
    assert categorize_workout("Recovery") == "recovery"
    assert categorize_workout("Endurance") == "endurance"
    assert categorize_workout("Endurance + Sprints") == "endurance"
    assert categorize_workout("Indoor VO2s 7x3") == "high_intensity"
    assert categorize_workout("FTP Test") == "test"
    assert categorize_workout("Strength") == "strength"
    assert categorize_workout("Sweet Spot 3x15") == "threshold"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_tp_ingest.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement tp_ingest.py**

```python
# wko5/tp_ingest.py
"""TrainingPeaks CSV ingestion and activity matching."""

import logging
import os
import re

import pandas as pd

from wko5.db import get_connection, get_activities

logger = logging.getLogger(__name__)

TP_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS tp_workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_day TEXT NOT NULL,
    title TEXT,
    workout_type TEXT,
    workout_description TEXT,
    planned_duration_hr REAL,
    coach_comments TEXT,
    athlete_comments TEXT,
    actual_duration_hr REAL,
    distance_m REAL,
    power_avg REAL,
    power_max REAL,
    energy_kj REAL,
    intensity_factor REAL,
    tss REAL,
    rpe INTEGER,
    feeling INTEGER,
    hr_zone1_min REAL, hr_zone2_min REAL, hr_zone3_min REAL,
    hr_zone4_min REAL, hr_zone5_min REAL,
    pwr_zone1_min REAL, pwr_zone2_min REAL, pwr_zone3_min REAL,
    pwr_zone4_min REAL, pwr_zone5_min REAL, pwr_zone6_min REAL,
    pwr_zone7_min REAL,
    category TEXT,
    activity_id INTEGER,
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);
"""

# Workout title → category mapping
CATEGORY_PATTERNS = [
    (r"(?i)(easy|recovery|rest)", "recovery"),
    (r"(?i)(endurance|long ride|base)", "endurance"),
    (r"(?i)(sweet\s*spot|tempo|ss\s)", "threshold"),
    (r"(?i)(vo2|anaerobic|interval|tabata)", "high_intensity"),
    (r"(?i)(ftp\s*test|ramp\s*test|tt|time\s*trial|test)", "test"),
    (r"(?i)(sprint|neuromuscular|snap)", "sprint"),
    (r"(?i)(strength|gym|weight|core|yoga|stretch)", "strength"),
]


def categorize_workout(title):
    """Categorize a workout by its title."""
    if not title:
        return "unknown"
    for pattern, category in CATEGORY_PATTERNS:
        if re.search(pattern, title):
            return category
    return "endurance"  # default for unlabeled bike rides


def _safe_float(val):
    """Convert to float, handling empty strings and None."""
    if val is None or val == "" or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    """Convert to int, handling empty strings and None."""
    f = _safe_float(val)
    return int(f) if f is not None else None


def ingest_tp_csv(csv_path):
    """Ingest one or more TrainingPeaks workout CSVs into the database.

    Args:
        csv_path: single path string or list of paths

    Returns number of rows ingested.
    """
    if isinstance(csv_path, (list, tuple)):
        dfs = [pd.read_csv(p) for p in csv_path]
        df = pd.concat(dfs, ignore_index=True)
        # Deduplicate by date + title
        df = df.drop_duplicates(subset=["WorkoutDay", "Title"], keep="last")
    else:
        df = pd.read_csv(csv_path)
    conn = get_connection()
    conn.execute(TP_TABLE_DDL)

    # Clear existing data (re-ingest is idempotent)
    conn.execute("DELETE FROM tp_workouts")

    count = 0
    for _, row in df.iterrows():
        title = row.get("Title", "")
        category = categorize_workout(title)

        conn.execute("""
            INSERT INTO tp_workouts (
                workout_day, title, workout_type, workout_description,
                planned_duration_hr, coach_comments, athlete_comments,
                actual_duration_hr, distance_m, power_avg, power_max, energy_kj,
                intensity_factor, tss, rpe, feeling,
                hr_zone1_min, hr_zone2_min, hr_zone3_min, hr_zone4_min, hr_zone5_min,
                pwr_zone1_min, pwr_zone2_min, pwr_zone3_min, pwr_zone4_min,
                pwr_zone5_min, pwr_zone6_min, pwr_zone7_min,
                category
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            row.get("WorkoutDay"),
            title,
            row.get("WorkoutType"),
            row.get("WorkoutDescription"),
            _safe_float(row.get("PlannedDuration")),
            row.get("CoachComments"),
            row.get("AthleteComments"),
            _safe_float(row.get("TimeTotalInHours")),
            _safe_float(row.get("DistanceInMeters")),
            _safe_float(row.get("PowerAverage")),
            _safe_float(row.get("PowerMax")),
            _safe_float(row.get("Energy")),
            _safe_float(row.get("IF")),
            _safe_float(row.get("TSS")),
            _safe_int(row.get("Rpe")),
            _safe_int(row.get("Feeling")),
            _safe_float(row.get("HRZone1Minutes")),
            _safe_float(row.get("HRZone2Minutes")),
            _safe_float(row.get("HRZone3Minutes")),
            _safe_float(row.get("HRZone4Minutes")),
            _safe_float(row.get("HRZone5Minutes")),
            _safe_float(row.get("PWRZone1Minutes")),
            _safe_float(row.get("PWRZone2Minutes")),
            _safe_float(row.get("PWRZone3Minutes")),
            _safe_float(row.get("PWRZone4Minutes")),
            _safe_float(row.get("PWRZone5Minutes")),
            _safe_float(row.get("PWRZone6Minutes")),
            _safe_float(row.get("PWRZone7Minutes")),
            category,
        ))
        count += 1

    conn.commit()

    # Match to activities by date
    _match_activities(conn)

    conn.close()
    logger.info(f"Ingested {count} TrainingPeaks workouts")
    return count


def _match_activities(conn):
    """Match tp_workouts to activities by date and workout type (Bike)."""
    conn.execute("""
        UPDATE tp_workouts SET activity_id = (
            SELECT a.id FROM activities a
            WHERE date(a.start_time) = tp_workouts.workout_day
            AND tp_workouts.workout_type = 'Bike'
            ORDER BY a.total_timer_time DESC
            LIMIT 1
        )
        WHERE workout_type = 'Bike'
    """)
    conn.commit()

    # Count matches
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tp_workouts WHERE activity_id IS NOT NULL")
    matched = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tp_workouts WHERE workout_type = 'Bike'")
    total_bike = cursor.fetchone()[0]
    logger.info(f"Matched {matched}/{total_bike} bike workouts to activities")


def get_tp_workouts(start=None, end=None):
    """Get TrainingPeaks workouts as DataFrame, optionally filtered by date."""
    conn = get_connection()

    # Ensure table exists
    conn.execute(TP_TABLE_DDL)

    query = "SELECT * FROM tp_workouts WHERE 1=1"
    params = []
    if start:
        query += " AND workout_day >= ?"
        params.append(start)
    if end:
        query += " AND workout_day <= ?"
        params.append(end)
    query += " ORDER BY workout_day"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def match_tp_to_activities(start=None, end=None):
    """Get joined view of TP workouts matched to activities."""
    conn = get_connection()
    conn.execute(TP_TABLE_DDL)

    query = """
        SELECT
            tp.workout_day,
            tp.title AS tp_title,
            tp.workout_description AS tp_description,
            tp.planned_duration_hr AS tp_planned_hr,
            tp.coach_comments,
            tp.athlete_comments,
            tp.category AS tp_category,
            tp.rpe,
            tp.feeling,
            tp.activity_id,
            a.start_time,
            a.total_timer_time,
            a.total_distance,
            a.avg_power,
            a.normalized_power,
            a.intensity_factor AS garmin_if,
            a.training_stress_score AS garmin_tss,
            a.total_ascent,
            a.sub_sport
        FROM tp_workouts tp
        LEFT JOIN activities a ON tp.activity_id = a.id
        WHERE 1=1
    """
    params = []
    if start:
        query += " AND tp.workout_day >= ?"
        params.append(start)
    if end:
        query += " AND tp.workout_day <= ?"
        params.append(end)
    query += " ORDER BY tp.workout_day"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_tp_ingest.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`

- [ ] **Step 6: Commit**

```bash
git add wko5/tp_ingest.py tests/test_tp_ingest.py
git commit -m "feat: add TrainingPeaks CSV ingestion with activity matching"
```

---

## Task 2: Training block analysis (`blocks.py`)

**Files:**
- Create: `wko5/blocks.py`
- Create: `tests/test_blocks.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_blocks.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from wko5.blocks import (
    block_stats, weekly_summary, detect_phase, compare_blocks,
    feasibility_projection, set_training_phase, get_training_phases,
)


def test_block_stats_basic():
    """Block stats should return volume, intensity, and power metrics."""
    result = block_stats("2025-01-01", "2025-03-31")
    assert "volume" in result
    assert "intensity" in result
    assert "power" in result
    assert result["volume"]["ride_count"] > 0
    assert result["volume"]["hours"] > 0
    assert result["volume"]["km"] > 0
    assert result["volume"]["kj"] > 0


def test_block_stats_volume():
    """Volume metrics should be reasonable."""
    result = block_stats("2025-01-01", "2025-01-31")
    vol = result["volume"]
    assert 0 < vol["hours"] < 200
    assert 0 < vol["ride_count"] < 60
    assert "elevation_m" in vol


def test_block_stats_intensity():
    """Intensity distribution should sum to ~100%."""
    result = block_stats("2025-06-01", "2025-06-30")
    intensity = result["intensity"]
    if "seiler_zone1_pct" in intensity:
        total = intensity["seiler_zone1_pct"] + intensity["seiler_zone2_pct"] + intensity["seiler_zone3_pct"]
        assert 90 < total < 110, f"Seiler zones sum to {total}%"


def test_block_stats_power():
    """Power metrics should include key durations."""
    result = block_stats("2025-06-01", "2025-08-31")
    power = result["power"]
    assert "avg_power" in power
    assert "avg_np" in power
    assert "avg_if" in power
    assert "avg_tss_per_ride" in power


def test_weekly_summary():
    """Weekly summary should return a DataFrame."""
    df = weekly_summary("2025-06-01", "2025-08-31")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "week" in df.columns
    assert "hours" in df.columns
    assert "tss" in df.columns
    assert "ride_count" in df.columns


def test_detect_phase():
    """Phase detection should return a valid phase."""
    phase = detect_phase("2025-06-01", "2025-06-30")
    assert phase["phase"] in ("base", "build", "peak", "recovery", "unknown")
    assert 0 < phase["confidence"] <= 1.0


def test_compare_blocks():
    """Block comparison should show differences."""
    diff = compare_blocks(
        ("2025-01-01", "2025-03-31"),
        ("2025-04-01", "2025-06-30"),
    )
    assert "volume_change" in diff
    assert "intensity_change" in diff
    assert "power_change" in diff


def test_set_and_get_training_phase():
    """Should store and retrieve coach-assigned phases."""
    set_training_phase("2025-07-01", "2025-08-31", "build", source="coach", notes="targeting fall event")
    phases = get_training_phases("2025-01-01", "2025-12-31")
    assert len(phases) > 0
    coach_phases = [p for p in phases if p["source"] == "coach"]
    assert any(p["phase"] == "build" for p in coach_phases)


def test_feasibility_projection():
    """Feasibility should estimate if CTL target is reachable."""
    result = feasibility_projection(target_ctl=80, weeks_available=12)
    assert "current_ctl" in result
    assert "target_ctl" in result
    assert "feasible" in result
    assert "required_ramp_rate" in result
    assert isinstance(result["feasible"], bool)


def test_block_stats_with_tp_enrichment():
    """Block stats should include TP data when available."""
    result = block_stats("2025-06-01", "2025-06-30")
    if "tp" in result:
        tp = result["tp"]
        assert "prescribed_count" in tp
        assert "compliance_rate" in tp
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_blocks.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement blocks.py**

```python
# wko5/blocks.py
"""Training block analysis — stats, phase detection, comparison, feasibility."""

import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from wko5.db import get_connection, get_activities
from wko5.training_load import build_pmc, current_fitness
from wko5.config import get_config

logger = logging.getLogger(__name__)

PHASES_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS training_phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    phase TEXT NOT NULL,
    source TEXT DEFAULT 'auto',
    notes TEXT,
    confidence REAL DEFAULT 1.0
);
"""


def block_stats(start, end):
    """Compute training block statistics for a date range.

    Returns dict with volume, intensity, power, and optional TP enrichment.
    """
    activities = get_activities(start=start, end=end)

    if activities.empty:
        return {"volume": {}, "intensity": {}, "power": {}, "rides": 0}

    # Filter to cycling only
    cycling = activities[activities["sport"].str.lower().isin(["cycling", "6"])]
    if cycling.empty:
        cycling = activities  # fallback if sport field is inconsistent

    # Volume
    hours = cycling["total_timer_time"].sum() / 3600
    km = cycling["total_distance"].sum() / 1000
    kj = cycling["total_work"].sum() / 1000 if "total_work" in cycling.columns else 0
    elevation = cycling["total_ascent"].sum()
    long_rides = len(cycling[cycling["total_timer_time"] > 10800])  # >3h

    volume = {
        "ride_count": len(cycling),
        "hours": round(hours, 1),
        "km": round(km, 0),
        "kj": round(kj, 0),
        "elevation_m": round(elevation, 0),
        "long_ride_count": long_rides,
        "avg_hours_per_ride": round(hours / len(cycling), 2) if len(cycling) > 0 else 0,
    }

    # Intensity distribution (Seiler 3-zone using IF)
    # Zone 1: IF < 0.75 (below LT1/VT1)
    # Zone 2: 0.75 <= IF < 0.90 (between LT1 and LT2)
    # Zone 3: IF >= 0.90 (above LT2)
    if_values = cycling["intensity_factor"].dropna()
    if len(if_values) > 0:
        # Weight by duration
        durations = cycling.loc[if_values.index, "total_timer_time"].fillna(0)
        total_dur = durations.sum()

        z1_mask = if_values < 0.75
        z2_mask = (if_values >= 0.75) & (if_values < 0.90)
        z3_mask = if_values >= 0.90

        z1_pct = durations[z1_mask].sum() / total_dur * 100 if total_dur > 0 else 0
        z2_pct = durations[z2_mask].sum() / total_dur * 100 if total_dur > 0 else 0
        z3_pct = durations[z3_mask].sum() / total_dur * 100 if total_dur > 0 else 0

        intensity = {
            "seiler_zone1_pct": round(z1_pct, 1),
            "seiler_zone2_pct": round(z2_pct, 1),
            "seiler_zone3_pct": round(z3_pct, 1),
            "avg_if": round(float(if_values.mean()), 3),
            "max_if": round(float(if_values.max()), 3),
        }
    else:
        intensity = {}

    # Power metrics
    power = {}
    if "avg_power" in cycling.columns:
        ap = cycling["avg_power"].dropna()
        if len(ap) > 0:
            power["avg_power"] = round(float(ap.mean()), 0)

    if "normalized_power" in cycling.columns:
        np_vals = cycling["normalized_power"].dropna()
        if len(np_vals) > 0:
            power["avg_np"] = round(float(np_vals.mean()), 0)

    if len(if_values) > 0:
        power["avg_if"] = round(float(if_values.mean()), 3)

    tss_vals = cycling["training_stress_score"].dropna()
    if len(tss_vals) > 0:
        power["total_tss"] = round(float(tss_vals.sum()), 0)
        power["avg_tss_per_ride"] = round(float(tss_vals.mean()), 1)
        power["weekly_tss"] = round(float(tss_vals.sum()) / max(1, hours / 168 * 7), 0)

    result = {
        "start": start,
        "end": end,
        "volume": volume,
        "intensity": intensity,
        "power": power,
    }

    # TP enrichment if available
    try:
        from wko5.tp_ingest import get_tp_workouts
        tp = get_tp_workouts(start=start, end=end)
        if not tp.empty:
            bike_tp = tp[tp["workout_type"] == "Bike"]
            prescribed = len(bike_tp)
            executed = len(bike_tp[bike_tp["actual_duration_hr"].notna() & (bike_tp["actual_duration_hr"] > 0)])

            # Compliance: did planned duration match actual?
            has_both = bike_tp[bike_tp["planned_duration_hr"].notna() & bike_tp["actual_duration_hr"].notna()]
            if len(has_both) > 0:
                duration_compliance = (has_both["actual_duration_hr"] / has_both["planned_duration_hr"]).mean()
            else:
                duration_compliance = None

            # Category breakdown
            categories = bike_tp["category"].value_counts().to_dict()

            # RPE and feeling averages
            rpe_vals = bike_tp["rpe"].dropna()
            feeling_vals = bike_tp["feeling"].dropna()

            result["tp"] = {
                "prescribed_count": prescribed,
                "executed_count": executed,
                "compliance_rate": round(executed / prescribed, 2) if prescribed > 0 else None,
                "duration_compliance": round(float(duration_compliance), 2) if duration_compliance is not None else None,
                "categories": categories,
                "avg_rpe": round(float(rpe_vals.mean()), 1) if len(rpe_vals) > 0 else None,
                "avg_feeling": round(float(feeling_vals.mean()), 1) if len(feeling_vals) > 0 else None,
            }
    except Exception:
        pass  # TP data not available

    return result


def weekly_summary(start, end):
    """Compute weekly training summaries.

    Returns DataFrame with one row per week.
    """
    activities = get_activities(start=start, end=end)
    if activities.empty:
        return pd.DataFrame()

    activities = activities.copy()
    activities["date"] = pd.to_datetime(activities["start_time"], format="ISO8601", utc=True)
    activities["week"] = activities["date"].dt.isocalendar().week.astype(int)
    activities["year"] = activities["date"].dt.isocalendar().year.astype(int)
    activities["year_week"] = activities["year"].astype(str) + "-W" + activities["week"].astype(str).str.zfill(2)

    weekly = activities.groupby("year_week").agg(
        hours=("total_timer_time", lambda x: round(x.sum() / 3600, 1)),
        km=("total_distance", lambda x: round(x.sum() / 1000, 0)),
        tss=("training_stress_score", lambda x: round(x.sum(), 0)),
        ride_count=("id", "count"),
        avg_if=("intensity_factor", lambda x: round(x.mean(), 3) if x.notna().any() else None),
        elevation=("total_ascent", "sum"),
        avg_power=("avg_power", lambda x: round(x.mean(), 0) if x.notna().any() else None),
    ).reset_index()

    weekly.rename(columns={"year_week": "week"}, inplace=True)
    return weekly


def detect_phase(start, end):
    """Auto-detect training phase from intensity distribution and volume.

    Returns dict with phase, confidence, and reasoning.
    """
    stats = block_stats(start, end)
    vol = stats.get("volume", {})
    intensity = stats.get("intensity", {})

    if not vol or vol.get("ride_count", 0) < 3:
        return {"phase": "unknown", "confidence": 0.0, "reasoning": "Insufficient data"}

    hours_per_week = vol["hours"] / max(1, _weeks_in_range(start, end))
    z3_pct = intensity.get("seiler_zone3_pct", 0)
    z2_pct = intensity.get("seiler_zone2_pct", 0)
    avg_if = intensity.get("avg_if", 0)

    # Heuristic classification
    # Recovery: low volume, low intensity
    if hours_per_week < 4 and avg_if < 0.65:
        return {"phase": "recovery", "confidence": 0.8,
                "reasoning": f"Low volume ({hours_per_week:.0f}h/wk) and low intensity (IF={avg_if:.2f})"}

    # Base: high volume, low Zone 3
    if hours_per_week > 7 and z3_pct < 10:
        return {"phase": "base", "confidence": 0.7,
                "reasoning": f"High volume ({hours_per_week:.0f}h/wk) with only {z3_pct:.0f}% in Zone 3"}

    # Build: moderate volume, rising Zone 2-3
    if z2_pct + z3_pct > 20 and hours_per_week > 5:
        return {"phase": "build", "confidence": 0.6,
                "reasoning": f"Moderate volume ({hours_per_week:.0f}h/wk) with {z2_pct+z3_pct:.0f}% in Zone 2+3"}

    # Peak: reduced volume, high Zone 3
    if hours_per_week < 7 and z3_pct > 15:
        return {"phase": "peak", "confidence": 0.6,
                "reasoning": f"Reduced volume ({hours_per_week:.0f}h/wk) with high intensity ({z3_pct:.0f}% Zone 3)"}

    # Default to base/build blend
    return {"phase": "build", "confidence": 0.4,
            "reasoning": f"Mixed signals: {hours_per_week:.0f}h/wk, IF={avg_if:.2f}, Z3={z3_pct:.0f}%"}


def compare_blocks(block_a, block_b):
    """Compare two training blocks.

    Args:
        block_a: (start_date, end_date) tuple for first block
        block_b: (start_date, end_date) tuple for second block

    Returns dict with volume_change, intensity_change, power_change.
    """
    stats_a = block_stats(block_a[0], block_a[1])
    stats_b = block_stats(block_b[0], block_b[1])

    def _pct_change(a, b):
        if a and a != 0:
            return round((b - a) / abs(a) * 100, 1)
        return None

    def _diff(a, b):
        if a is not None and b is not None:
            return round(b - a, 1)
        return None

    vol_a = stats_a.get("volume", {})
    vol_b = stats_b.get("volume", {})
    int_a = stats_a.get("intensity", {})
    int_b = stats_b.get("intensity", {})
    pow_a = stats_a.get("power", {})
    pow_b = stats_b.get("power", {})

    return {
        "block_a": {"start": block_a[0], "end": block_a[1], "stats": stats_a},
        "block_b": {"start": block_b[0], "end": block_b[1], "stats": stats_b},
        "volume_change": {
            "hours_pct": _pct_change(vol_a.get("hours"), vol_b.get("hours")),
            "ride_count_diff": _diff(vol_a.get("ride_count"), vol_b.get("ride_count")),
            "km_pct": _pct_change(vol_a.get("km"), vol_b.get("km")),
            "elevation_pct": _pct_change(vol_a.get("elevation_m"), vol_b.get("elevation_m")),
        },
        "intensity_change": {
            "avg_if_diff": _diff(int_a.get("avg_if"), int_b.get("avg_if")),
            "zone3_pct_diff": _diff(int_a.get("seiler_zone3_pct"), int_b.get("seiler_zone3_pct")),
        },
        "power_change": {
            "avg_power_diff": _diff(pow_a.get("avg_power"), pow_b.get("avg_power")),
            "avg_np_diff": _diff(pow_a.get("avg_np"), pow_b.get("avg_np")),
            "weekly_tss_diff": _diff(pow_a.get("weekly_tss"), pow_b.get("weekly_tss")),
        },
    }


def set_training_phase(start_date, end_date, phase, source="user", notes=None, confidence=1.0):
    """Store a training phase (from coach or user)."""
    conn = get_connection()
    conn.execute(PHASES_TABLE_DDL)
    conn.execute("""
        INSERT INTO training_phases (start_date, end_date, phase, source, notes, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (start_date, end_date, phase, source, notes, confidence))
    conn.commit()
    conn.close()


def get_training_phases(start=None, end=None):
    """Get stored training phases, optionally filtered by date range."""
    conn = get_connection()
    conn.execute(PHASES_TABLE_DDL)

    query = "SELECT * FROM training_phases WHERE 1=1"
    params = []
    if start:
        query += " AND end_date >= ?"
        params.append(start)
    if end:
        query += " AND start_date <= ?"
        params.append(end)
    query += " ORDER BY start_date"

    cursor = conn.cursor()
    cursor.execute(query, params)
    columns = [desc[0] for desc in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return rows


def feasibility_projection(target_ctl, weeks_available, max_ramp_rate=7):
    """Project whether a CTL target is achievable.

    Args:
        target_ctl: desired CTL by event date
        weeks_available: weeks until event
        max_ramp_rate: maximum sustainable TSS/day/week ramp rate (default 7)

    Returns dict with current CTL, required ramp, feasibility.
    """
    fitness = current_fitness()
    current_ctl = fitness.get("CTL", 0)

    ctl_gap = target_ctl - current_ctl
    days_available = weeks_available * 7

    # CTL responds to daily TSS with ~42-day time constant
    # Rough approximation: to raise CTL by X in N days,
    # you need average daily TSS ≈ current_daily_TSS + X * (42/N) * correction
    # Simpler: CTL rises ~1 point per week at +7 TSS/day/week ramp
    required_ramp = ctl_gap / weeks_available if weeks_available > 0 else float("inf")

    feasible = required_ramp <= max_ramp_rate and ctl_gap >= 0
    if ctl_gap <= 0:
        feasible = True  # already at or above target

    return {
        "current_ctl": round(current_ctl, 1),
        "target_ctl": target_ctl,
        "ctl_gap": round(ctl_gap, 1),
        "weeks_available": weeks_available,
        "required_ramp_rate": round(required_ramp, 1),
        "max_sustainable_ramp": max_ramp_rate,
        "feasible": feasible,
        "margin_weeks": round((max_ramp_rate * weeks_available - ctl_gap) / max_ramp_rate, 1) if max_ramp_rate > 0 else 0,
    }


def _weeks_in_range(start, end):
    """Compute number of weeks between two date strings."""
    try:
        d1 = datetime.strptime(start, "%Y-%m-%d")
        d2 = datetime.strptime(end, "%Y-%m-%d")
        return max(1, (d2 - d1).days / 7)
    except (ValueError, TypeError):
        return 1
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_blocks.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`

- [ ] **Step 6: Commit**

```bash
git add wko5/blocks.py tests/test_blocks.py
git commit -m "feat: add training block analysis — stats, phase detection, block comparison, feasibility"
```

---

## Task 3: API endpoints + exports

**Files:**
- Modify: `wko5/api/routes.py`
- Modify: `wko5/__init__.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Add new routes**

Add to `wko5/api/routes.py`:

```python
from wko5.blocks import block_stats, weekly_summary, detect_phase, compare_blocks, feasibility_projection
from wko5.tp_ingest import ingest_tp_csv, get_tp_workouts

@router.get("/training-blocks", dependencies=[Depends(verify_token)])
def training_blocks(start: str = None, end: str = None):
    if not start:
        start = "2025-01-01"
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    result = block_stats(start, end)
    return _sanitize_nans(result)

@router.get("/weekly-summary", dependencies=[Depends(verify_token)])
def weekly_summary_endpoint(start: str = None, end: str = None):
    if not start:
        start = "2025-01-01"
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    from wko5.blocks import weekly_summary as ws
    df = ws(start, end)
    return _sanitize_nans(df.to_dict(orient="records"))

@router.get("/detect-phase", dependencies=[Depends(verify_token)])
def detect_phase_endpoint(start: str = "2025-01-01", end: str = None):
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    return detect_phase(start, end)

@router.get("/feasibility", dependencies=[Depends(verify_token)])
def feasibility(target_ctl: int = 80, weeks: int = 12):
    return feasibility_projection(target_ctl, weeks)
```

- [ ] **Step 2: Add test**

Add to `tests/test_api.py`:

```python
def test_training_blocks_with_auth():
    client, token = _get_client()
    response = client.get("/api/training-blocks?start=2025-06-01&end=2025-06-30",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "volume" in data
```

- [ ] **Step 3: Update package exports**

Add to `wko5/__init__.py`:
```python
from wko5.blocks import block_stats, weekly_summary, detect_phase, compare_blocks, feasibility_projection
from wko5.tp_ingest import ingest_tp_csv, get_tp_workouts, match_tp_to_activities
```

- [ ] **Step 4: Run full test suite**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -v`

- [ ] **Step 5: Commit and push**

```bash
git add wko5/api/routes.py wko5/__init__.py tests/test_api.py
git commit -m "feat: add training block API endpoints and package exports"
```
