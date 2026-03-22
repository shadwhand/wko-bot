import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.pdcurve import (
    compute_mmp, get_cached_mmp, compute_envelope_mmp,
    fit_pd_model, power_at_durations, rolling_ftp, compare_periods,
)


def test_decompose_pd_change():
    """Should decompose PD changes into CP vs W' vs Pmax contributions."""
    from wko5.pdcurve import decompose_pd_change
    old = {"Pmax": 1100, "FRC": 18, "mFTP": 280, "tau": 15, "t0": 4}
    new = {"Pmax": 1100, "FRC": 22, "mFTP": 285, "tau": 15, "t0": 4}
    result = decompose_pd_change(old, new)
    assert "mFTP_change_w" in result
    assert "FRC_change_kj" in result
    assert result["mFTP_change_w"] == 5
    assert result["FRC_change_kj"] == 4
    assert "dominant_change" in result


def test_compute_mmp_constant_power():
    power = pd.Series([200.0] * 100)
    mmp = compute_mmp(power)
    assert len(mmp) == 100
    assert mmp[0] == 200.0
    assert abs(mmp[49] - 200.0) < 0.01
    assert abs(mmp[99] - 200.0) < 0.01


def test_compute_mmp_decreasing():
    power = pd.Series(np.random.randint(100, 400, size=1000).astype(float))
    mmp = compute_mmp(power)
    for i in range(1, len(mmp)):
        assert mmp[i] <= mmp[i - 1] + 0.01


def test_compute_mmp_known_values():
    power = pd.Series([300.0] * 60 + [200.0] * 60)
    mmp = compute_mmp(power)
    assert mmp[0] == 300.0
    assert abs(mmp[59] - 300.0) < 0.01
    assert abs(mmp[119] - 250.0) < 0.01


def test_compute_mmp_handles_nan():
    power = pd.Series([200.0, np.nan, 200.0, 200.0, 200.0])
    mmp = compute_mmp(power)
    assert len(mmp) == 5
    assert mmp[0] == 200.0


def test_get_cached_mmp_returns_array():
    mmp = get_cached_mmp(1)
    assert isinstance(mmp, np.ndarray)
    assert len(mmp) > 100
    assert mmp[0] > 0


def test_get_cached_mmp_cache_consistency():
    mmp1 = get_cached_mmp(1)
    mmp2 = get_cached_mmp(1)
    np.testing.assert_array_equal(mmp1, mmp2)


def test_compute_envelope_mmp():
    mmp = compute_envelope_mmp(days=90)
    assert isinstance(mmp, np.ndarray)
    assert len(mmp) > 100
    for i in range(1, min(len(mmp), 3600)):
        assert mmp[i] <= mmp[i - 1] + 0.01


def test_fit_pd_model_synthetic():
    durations = np.arange(1, 3601)
    synthetic = 1200 * np.exp(-durations / 15) + 20000 / (durations + 5) + 280
    synthetic += np.random.normal(0, 1, len(synthetic))
    result = fit_pd_model(synthetic)
    assert result is not None
    assert "Pmax" in result
    assert "FRC" in result
    assert "mFTP" in result
    assert "TTE" in result
    assert "mVO2max_ml_min_kg" in result
    assert 250 < result["mFTP"] < 320


def test_fit_pd_model_real_data():
    mmp = compute_envelope_mmp(days=90)
    if len(mmp) < 300:
        return
    result = fit_pd_model(mmp)
    assert result is not None
    assert 220 < result["mFTP"] < 350, f"mFTP={result['mFTP']} outside reasonable range"


def test_fit_pd_model_empty_input():
    result = fit_pd_model(np.array([]))
    assert result is None


def test_fit_pd_model_short_input():
    result = fit_pd_model(np.array([500, 400, 350, 300, 280]))
    assert result is None


def test_power_at_durations():
    mmp = np.array([500, 450, 400, 350, 300])
    result = power_at_durations(mmp, durations=[1, 3, 5])
    assert result[1] == 500
    assert result[3] == 400
    assert result[5] == 300


def test_power_at_durations_beyond_length():
    mmp = np.array([500, 450, 400])
    result = power_at_durations(mmp, durations=[1, 5])
    assert result[1] == 500
    assert np.isnan(result[5])


def test_vo2max_trained_cyclist():
    """VO2max for a trained cyclist should be in a reasonable range using efficiency-based estimation."""
    mmp = compute_envelope_mmp(days=365)
    if len(mmp) < 300:
        return
    result = fit_pd_model(mmp)
    if result is None:
        return
    # Trained cyclist at ~3.5-4.0 W/kg should be ~45-70 mL/min/kg
    assert 40 < result["mVO2max_ml_min_kg"] < 75, \
        f"mVO2max={result['mVO2max_ml_min_kg']} outside trained cyclist range"
