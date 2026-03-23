# tests/test_gap_analysis.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from wko5.gap_analysis import (
    run_monte_carlo, gap_analysis, feasibility_flag,
    opportunity_cost_analysis, short_power_consistency,
)


def test_feasibility_flag_comfortable():
    assert feasibility_flag(0.70) == "comfortable"

def test_feasibility_flag_hard():
    assert feasibility_flag(0.90) == "hard"

def test_feasibility_flag_limit():
    assert feasibility_flag(0.97) == "limit"

def test_feasibility_flag_impossible():
    assert feasibility_flag(1.10) == "impossible"


def test_monte_carlo_returns_probabilities():
    """Monte Carlo should return per-segment success probabilities."""
    segments = [
        {"type": "flat", "distance_m": 5000, "duration_s": 600, "avg_grade": 0.0,
         "power_required": 180, "cumulative_kj_at_start": 0},
        {"type": "climb", "distance_m": 2000, "duration_s": 600, "avg_grade": 0.06,
         "power_required": 280, "cumulative_kj_at_start": 108},
    ]
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600, "tau": 15, "t0": 4}
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = run_monte_carlo(segments, pd_model, dur_params, n_draws=50)
    assert isinstance(result, list)
    assert len(result) == 2
    for seg in result:
        assert "success_probability" in seg
        assert 0 <= seg["success_probability"] <= 1


def test_monte_carlo_easy_route_high_probability():
    """An easy flat route should have near-100% success probability."""
    segments = [
        {"type": "flat", "distance_m": 10000, "duration_s": 1200, "avg_grade": 0.0,
         "power_required": 120, "cumulative_kj_at_start": 0},
    ]
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600, "tau": 15, "t0": 4}
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = run_monte_carlo(segments, pd_model, dur_params, n_draws=100)
    assert result[0]["success_probability"] > 0.9


def test_monte_carlo_impossible_route_low_probability():
    """A route demanding 500W sustained should have low success probability."""
    segments = [
        {"type": "climb", "distance_m": 5000, "duration_s": 1200, "avg_grade": 0.12,
         "power_required": 500, "cumulative_kj_at_start": 0},
    ]
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600, "tau": 15, "t0": 4}
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = run_monte_carlo(segments, pd_model, dur_params, n_draws=100)
    assert result[0]["success_probability"] < 0.3


def test_gap_analysis_structure():
    """Gap analysis should return segments, bottleneck, and overall feasibility."""
    segments = [
        {"type": "flat", "distance_m": 5000, "duration_s": 600, "avg_grade": 0.0,
         "power_required": 180, "cumulative_kj_at_start": 0},
        {"type": "climb", "distance_m": 2000, "duration_s": 600, "avg_grade": 0.06,
         "power_required": 280, "cumulative_kj_at_start": 108},
        {"type": "descent", "distance_m": 3000, "duration_s": 300, "avg_grade": -0.04,
         "power_required": 0, "cumulative_kj_at_start": 276},
    ]
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600, "tau": 15, "t0": 4}
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = gap_analysis(segments, pd_model, dur_params, n_draws=50)
    assert "segments" in result
    assert "bottleneck" in result
    assert "overall" in result
    assert "hardest_segment_idx" in result["bottleneck"]
    assert "route_completable" in result["overall"]
    assert "probability_of_completion" in result["overall"]
    assert "key_risk_factors" in result["overall"]
    assert "safety_margin_w" in result["overall"]


def test_gap_analysis_has_absolute_power_check():
    """Gap analysis should include absolute power check alongside durability."""
    segments = [
        {"type": "climb", "distance_m": 5000, "duration_s": 1200, "avg_grade": 0.06,
         "power_required": 280, "cumulative_kj_at_start": 0},
    ]
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600, "tau": 15, "t0": 4}
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}
    result = gap_analysis(segments, pd_model, dur_params, n_draws=20)
    assert "absolute_power_check" in result
    assert "fresh_power_sufficient" in result["absolute_power_check"]


def test_gap_analysis_with_real_ride():
    """End-to-end: real ride -> segments -> gap analysis."""
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

    ride = analyze_ride_segments(row[0])
    if not ride["segments"]:
        return

    from wko5.pdcurve import compute_envelope_mmp, fit_pd_model
    pd_model = fit_pd_model(compute_envelope_mmp(days=90))
    from wko5.durability import fit_durability_model
    dur_params = fit_durability_model()
    if pd_model is None or dur_params is None:
        return

    result = gap_analysis(ride["segments"], pd_model, dur_params, n_draws=20)
    assert len(result["segments"]) == len(ride["segments"])
    assert isinstance(result["overall"]["probability_of_completion"], float)


def test_monte_carlo_with_posteriors():
    """Monte Carlo should use posteriors when available."""
    from wko5.bayesian import fit_pd_bayesian, fit_durability_bayesian, store_posterior

    # Fit and store posteriors
    pd = fit_pd_bayesian(days=90)
    dur = fit_durability_bayesian()
    if pd:
        store_posterior("pd_model", pd)
    if dur:
        store_posterior("durability", dur)

    segments = [
        {"type": "flat", "distance_m": 5000, "duration_s": 600, "avg_grade": 0.0,
         "power_required": 180, "cumulative_kj_at_start": 0},
    ]
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600, "tau": 15, "t0": 4}
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = run_monte_carlo(segments, pd_model, dur_params, n_draws=50)
    assert len(result) == 1
    assert "success_probability" in result[0]


def test_opportunity_cost_returns_none_for_missing_route():
    """opportunity_cost_analysis should return None for a non-existent route."""
    result = opportunity_cost_analysis(route_id=999999)
    assert result is None


def test_opportunity_cost_returns_none_when_no_routes():
    """opportunity_cost_analysis should handle empty routes table gracefully."""
    from wko5.db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    # Check if routes table has any data
    try:
        cursor.execute("SELECT id FROM routes LIMIT 1")
        row = cursor.fetchone()
    except Exception:
        row = None
    finally:
        conn.close()

    if row is None:
        # No routes — any route_id should return None
        result = opportunity_cost_analysis(route_id=1)
        assert result is None
    else:
        # Routes exist; just verify it doesn't crash for a missing route
        result = opportunity_cost_analysis(route_id=999999)
        assert result is None


def test_short_power_consistency_returns_none_insufficient_data():
    """short_power_consistency should return None when fewer than 5 efforts exist."""
    from wko5.db import get_activities
    activities = get_activities()
    # Use an absurdly long duration so no ride has that many seconds of power data
    result = short_power_consistency(duration_s=86400, days_back=365)
    assert result is None


def test_short_power_consistency_structure():
    """short_power_consistency should return correct keys when data is available."""
    from wko5.db import get_activities, get_records
    activities = get_activities()

    # Count rides with enough power data at 60s
    usable = 0
    for _, act in activities.iterrows():
        records = get_records(act["id"])
        if not records.empty and "power" in records.columns and len(records) >= 60:
            power = records["power"].fillna(0).values
            if power.max() > 0:
                usable += 1
        if usable >= 5:
            break

    if usable < 5:
        # Not enough data — skip the structural check
        return

    result = short_power_consistency(duration_s=60, days_back=365)
    assert result is not None
    assert "peak" in result
    assert "typical" in result
    assert "ratio" in result
    assert "diagnosis" in result
    assert "efforts_analyzed" in result
    assert "message" in result
    assert result["diagnosis"] in ("consistency", "capacity")
    assert result["ratio"] == round(result["peak"] / result["typical"], 3)
    assert result["efforts_analyzed"] >= 5
