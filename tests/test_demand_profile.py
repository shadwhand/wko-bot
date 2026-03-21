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
        return

    ride_result = analyze_ride_segments(row[0])
    if not ride_result["segments"]:
        return

    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600}
    durability_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = build_demand_profile(ride_result["segments"], pd_model, durability_params)
    assert len(result) == len(ride_result["segments"])
    assert all("demand_ratio" in s for s in result)
