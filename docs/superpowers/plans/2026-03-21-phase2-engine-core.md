# Phase 2: Engine Core — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the novel analytical core — segment decomposition from altitude/GPS data, empirical durability model fitted from 8 years of ride history, fatigued PD curves, and FRC budget tracking across sequential segments.

**Architecture:** Three new modules (`segments.py`, `physics.py`, `durability.py`) that build on the existing `wko5/` library. Segments decompose routes into physiological demands. The durability model fits an empirical decay function from long rides. The fatigued PD curve composes the fresh PD model with durability degradation at any point in a route. FRC budget tracks anaerobic reserve depletion/recharge across segments with stateful recovery ceiling.

**Tech Stack:** Python 3, numpy, pandas, scipy (curve_fit), SQLite

**Spec:** `docs/superpowers/specs/2026-03-20-wko5-desktop-design.md` (Phase 2 section + Sub-projects 1-2)

**Existing:** `wko5/` package with config system, PD model, MMP computation, 69 passing tests. DB has 1,653 activities with per-second altitude/speed/power data. 337 rides >2h with altitude. 100% altitude coverage for 2024-2026.

**Python env:** `/tmp/fitenv/`. Recreate: `rm -rf /tmp/fitenv && python3 -m venv /tmp/fitenv && source /tmp/fitenv/bin/activate && pip install numpy pandas scipy matplotlib fitdecode pytest fastapi uvicorn defusedxml keyring httpx garth`

**Test command:** `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && pytest tests/ -v`

---

## File Structure

```
wko5/
  physics.py          # Cycling power equation, air density, speed estimation
  segments.py         # Segment detection, classification, demand profiling
  durability.py       # Empirical degradation model, fatigued PD, FRC budget
  demand_profile.py   # Composition: segments + durability + PD → demand ratios
```

Each module has a single clear responsibility:
- `physics.py` — pure math: given grade, speed, weight, CdA, Crr → power required (and inverse)
- `segments.py` — data processing: given altitude+distance time series → classified segments with demands
- `durability.py` — modeling: given historical rides → fitted decay, given a route position → effective capacity
- `demand_profile.py` — composition: given segments + PD model + durability params → per-segment demand ratios and success probabilities

**Deferred to later phases:** circadian adjustment, collapse zone detection, Bayesian upgrade (Phase 6)

---

## Task 1: Physics model (`physics.py`)

The cycling power equation is the foundation for computing power required on any segment.

**Files:**
- Create: `wko5/physics.py`
- Create: `tests/test_physics.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_physics.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from wko5.physics import power_required, speed_from_power, air_density


def test_power_flat_no_wind():
    """Power on flat at 30 km/h should be ~150-200W for a road cyclist."""
    v = 30 / 3.6  # m/s
    p = power_required(speed=v, grade=0, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert 100 < p < 250, f"Power={p:.0f}W on flat at 30km/h outside expected range"


def test_power_climbing():
    """Power climbing 8% at 10 km/h should be ~250-350W."""
    v = 10 / 3.6
    p = power_required(speed=v, grade=0.08, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert 200 < p < 400, f"Power={p:.0f}W climbing 8% at 10km/h outside expected range"


def test_power_descending_negative():
    """Descending steep grade at speed should require near-zero or negative power."""
    v = 50 / 3.6
    p = power_required(speed=v, grade=-0.08, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert p < 50, f"Power={p:.0f}W descending 8% should be near zero"


def test_power_increases_with_speed():
    """Power should increase with speed on flat (cubic relationship)."""
    p1 = power_required(speed=20/3.6, grade=0, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    p2 = power_required(speed=40/3.6, grade=0, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert p2 > p1 * 3, "Power at 40km/h should be >3x power at 20km/h (cubic)"


def test_power_increases_with_grade():
    """Power should increase linearly with grade at low speed."""
    p1 = power_required(speed=15/3.6, grade=0.04, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    p2 = power_required(speed=15/3.6, grade=0.08, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert p2 > p1 * 1.5, "Power at 8% should be significantly more than at 4%"


def test_speed_from_power_roundtrip():
    """speed_from_power should be inverse of power_required on flat."""
    target_power = 200
    v = speed_from_power(power=target_power, grade=0, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    p_check = power_required(speed=v, grade=0, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert abs(p_check - target_power) < 1.0, f"Roundtrip error: {p_check:.1f} vs {target_power}"


def test_speed_from_power_climbing():
    """Speed from power on a climb should be reasonable."""
    v = speed_from_power(power=280, grade=0.06, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    v_kmh = v * 3.6
    assert 10 < v_kmh < 20, f"Speed={v_kmh:.1f}km/h on 6% at 280W outside expected range"


def test_air_density_sea_level():
    """Air density at sea level, 20C should be ~1.2 kg/m3."""
    rho = air_density(temperature_c=20, altitude_m=0)
    assert 1.15 < rho < 1.25


def test_air_density_altitude():
    """Air density decreases with altitude."""
    rho_sea = air_density(temperature_c=20, altitude_m=0)
    rho_high = air_density(temperature_c=20, altitude_m=2000)
    assert rho_high < rho_sea * 0.85
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_physics.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement physics.py**

```python
# wko5/physics.py
"""Cycling power equation and related physics calculations."""

import numpy as np
from scipy.optimize import brentq

# Standard gravitational acceleration
G = 9.81


def air_density(temperature_c=20, altitude_m=0, pressure_pa=None):
    """Calculate air density from temperature and altitude.

    Uses the barometric formula for standard atmosphere if pressure not provided.
    """
    if pressure_pa is None:
        # Standard atmosphere pressure at altitude
        # P = P0 * (1 - 0.0065 * h / 288.15) ^ 5.2559
        pressure_pa = 101325 * (1 - 0.0065 * altitude_m / 288.15) ** 5.2559

    # Ideal gas law: rho = P / (R_specific * T)
    R_specific = 287.058  # J/(kg·K) for dry air
    temperature_k = temperature_c + 273.15
    return pressure_pa / (R_specific * temperature_k)


