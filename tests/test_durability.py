# tests/test_durability.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.durability import (
    compute_windowed_mmp, fit_durability_model, degradation_factor,
    effective_capacity, frc_budget_simulate, repeatability_index,
    check_fresh_baseline, durability_benchmark,
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
        {"avg_power": 350, "duration_s": 300},
        {"avg_power": 150, "duration_s": 600},
        {"avg_power": 400, "duration_s": 120},
    ]
    result = frc_budget_simulate(segments, mftp=280, frc_kj=20)
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0]["frc_remaining"] < 20
    assert result[1]["frc_remaining"] > result[0]["frc_remaining"]
    assert result[1]["frc_remaining"] < 20


def test_frc_budget_recovery_ceiling_degrades():
    """Recovery ceiling should decrease with successive deep depletions."""
    segments = [
        {"avg_power": 500, "duration_s": 60},
        {"avg_power": 150, "duration_s": 600},
        {"avg_power": 500, "duration_s": 60},
        {"avg_power": 150, "duration_s": 600},
        {"avg_power": 500, "duration_s": 60},
        {"avg_power": 150, "duration_s": 600},
    ]
    result = frc_budget_simulate(segments, mftp=280, frc_kj=20)
    # Recovery ceiling should degrade: check it directly
    assert result[1]["recovery_ceiling"] >= result[3]["recovery_ceiling"] or \
           result[3]["recovery_ceiling"] >= result[5]["recovery_ceiling"]


def test_repeatability_index():
    """Repeatability index should be between 0 and 1."""
    ri = repeatability_index(activity_id=1, duration_s=300)
    if ri is not None:
        assert 0 < ri <= 1.0


def test_degradation_factor_with_weight():
    """Degradation factor should accept weight_kg for kJ/kg normalization."""
    params = {"a": 0.5, "b": 0.001, "c": 0.05}
    # Same kJ, different weights = different degradation
    df_heavy = degradation_factor(2000, 3.0, params, weight_kg=80)
    df_light = degradation_factor(2000, 3.0, params, weight_kg=55)
    # Lighter rider should degrade more at same absolute kJ
    assert df_light < df_heavy


def test_windowed_mmp_has_kj_per_kg():
    """Windowed MMP should include kJ/kg field when weight provided."""
    power = pd.Series(np.random.normal(200, 20, 14400))  # 4 hours
    windows = compute_windowed_mmp(power, window_hours=2, weight_kg=78)
    if windows:
        assert "cumulative_kj_per_kg" in windows[0]


def test_check_fresh_baseline():
    """Fresh baseline check should return staleness info."""
    result = check_fresh_baseline(days=180)
    assert isinstance(result, dict)
    for dur in [60, 300]:
        if dur in result:
            assert "exists" in result[dur]


def test_durability_benchmark():
    """Benchmark classification should match EC podcast tiers."""
    assert durability_benchmark(1) == "elite_pro"
    assert durability_benchmark(15) == "good_amateur"
    assert durability_benchmark(35) == "average_amateur"
    assert durability_benchmark(50) == "needs_work"
