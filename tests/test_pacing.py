# tests/test_pacing.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.pacing import solve_pacing, RidePlan


def test_ride_plan_defaults():
    """RidePlan should have sensible defaults for non-config fields."""
    plan = RidePlan(target_riding_hours=10, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert plan.rest_hours == 0
    assert plan.drafting_pct == 0.0
    assert plan.drafting_savings == 0.30
    assert plan.starting_glycogen_g == 500


def test_solve_pacing_flat():
    """Flat route should return uniform power across segments."""
    segments = [
        {"type": "flat", "distance_m": 5000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
        {"type": "flat", "distance_m": 5000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
    ]
    plan = RidePlan(target_riding_hours=1, cda=0.35, weight_rider=78, weight_bike=9)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = solve_pacing(segments, plan, dur_params)
    assert "base_power" in result
    assert "segments" in result
    assert len(result["segments"]) == 2
    for seg in result["segments"]:
        assert "target_power" in seg
        assert "estimated_speed_kmh" in seg
        assert "estimated_duration_s" in seg


def test_solve_pacing_matches_target_time():
    """Total segment time should approximately match target."""
    segments = [
        {"type": "flat", "distance_m": 20000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
        {"type": "climb", "distance_m": 5000, "avg_grade": 0.05, "cumulative_kj_at_start": 0},
        {"type": "descent", "distance_m": 10000, "avg_grade": -0.03, "cumulative_kj_at_start": 0},
    ]
    plan = RidePlan(target_riding_hours=2, cda=0.35, weight_rider=78, weight_bike=9)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = solve_pacing(segments, plan, dur_params)
    total_s = sum(s["estimated_duration_s"] for s in result["segments"])
    target_s = 2 * 3600
    assert abs(total_s - target_s) < 60, f"Off by {abs(total_s - target_s):.0f}s"


def test_pacing_power_fades_with_durability():
    """Later segments should have lower target power due to durability decay."""
    segments = [
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 3000},
    ]
    plan = RidePlan(target_riding_hours=6, cda=0.35, weight_rider=78, weight_bike=9)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = solve_pacing(segments, plan, dur_params)
    p1 = result["segments"][0]["target_power"]
    p2 = result["segments"][1]["target_power"]
    assert p2 < p1, f"Second segment power {p2:.0f}W should be < first {p1:.0f}W"


def test_pacing_with_drafting():
    """Drafting should reduce required power on flat segments."""
    segments = [
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
    ]
    plan_solo = RidePlan(target_riding_hours=2, cda=0.35, weight_rider=78, weight_bike=9, drafting_pct=0.0)
    plan_draft = RidePlan(target_riding_hours=2, cda=0.35, weight_rider=78, weight_bike=9, drafting_pct=0.4, drafting_savings=0.30)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    r_solo = solve_pacing(segments, plan_solo, dur_params)
    r_draft = solve_pacing(segments, plan_draft, dur_params)
    assert r_draft["base_power"] < r_solo["base_power"]


def test_pacing_with_aerobars():
    """Lower CdA (aerobars) should reduce required power."""
    segments = [
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
    ]
    plan_hoods = RidePlan(target_riding_hours=2, cda=0.35, weight_rider=78, weight_bike=9)
    plan_aero = RidePlan(target_riding_hours=2, cda=0.28, weight_rider=78, weight_bike=9)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    r_hoods = solve_pacing(segments, plan_hoods, dur_params)
    r_aero = solve_pacing(segments, plan_aero, dur_params)
    assert r_aero["base_power"] < r_hoods["base_power"]


def test_pacing_with_real_ride():
    """Pacing solver should work with real ride segments."""
    from wko5.segments import analyze_ride_segments
    from wko5.durability import fit_durability_model
    ride = analyze_ride_segments(1628)  # 300km ride
    if not ride["segments"]:
        return
    dur_params = fit_durability_model()
    if dur_params is None:
        return

    plan = RidePlan(target_riding_hours=11, cda=0.28, weight_rider=78, weight_bike=9)
    result = solve_pacing(ride["segments"], plan, dur_params)
    assert 100 < result["base_power"] < 300
    total_h = sum(s["estimated_duration_s"] for s in result["segments"]) / 3600
    assert abs(total_h - 11) < 0.1