def power_required(speed, grade, weight_rider, weight_bike, cda, crr,
                   rho=None, temperature_c=20, altitude_m=0, drivetrain_loss=0.03):
    """Calculate power required to maintain speed on a given grade.

    P = P_aero + P_rolling + P_gravity + P_drivetrain_loss

    Args:
        speed: velocity in m/s
        grade: decimal (0.05 = 5%)
        weight_rider: kg
        weight_bike: kg
        cda: drag area (m^2)
        crr: rolling resistance coefficient
        rho: air density kg/m^3 (computed from temp/altitude if None)
        temperature_c: ambient temperature
        altitude_m: altitude for air density
        drivetrain_loss: fraction of power lost in drivetrain (default 3%)

    Returns: power in watts
    """
    if rho is None:
        rho = air_density(temperature_c, altitude_m)

    m = weight_rider + weight_bike

    p_aero = 0.5 * cda * rho * speed ** 3
    p_rolling = crr * m * G * speed * np.cos(np.arctan(grade))
    p_gravity = m * G * speed * np.sin(np.arctan(grade))

    p_total = p_aero + p_rolling + p_gravity

    # Account for drivetrain loss (power at pedals > power at wheel)
    if p_total > 0:
        p_total = p_total / (1 - drivetrain_loss)

    return float(p_total)


def speed_from_power(power, grade, weight_rider, weight_bike, cda, crr,
                     rho=None, temperature_c=20, altitude_m=0, drivetrain_loss=0.03):
    """Calculate speed achievable at a given power on a given grade.

    Inverse of power_required. Uses root-finding (Brent's method).

    Returns: speed in m/s
    """
    if rho is None:
        rho = air_density(temperature_c, altitude_m)

    # Effective power at wheel after drivetrain loss
    p_wheel = power * (1 - drivetrain_loss)

    def residual(v):
        if v <= 0:
            return -p_wheel
        m = weight_rider + weight_bike
        p_aero = 0.5 * cda * rho * v ** 3
        p_rolling = crr * m * G * v * np.cos(np.arctan(grade))
        p_gravity = m * G * v * np.sin(np.arctan(grade))
        return p_aero + p_rolling + p_gravity - p_wheel

    # Find speed where power balance = 0
    try:
        v = brentq(residual, 0.1, 30.0)  # 0.36 to 108 km/h
    except ValueError:
        # If no root in range, return boundary
        if residual(0.1) > 0:
            return 0.1  # Can't go even 0.36 km/h at this power
        return 30.0  # Faster than 108 km/h

    return float(v)
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_physics.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`
Expected: 78+ tests PASS

- [ ] **Step 6: Commit**

```bash
git add wko5/physics.py tests/test_physics.py
git commit -m "feat: add cycling physics model — power equation, speed solver, air density"
```

---

## Task 2: Segment detection and classification (`segments.py`)

**Files:**
- Create: `wko5/segments.py`
- Create: `tests/test_segments.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_segments.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.segments import compute_grade, classify_segments, analyze_ride_segments, analyze_gpx


def test_compute_grade_flat():
    """Flat terrain should have ~0% grade."""
    altitude = pd.Series([100.0] * 100)
    distance = pd.Series(np.arange(0, 1000, 10, dtype=float))
    grade = compute_grade(altitude, distance)
    assert abs(grade.mean()) < 0.01


def test_compute_grade_climbing():
    """10m rise over 100m distance = 10% grade."""
    altitude = pd.Series(np.linspace(100, 110, 20))
    distance = pd.Series(np.linspace(0, 100, 20))
    grade = compute_grade(altitude, distance)
    # Average should be near 0.10
    assert 0.05 < grade.mean() < 0.15


def test_classify_segments_basic():
    """Should detect climb, flat, and descent segments."""
    # Build a synthetic ride: flat → climb → flat → descent
    n = 400
    alt = np.concatenate([
        np.full(100, 100),           # flat
        np.linspace(100, 200, 100),  # climb (100m over 100 samples)
        np.full(100, 200),           # flat
        np.linspace(200, 100, 100),  # descent
    ])
    dist = np.linspace(0, 4000, n)  # 4km total, 10m per sample

    altitude = pd.Series(alt)
    distance = pd.Series(dist)

    segments = classify_segments(altitude, distance)
    assert isinstance(segments, list)
    assert len(segments) >= 3  # at least flat, climb, flat

    # Should have at least one climb and one descent
    types = [s["type"] for s in segments]
    assert "climb" in types
    assert "descent" in types


def test_classify_segments_min_length():
    """Very short segments should be merged into neighbors."""
    # A tiny 20m blip shouldn't create its own segment
    alt = np.concatenate([
        np.full(50, 100),       # flat
        np.array([100, 105]),   # tiny blip
        np.full(50, 100),       # flat
    ])
    dist = np.linspace(0, 1020, len(alt))

    segments = classify_segments(pd.Series(alt), pd.Series(dist))
    # Should be merged into one flat segment, not 3
    assert len(segments) <= 2


def test_analyze_ride_segments():
    """Analyze a real ride's segments."""
    from wko5.db import get_activities
    acts = get_activities(sub_sport="road")
    # Find a hilly ride with altitude
    import sqlite3
    from wko5.db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id FROM activities a
        JOIN records r ON r.activity_id = a.id
        WHERE a.sub_sport = 'road' AND a.total_ascent > 500
        AND r.altitude IS NOT NULL
        GROUP BY a.id
        ORDER BY a.start_time DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return  # Skip if no suitable ride

    result = analyze_ride_segments(row[0])
    assert isinstance(result, dict)
    assert "segments" in result
    assert "summary" in result
    assert len(result["segments"]) > 0

    # Each segment should have required fields
    seg = result["segments"][0]
    assert "type" in seg
    assert "distance_m" in seg
    assert "duration_s" in seg
    assert "avg_grade" in seg


