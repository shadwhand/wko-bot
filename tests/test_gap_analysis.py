# tests/test_gap_analysis.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from wko5.gap_analysis import (
    run_monte_carlo, gap_analysis, feasibility_flag,
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
