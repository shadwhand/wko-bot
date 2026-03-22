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