def test_segment_demand_classification():
    """Segments should be classified by physiological system."""
    from wko5.db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id FROM activities a
        JOIN records r ON r.activity_id = a.id
        WHERE a.sub_sport = 'road' AND a.total_ascent > 1000
        AND r.altitude IS NOT NULL
        GROUP BY a.id
        ORDER BY a.start_time DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return

    result = analyze_ride_segments(row[0])
    for seg in result["segments"]:
        if seg["type"] == "climb":
            assert "system_taxed" in seg
            assert seg["system_taxed"] in ["neuromuscular", "anaerobic", "vo2max", "threshold", "endurance"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_segments.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement segments.py**

```python
# wko5/segments.py
"""Segment detection, classification, and demand profiling from ride data."""

import logging

import numpy as np
import pandas as pd

from wko5.config import get_config
from wko5.db import get_connection, get_records
from wko5.physics import power_required, speed_from_power

logger = logging.getLogger(__name__)

# Segment type thresholds (grade as decimal)
CLIMB_THRESHOLD = 0.03
ROLLING_THRESHOLD = 0.01
FLAT_THRESHOLD = 0.01  # -1% to +1%
MIN_SEGMENT_DISTANCE = 200  # meters — segments shorter than this are merged


def compute_grade(altitude, distance, smoothing_window=10):
    """Compute grade from altitude and distance series.

    Args:
        altitude: pd.Series of altitude in meters
        distance: pd.Series of cumulative distance in meters
        smoothing_window: rolling average window to remove GPS noise

    Returns: pd.Series of grade (decimal, e.g. 0.05 = 5%)
    """
    alt_diff = altitude.diff()
    dist_diff = distance.diff().replace(0, np.nan)

    grade = (alt_diff / dist_diff).fillna(0)

    # Smooth to remove GPS noise
    if smoothing_window > 1:
        grade = grade.rolling(window=smoothing_window, min_periods=1, center=True).mean()

    # Clamp to physically reasonable range (-0.5 to 0.5)
    grade = grade.clip(-0.5, 0.5)

    return grade


def _classify_point(grade):
    """Classify a single grade value into a segment type."""
    if grade > CLIMB_THRESHOLD:
        return "climb"
    elif grade > ROLLING_THRESHOLD:
        return "rolling"
    elif grade < -CLIMB_THRESHOLD:
        return "descent"
    elif grade < -ROLLING_THRESHOLD:
        return "rolling_descent"
    else:
        return "flat"


def _classify_demand(duration_s):
    """Classify physiological demand based on expected segment duration."""
    if duration_s < 15:
        return "neuromuscular"
    elif duration_s < 120:
        return "anaerobic"
    elif duration_s < 480:
        return "vo2max"
    elif duration_s < 1200:
        return "threshold"
    else:
        return "endurance"


def classify_segments(altitude, distance, power=None, speed=None, timestamps=None):
    """Detect and classify segments from altitude and distance data.

    Returns list of segment dicts, each with:
        type, start_idx, end_idx, distance_m, elevation_gain, avg_grade,
        duration_s (if timestamps provided), avg_power (if power provided)
    """
    grade = compute_grade(altitude, distance)

    # Classify each point
    classifications = grade.apply(_classify_point)

    # Build raw segments by grouping consecutive same-type points
    raw_segments = []
    current_type = classifications.iloc[0]
    start_idx = 0

    for i in range(1, len(classifications)):
        if classifications.iloc[i] != current_type:
            raw_segments.append({
                "type": current_type,
                "start_idx": start_idx,
                "end_idx": i,
            })
            current_type = classifications.iloc[i]
            start_idx = i

    # Don't forget the last segment
    raw_segments.append({
        "type": current_type,
        "start_idx": start_idx,
        "end_idx": len(classifications),
    })

    # Merge short segments into neighbors
    merged = []
    for seg in raw_segments:
        seg_dist = float(distance.iloc[min(seg["end_idx"]-1, len(distance)-1)] -
                        distance.iloc[seg["start_idx"]])

        if seg_dist < MIN_SEGMENT_DISTANCE and merged:
            # Merge into previous segment
            merged[-1]["end_idx"] = seg["end_idx"]
        else:
            merged.append(seg)

    # Get config once outside loop (not per-segment)
    cfg = get_config()

    # Compute metrics for each segment, tracking cumulative kJ
    result = []
    cumulative_kj = 0.0

    for seg in merged:
        s, e = seg["start_idx"], min(seg["end_idx"], len(altitude) - 1)
        if s >= e:
            continue

        seg_alt = altitude.iloc[s:e+1]
        seg_dist_vals = distance.iloc[s:e+1]
        seg_grade = grade.iloc[s:e+1]

        dist_m = float(seg_dist_vals.iloc[-1] - seg_dist_vals.iloc[0])
        elev_gain = float(max(0, seg_alt.iloc[-1] - seg_alt.iloc[0]))
        elev_loss = float(max(0, seg_alt.iloc[0] - seg_alt.iloc[-1]))
        avg_grade = float(seg_grade.mean())

        entry = {
            "type": seg["type"],
            "start_idx": s,
            "end_idx": e,
            "distance_m": round(dist_m, 1),
            "elevation_gain": round(elev_gain, 1),
            "elevation_loss": round(elev_loss, 1),
            "avg_grade": round(avg_grade, 4),
            "cumulative_kj_at_start": round(cumulative_kj, 1),
        }

        if timestamps is not None and len(timestamps) > e:
            try:
                t_start = pd.to_datetime(timestamps.iloc[s])
                t_end = pd.to_datetime(timestamps.iloc[e])
                entry["duration_s"] = (t_end - t_start).total_seconds()
            except Exception:
                entry["duration_s"] = float(e - s)  # fallback: 1 sample per second
        else:
            entry["duration_s"] = float(e - s)

        if power is not None:
            seg_power = power.iloc[s:e+1].dropna()
            if len(seg_power) > 0:
                entry["avg_power"] = round(float(seg_power.mean()), 1)
                entry["max_power"] = int(seg_power.max())
                # Accumulate kJ for cumulative tracking
                cumulative_kj += float(seg_power.sum()) / 1000

        if speed is not None:
            seg_speed = speed.iloc[s:e+1].dropna()
            if len(seg_speed) > 0:
                entry["avg_speed_ms"] = round(float(seg_speed.mean()), 2)

        # Classify physiological demand for climbs
        if seg["type"] == "climb" and entry["duration_s"] > 0:
            entry["system_taxed"] = _classify_demand(entry["duration_s"])

        # Compute power required for ALL segment types (spec requirement)
        if dist_m > 0 and entry["duration_s"] > 0:
            avg_speed = dist_m / entry["duration_s"]
            p_req = power_required(
                speed=avg_speed,
                grade=avg_grade,
                weight_rider=cfg["weight_kg"],
                weight_bike=cfg["bike_weight_kg"],
                cda=cfg["cda"],
                crr=cfg["crr"],
            )
            entry["power_required"] = round(max(0, p_req), 1)  # floor at 0 for descents

        result.append(entry)

    return result


def analyze_ride_segments(activity_id):
    """Full segment analysis for a recorded ride.

    Returns dict with:
        segments: list of segment dicts
        summary: aggregate demand profile
    """
    records = get_records(activity_id)
    if records.empty:
        return {"segments": [], "summary": {}}

    # Need altitude and distance
    if "altitude" not in records.columns or records["altitude"].isna().all():
        logger.warning(f"Activity {activity_id} has no altitude data")
        return {"segments": [], "summary": {"error": "no altitude data"}}

    if "distance" not in records.columns or records["distance"].isna().all():
        logger.warning(f"Activity {activity_id} has no distance data")
        return {"segments": [], "summary": {"error": "no distance data"}}

    altitude = records["altitude"].interpolate()
    distance = records["distance"].interpolate()
    power = records.get("power")
    speed = records.get("speed")
    timestamps = records.get("timestamp")

    segments = classify_segments(altitude, distance, power=power, speed=speed, timestamps=timestamps)

    # Build summary
    climbs = [s for s in segments if s["type"] == "climb"]
    total_climbing = sum(s["elevation_gain"] for s in climbs)
    total_distance = float(distance.iloc[-1] - distance.iloc[0]) if len(distance) > 0 else 0

    # Demand summary: what systems are taxed and how much
    demand_summary = {}
    for seg in climbs:
        system = seg.get("system_taxed", "unknown")
        if system not in demand_summary:
            demand_summary[system] = {"count": 0, "total_time_s": 0, "total_elevation": 0}
        demand_summary[system]["count"] += 1
        demand_summary[system]["total_time_s"] += seg.get("duration_s", 0)
        demand_summary[system]["total_elevation"] += seg.get("elevation_gain", 0)

    summary = {
        "total_segments": len(segments),
        "total_climbs": len(climbs),
        "total_climbing_m": round(total_climbing, 1),
        "total_distance_m": round(total_distance, 1),
        "demand_by_system": demand_summary,
    }

    return {"segments": segments, "summary": summary}


def analyze_gpx(gpx_path):
    """Analyze segments from a GPX file (for prospective route analysis).

    Args:
        gpx_path: path to a GPX file

    Returns: same format as analyze_ride_segments
    """
    import defusedxml.ElementTree as ET

    tree = ET.parse(gpx_path)
    root = tree.getroot()

    # Handle GPX namespace
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

    points = []
    cum_dist = 0.0
    prev_lat = prev_lon = None

    for trkpt in root.iter("{http://www.topografix.com/GPX/1/1}trkpt"):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        ele_elem = trkpt.find("gpx:ele", ns) or trkpt.find("{http://www.topografix.com/GPX/1/1}ele")
        ele = float(ele_elem.text) if ele_elem is not None else 0

        if prev_lat is not None:
            # Haversine distance
            R = 6371000  # Earth radius in meters
            dlat = np.radians(lat - prev_lat)
            dlon = np.radians(lon - prev_lon)
            a = np.sin(dlat/2)**2 + np.cos(np.radians(prev_lat)) * np.cos(np.radians(lat)) * np.sin(dlon/2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            cum_dist += R * c

        points.append({"altitude": ele, "distance": cum_dist})
        prev_lat, prev_lon = lat, lon

    if not points:
        return {"segments": [], "summary": {"error": "no trackpoints in GPX"}}

    df = pd.DataFrame(points)
    segments = classify_segments(df["altitude"], df["distance"])

    # Estimate duration for each segment using speed_from_power
    cfg = get_config()
    from wko5.pdcurve import compute_envelope_mmp, fit_pd_model
    mmp = compute_envelope_mmp(days=90)
    model = fit_pd_model(mmp)
    target_power = model["mFTP"] * 0.85 if model else cfg["ftp_manual"] * 0.85

    for seg in segments:
        if seg["distance_m"] > 0:
            est_speed = speed_from_power(
                power=target_power,
                grade=seg["avg_grade"],
                weight_rider=cfg["weight_kg"],
                weight_bike=cfg["bike_weight_kg"],
                cda=cfg["cda"],
                crr=cfg["crr"],
            )
            seg["estimated_duration_s"] = round(seg["distance_m"] / max(est_speed, 0.5), 1)
            seg["estimated_speed_kmh"] = round(est_speed * 3.6, 1)
            if seg["type"] == "climb":
                seg["system_taxed"] = _classify_demand(seg["estimated_duration_s"])
                seg["power_required"] = round(power_required(
                    speed=est_speed,
                    grade=seg["avg_grade"],
                    weight_rider=cfg["weight_kg"],
                    weight_bike=cfg["bike_weight_kg"],
                    cda=cfg["cda"],
                    crr=cfg["crr"],
                ), 1)

    climbs = [s for s in segments if s["type"] == "climb"]
    summary = {
        "total_segments": len(segments),
        "total_climbs": len(climbs),
        "total_climbing_m": round(sum(s["elevation_gain"] for s in climbs), 1),
        "total_distance_m": round(df["distance"].iloc[-1], 1),
    }

    return {"segments": segments, "summary": summary}
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_segments.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`

- [ ] **Step 6: Commit**

```bash
git add wko5/segments.py tests/test_segments.py
git commit -m "feat: add segment detection and classification from altitude/distance data"
```

---

## Task 3: Durability model (`durability.py`)

The most novel component — fits an empirical degradation function from historical long rides.

**Files:**
- Create: `wko5/durability.py`
- Create: `tests/test_durability.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_durability.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.durability import (
    compute_windowed_mmp, fit_durability_model, degradation_factor,
    effective_capacity, frc_budget_simulate, repeatability_index,
)


def test_degradation_factor_starts_at_one():
    """At zero cumulative work and zero time, degradation should be ~1.0."""
    params = {"a": 0.5, "b": 0.001, "c": 0.05}
    df = degradation_factor(cumulative_kj=0, elapsed_hours=0, params=params)
    assert abs(df - 1.0) < 0.05


def test_degradation_factor_decreases():
    """Degradation should decrease with more work and time."""
    params = {"a": 0.5, "b": 0.001, "c": 0.05}
    df1 = degradation_factor(cumulative_kj=0, elapsed_hours=0, params=params)
    df2 = degradation_factor(cumulative_kj=5000, elapsed_hours=5, params=params)
    df3 = degradation_factor(cumulative_kj=15000, elapsed_hours=15, params=params)
    assert df1 > df2 > df3


def test_degradation_factor_never_negative():
    """Degradation should never go below zero."""
    params = {"a": 0.5, "b": 0.001, "c": 0.05}
    df = degradation_factor(cumulative_kj=50000, elapsed_hours=60, params=params)
    assert df >= 0


def test_effective_capacity_less_than_fresh():
    """Effective capacity should always be <= fresh PD curve."""
    fresh_mmp = np.array([500, 450, 400, 350, 300, 280, 260, 250])
    params = {"a": 0.5, "b": 0.001, "c": 0.05}
    eff = effective_capacity(fresh_mmp, cumulative_kj=5000, elapsed_hours=5, params=params)
    assert all(eff <= fresh_mmp)
    assert all(eff > 0)


def test_fit_durability_model_real_data():
    """Fit durability model from real ride data and check it produces reasonable params."""
    result = fit_durability_model(min_ride_hours=3, min_rides=5)
    if result is None:
        return  # Skip if not enough long rides

    assert "a" in result
    assert "b" in result
    assert "c" in result
    assert "rides_used" in result
    assert "rmse" in result
    assert 0 < result["a"] < 1
    assert result["b"] > 0
    assert result["c"] > 0


def test_frc_budget_basic():
    """FRC budget should deplete above FTP and recharge below."""
    segments = [
        {"avg_power": 350, "duration_s": 300},   # 5 min above FTP — depletes
        {"avg_power": 150, "duration_s": 600},   # 10 min below FTP — recharges
        {"avg_power": 400, "duration_s": 120},   # 2 min hard — depletes more
    ]
    result = frc_budget_simulate(segments, mftp=280, frc_kj=20)
    assert isinstance(result, list)
    assert len(result) == 3
    # FRC should decrease after first segment
    assert result[0]["frc_remaining"] < 20
    # FRC should partially recover after second segment
    assert result[1]["frc_remaining"] > result[0]["frc_remaining"]
    # But recovery ceiling means it doesn't fully recover
    assert result[1]["frc_remaining"] < 20


def test_frc_budget_recovery_ceiling_degrades():
    """Recovery ceiling should decrease with successive deep depletions."""
    segments = [
        {"avg_power": 500, "duration_s": 60},   # hard — deep depletion
        {"avg_power": 150, "duration_s": 600},   # recovery
        {"avg_power": 500, "duration_s": 60},   # hard again
        {"avg_power": 150, "duration_s": 600},   # recovery
        {"avg_power": 500, "duration_s": 60},   # hard third time
        {"avg_power": 150, "duration_s": 600},   # recovery
    ]
    result = frc_budget_simulate(segments, mftp=280, frc_kj=20)
    # After 3rd recovery, FRC should be lower than after 1st recovery
    assert result[3]["frc_remaining"] > result[5]["frc_remaining"] or \
           result[1]["frc_remaining"] > result[3]["frc_remaining"]


def test_repeatability_index():
    """Repeatability index should be between 0 and 1."""
    ri = repeatability_index(activity_id=1, duration_s=300)
    if ri is not None:
        assert 0 < ri <= 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_durability.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement durability.py**

```python
# wko5/durability.py
"""Empirical durability model — degradation fitting, fatigued PD curves, FRC budget."""

import logging

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from wko5.config import get_config
from wko5.db import get_connection, get_activities, get_records
from wko5.pdcurve import compute_mmp
from wko5.training_load import compute_np, compute_tss

logger = logging.getLogger(__name__)


def degradation_factor(cumulative_kj, elapsed_hours, params):
    """Compute the degradation factor at a given point in a ride.

    Model: df = a * exp(-b * kJ/1000) + (1-a) * exp(-c * hours)

    Uses TSS-weighted kJ (intensity-weighted) per Exercise Physiologist review.

    Returns: float between 0 and 1 (1 = fresh, 0 = fully degraded)
    """
    a = params["a"]
    b = params["b"]
    c = params["c"]

    kj_term = a * np.exp(-b * cumulative_kj / 1000)
    time_term = (1 - a) * np.exp(-c * elapsed_hours)

    return float(max(0, kj_term + time_term))


def effective_capacity(fresh_mmp, cumulative_kj, elapsed_hours, params):
    """Compute the fatigued PD curve at a given point in a ride.

    effective_capacity = fresh_mmp * degradation_factor
    """
    df = degradation_factor(cumulative_kj, elapsed_hours, params)
    return fresh_mmp * df


def compute_windowed_mmp(power_series, window_hours=2):
    """Compute MMP at specific durations in rolling time windows across a ride.

    Uses vectorized rolling max at 4 target durations instead of full O(n^2) MMP.
    Returns list of dicts per window.
    """
    DURATIONS = [60, 300, 2400, 3600]  # 1min, 5min, 40min, 1hr

    window_s = int(window_hours * 3600)
    n = len(power_series)

    if n < window_s:
        return []

    power = power_series.fillna(0).values.astype(float)
    cumsum = np.concatenate([[0], np.cumsum(power)])

    # Pre-compute cumulative TSS: sum(power_i^2) / FTP / 3600
    cfg = get_config()
    ftp = cfg["ftp_manual"]
    cum_tss = np.cumsum(power ** 2) / (ftp * 3600) if ftp > 0 else np.cumsum(power) / 1000

    results = []

    # Non-overlapping windows
    for start in range(0, n - window_s + 1, window_s):
        end = start + window_s
        window_power = power[start:end]

        # Cumulative work and TSS from ride start to window midpoint
        midpoint = start + window_s // 2
        cum_kj = float(cumsum[midpoint]) / 1000
        elapsed_h = midpoint / 3600
        cum_tss_val = float(cum_tss[midpoint - 1]) if midpoint > 0 else 0.0

        entry = {
            "window_start_h": round(start / 3600, 2),
            "window_end_h": round(end / 3600, 2),
            "elapsed_hours": round(elapsed_h, 2),
            "cumulative_kj": round(cum_kj, 1),
            "cumulative_tss": round(cum_tss_val, 1),
        }

        # Compute MMP at specific durations via rolling mean max (vectorized)
        window_cumsum = np.concatenate([[0], np.cumsum(window_power)])
        for d in DURATIONS:
            label = f"mmp_{d}s"
            if d <= len(window_power):
                rolling_avg = (window_cumsum[d:] - window_cumsum[:len(window_power) - d + 1]) / d
                entry[label] = round(float(rolling_avg.max()), 1)
            else:
                entry[label] = float("nan")

        results.append(entry)

    return results


def _decay_model(x, a, b, c):
    """Decay function for curve fitting. x = (cumulative_kj, elapsed_hours)."""
    kj, hours = x
    return a * np.exp(-b * kj / 1000) + (1 - a) * np.exp(-c * hours)


def fit_durability_model(min_ride_hours=2, min_rides=5):
    """Fit the durability degradation model from historical long rides.

    Returns dict with fitted params {a, b, c, rides_used, rmse} or None if insufficient data.
    """
    activities = get_activities()
    long_rides = activities[activities["total_timer_time"] > min_ride_hours * 3600]

    if len(long_rides) < min_rides:
        logger.warning(f"Only {len(long_rides)} rides > {min_ride_hours}h, need {min_rides}")
        return None

    all_x_kj = []
    all_x_hours = []
    all_y_ratio = []
    rides_used = 0

    for _, ride in long_rides.iterrows():
        records = get_records(ride["id"])
        if records.empty or "power" not in records.columns:
            continue

        windows = compute_windowed_mmp(records["power"], window_hours=2)
        if len(windows) < 2:
            continue

        # Use 300s (5-min) power as the reference
        first_window_power = windows[0].get("mmp_300s")
        if first_window_power is None or first_window_power <= 0 or np.isnan(first_window_power):
            continue

        for w in windows[1:]:  # Skip first window (it's the reference)
            wp = w.get("mmp_300s")
            if wp is None or wp <= 0 or np.isnan(wp):
                continue

            ratio = wp / first_window_power
            if ratio > 1.2:  # Ignore anomalous increases (e.g., sprints at end)
                continue

            all_x_kj.append(w["cumulative_tss"])
            all_x_hours.append(w["elapsed_hours"])
            all_y_ratio.append(ratio)

        rides_used += 1

        if rides_used % 20 == 0:
            logger.info(f"Processed {rides_used} rides...")

    if len(all_y_ratio) < 10:
        logger.warning(f"Only {len(all_y_ratio)} data points, need at least 10")
        return None

    x_data = np.array([all_x_kj, all_x_hours])
    y_data = np.array(all_y_ratio)

    try:
        popt, _ = curve_fit(
            _decay_model, x_data, y_data,
            p0=[0.5, 0.001, 0.05],
            bounds=([0.01, 0.0001, 0.001], [0.99, 0.01, 0.5]),
            maxfev=10000,
        )
    except (RuntimeError, ValueError) as e:
        logger.warning(f"Durability model fitting failed: {e}")
        return None

    a, b, c = popt
    y_pred = _decay_model(x_data, a, b, c)
    rmse = float(np.sqrt(np.mean((y_data - y_pred) ** 2)))

    return {
        "a": round(float(a), 4),
        "b": round(float(b), 6),
        "c": round(float(c), 4),
        "rides_used": rides_used,
        "data_points": len(all_y_ratio),
        "rmse": round(rmse, 4),
    }


def frc_budget_simulate(segments, mftp, frc_kj, initial_depletion_count=0):
    """Simulate FRC budget across sequential segments.

    FRC depletes above mFTP, recharges below. Recovery ceiling degrades
    with successive deep depletions (stateful per Principal Engineer review).

    Args:
        segments: list of dicts with avg_power and duration_s
        mftp: functional threshold power (watts)
        frc_kj: total FRC capacity (kJ)
        initial_depletion_count: number of prior deep depletions

    Returns: list of dicts with frc_remaining, depletion_count, recovery_ceiling per segment
    """
    frc_remaining = frc_kj
    depletion_count = initial_depletion_count
    results = []

    for seg in segments:
        power = seg.get("avg_power", 0) or 0
        duration_s = seg.get("duration_s", 0) or 0

        if power > mftp:
            # Depleting FRC
            cost_kj = (power - mftp) * duration_s / 1000
            frc_remaining = max(0, frc_remaining - cost_kj)

            # Track deep depletions (>50% of FRC used in one segment)
            if cost_kj > frc_kj * 0.5:
                depletion_count += 1
        else:
            # Recharging FRC
            # Recovery rate: proportional to how far below mFTP
            recovery_rate = 0.5  # base rate: 50% of theoretical max per unit time
            recovery_kj = recovery_rate * (mftp - power) * duration_s / 1000

            # Recovery ceiling degrades with depletion count
            # After 0 depletions: can recover to 100%
            # After 1: 90%, after 2: 80%, etc.
            recovery_ceiling = max(0.5, 1.0 - depletion_count * 0.1)
            max_frc = frc_kj * recovery_ceiling

            frc_remaining = min(frc_remaining + recovery_kj, max_frc)

        results.append({
            "frc_remaining": round(frc_remaining, 2),
            "frc_pct": round(frc_remaining / frc_kj * 100, 1) if frc_kj > 0 else 0,
            "depletion_count": depletion_count,
            "recovery_ceiling": round(max(0.5, 1.0 - depletion_count * 0.1), 2),
        })

    return results


def repeatability_index(activity_id, duration_s=300):
    """Compute repeatability index: ratio of 3rd-best to 1st-best effort at a duration.

    Measures ability to produce repeated efforts vs one-off peaks.
    Returns float between 0 and 1, or None if insufficient data.
    """
    records = get_records(activity_id)
    if records.empty or "power" not in records.columns:
        return None

    power = records["power"].fillna(0).values.astype(float)
    n = len(power)

    if n < duration_s * 3:  # Need at least 3x the duration for meaningful repeatability
        return None

    # Compute rolling average at the target duration
    cumsum = np.concatenate([[0], np.cumsum(power)])
    rolling_avg = (cumsum[duration_s:] - cumsum[:n - duration_s + 1]) / duration_s

    # Find top 3 non-overlapping efforts
    efforts = []
    used_indices = set()

    sorted_indices = np.argsort(rolling_avg)[::-1]

    for idx in sorted_indices:
        # Check for overlap with existing efforts
        overlap = False
        for used_start in used_indices:
            if abs(idx - used_start) < duration_s:
                overlap = True
                break

        if not overlap:
            efforts.append(float(rolling_avg[idx]))
            used_indices.add(idx)

        if len(efforts) >= 3:
            break

    if len(efforts) < 3 or efforts[0] <= 0:
        return None

    return round(efforts[2] / efforts[0], 3)
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_durability.py -v`
Expected: All tests PASS. Note: `fit_durability_model` test hits real DB and computes windowed MMP for many rides — may take 1-2 minutes.

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add wko5/durability.py tests/test_durability.py
git commit -m "feat: add empirical durability model with FRC budget and repeatability index"
```

---

## Task 4: Demand profile composition (`demand_profile.py`)

The core integration point — composes segments with the durability model and PD curve to answer "what does this route demand and what's my capacity at each point?"

**Files:**
- Create: `wko5/demand_profile.py`
- Create: `tests/test_demand_profile.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_demand_profile.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from wko5.demand_profile import build_demand_profile


def test_demand_profile_basic():
    """Demand profile should enrich segments with capacity and demand ratio."""
    segments = [
        {"type": "flat", "distance_m": 5000, "duration_s": 600, "avg_grade": 0.0,
         "power_required": 180, "cumulative_kj_at_start": 0},
        {"type": "climb", "distance_m": 2000, "duration_s": 600, "avg_grade": 0.06,
         "power_required": 280, "cumulative_kj_at_start": 108},
        {"type": "flat", "distance_m": 5000, "duration_s": 600, "avg_grade": 0.0,
         "power_required": 180, "cumulative_kj_at_start": 276},
    ]
    # Fresh PD model
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600}
    durability_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = build_demand_profile(segments, pd_model, durability_params)
    assert isinstance(result, list)
    assert len(result) == 3

    for seg in result:
        assert "effective_capacity" in seg
        assert "demand_ratio" in seg
        assert "degradation" in seg


def test_demand_ratio_increases_with_fatigue():
    """Later segments should have higher demand ratios due to degradation."""
    segments = [
        {"type": "climb", "distance_m": 3000, "duration_s": 600, "avg_grade": 0.05,
         "power_required": 260, "cumulative_kj_at_start": 0},
        {"type": "climb", "distance_m": 3000, "duration_s": 600, "avg_grade": 0.05,
         "power_required": 260, "cumulative_kj_at_start": 5000},
    ]
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600}
    durability_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = build_demand_profile(segments, pd_model, durability_params)
    # Same power_required but more fatigue → higher demand ratio
    assert result[1]["demand_ratio"] > result[0]["demand_ratio"]


def test_demand_profile_fresh_has_no_degradation():
    """At zero cumulative work, degradation should be ~1.0."""
    segments = [
        {"type": "climb", "distance_m": 2000, "duration_s": 300, "avg_grade": 0.06,
         "power_required": 280, "cumulative_kj_at_start": 0},
    ]
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600}
    durability_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = build_demand_profile(segments, pd_model, durability_params)
    assert result[0]["degradation"] > 0.95


def test_demand_profile_with_real_ride():
    """End-to-end: real ride → segments → demand profile."""
    from wko5.db import get_connection
    from wko5.segments import analyze_ride_segments
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id FROM activities a
        JOIN records r ON r.activity_id = a.id
        WHERE a.sub_sport = 'road' AND a.total_ascent > 500
        AND r.altitude IS NOT NULL
        GROUP BY a.id
        ORDER BY a.start_time DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return  # Skip if no suitable ride

    ride_result = analyze_ride_segments(row[0])
    if not ride_result["segments"]:
        return

    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600}
    durability_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = build_demand_profile(ride_result["segments"], pd_model, durability_params)
    assert len(result) == len(ride_result["segments"])
    assert all("demand_ratio" in s for s in result)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_demand_profile.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement demand_profile.py**

```python
# wko5/demand_profile.py
"""Demand profile — compose segments with durability model and PD curve."""

import numpy as np

from wko5.durability import degradation_factor


def _capacity_at_duration(pd_model, duration_s):
    """Estimate power capacity at a given duration from PD model parameters.

    Uses the 3-component model: P(t) = Pmax * e^(-t/tau) + FRC*1000/(t+t0) + mFTP
    For simplicity, approximate from mFTP and FRC for durations > 60s.
    """
    mftp = pd_model.get("mFTP", 0)
    frc_kj = pd_model.get("FRC", 0)

    if duration_s <= 0:
        return mftp

    # Above-threshold capacity from FRC: P_above = FRC * 1000 / duration_s
    frc_contribution = (frc_kj * 1000) / duration_s if duration_s > 0 else 0

    return mftp + frc_contribution


def build_demand_profile(segments, pd_model, durability_params):
    """Build demand profile by composing segments with durability and PD curve.

    For each segment:
    1. Look up cumulative_kj_at_start and elapsed time
    2. Compute degradation_factor at that point
    3. Compute effective capacity = fresh_capacity * degradation
    4. Compute demand_ratio = power_required / effective_capacity

    Args:
        segments: list of segment dicts (from classify_segments or analyze_ride_segments)
        pd_model: dict with at least {mFTP, FRC} from fit_pd_model
        durability_params: dict with {a, b, c} from fit_durability_model

    Returns: list of enriched segment dicts with demand_ratio, effective_capacity, degradation
    """
    result = []
    elapsed_s = 0.0

    for seg in segments:
        cum_kj = seg.get("cumulative_kj_at_start", 0)
        duration_s = seg.get("duration_s", seg.get("estimated_duration_s", 0))
        elapsed_h = elapsed_s / 3600

        # Compute degradation at this point in the ride
        deg = degradation_factor(cum_kj, elapsed_h, durability_params)

        # Fresh capacity at this segment's duration
        fresh_capacity = _capacity_at_duration(pd_model, duration_s)

        # Effective (fatigued) capacity
        eff_capacity = fresh_capacity * deg

        # Demand ratio
        p_required = seg.get("power_required", 0)
        demand_ratio = p_required / eff_capacity if eff_capacity > 0 else float("inf")

        enriched = dict(seg)
        enriched.update({
            "degradation": round(deg, 4),
            "fresh_capacity": round(fresh_capacity, 1),
            "effective_capacity": round(eff_capacity, 1),
            "demand_ratio": round(demand_ratio, 4),
        })

        result.append(enriched)
        elapsed_s += duration_s

    return result
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_demand_profile.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`

- [ ] **Step 6: Commit**

```bash
git add wko5/demand_profile.py tests/test_demand_profile.py
git commit -m "feat: add demand profile — compose segments with durability model"
```

---

## Task 5: API endpoints for Phase 2 modules

**Files:**
- Modify: `wko5/api/routes.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Add new routes**

Add to `wko5/api/routes.py`:

```python
from wko5.segments import analyze_ride_segments
from wko5.durability import fit_durability_model, effective_capacity, frc_budget_simulate
from wko5.demand_profile import build_demand_profile

@router.get("/segments/{activity_id}", dependencies=[Depends(verify_token)])
def segments(activity_id: int):
    result = analyze_ride_segments(activity_id)
    return _sanitize_nans(result)

@router.get("/durability", dependencies=[Depends(verify_token)])
def durability():
    result = fit_durability_model()
    if result is None:
        return {"error": "Insufficient data for durability model"}
    return result

@router.get("/demand/{activity_id}", dependencies=[Depends(verify_token)])
def demand(activity_id: int):
    from wko5.pdcurve import compute_envelope_mmp, fit_pd_model
    ride_segments = analyze_ride_segments(activity_id)
    if not ride_segments["segments"]:
        return {"error": "No segments found"}
    pd_model = fit_pd_model(compute_envelope_mmp(days=90))
    dur_params = fit_durability_model()
    if dur_params is None:
        return {"error": "Insufficient data for durability model"}
    profile = build_demand_profile(ride_segments["segments"], pd_model, dur_params)
    return _sanitize_nans({"segments": profile, "summary": ride_segments["summary"]})
```

- [ ] **Step 2: Add tests**

Add to `tests/test_api.py`:

```python
def test_segments_with_auth():
    client, token = _get_client()
    response = client.get("/api/segments/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "segments" in data
    assert "summary" in data
```

- [ ] **Step 3: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_api.py -v`

- [ ] **Step 4: Commit**

```bash
git add wko5/api/routes.py tests/test_api.py
git commit -m "feat: add segment, durability, and demand profile API endpoints"
```

---

## Task 6: Update __init__.py and wko5-analyzer skill

**Files:**
- Modify: `wko5/__init__.py`
- Modify: `~/.claude/skills/wko5-analyzer/skill.md`

- [ ] **Step 1: Update package exports**

Add to `wko5/__init__.py`:
```python
from wko5.segments import analyze_ride_segments, analyze_gpx
from wko5.durability import fit_durability_model, effective_capacity, frc_budget_simulate
from wko5.physics import power_required, speed_from_power
from wko5.demand_profile import build_demand_profile
```

- [ ] **Step 2: Update the wko5-analyzer skill**

Add new entries to the Question → Function mapping table and Module Reference section:

```
### Segment Analysis
from wko5.segments import analyze_ride_segments, analyze_gpx
result = analyze_ride_segments(activity_id)  # segments + demand summary
result = analyze_gpx("/path/to/route.gpx")   # prospective route analysis

### Durability Model
from wko5.durability import fit_durability_model, effective_capacity, frc_budget_simulate
params = fit_durability_model()  # fit from historical data
eff = effective_capacity(fresh_mmp, cumulative_kj=5000, elapsed_hours=5, params=params)

| Route analysis / terrain | analyze_ride_segments() or analyze_gpx() |
| Durability / fade | fit_durability_model() + effective_capacity() |
| FRC budget for a route | frc_budget_simulate(segments, mftp, frc_kj) |
| Demand profile / what does this route require | build_demand_profile(segments, pd_model, durability_params) |
```

- [ ] **Step 3: Run full test suite**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit and push**

```bash
git add wko5/__init__.py
git commit -m "feat: export Phase 2 modules from package"
git push origin main
```
