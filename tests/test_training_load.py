import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from wko5.training_load import compute_np, compute_tss, build_pmc, current_fitness, efficiency_factor, if_distribution, ftp_growth_curve, performance_trend


def test_compute_np_constant_power():
    power = pd.Series([250.0] * 3600)
    np_val = compute_np(power)
    assert abs(np_val - 250.0) < 1.0


def test_compute_np_variable_power():
    power = pd.Series([200.0] * 1800 + [300.0] * 1800)
    np_val = compute_np(power)
    avg = power.mean()
    assert np_val >= avg


def test_compute_np_with_zeros():
    power = pd.Series([300.0] * 100 + [0.0] * 100 + [300.0] * 100)
    np_val = compute_np(power)
    assert np_val > 0


def test_compute_np_short_series():
    power = pd.Series([250.0] * 10)
    np_val = compute_np(power)
    assert np_val > 0


def test_compute_tss_one_hour_at_ftp():
    tss = compute_tss(np_watts=292.0, duration_s=3600, ftp=292.0)
    assert abs(tss - 100.0) < 1.0


def test_compute_tss_half_hour_at_ftp():
    tss = compute_tss(np_watts=292.0, duration_s=1800, ftp=292.0)
    assert abs(tss - 50.0) < 1.0


def test_compute_tss_above_ftp():
    tss = compute_tss(np_watts=350.0, duration_s=3600, ftp=292.0)
    assert tss > 100


def test_build_pmc_returns_dataframe():
    pmc = build_pmc()
    assert isinstance(pmc, pd.DataFrame)
    assert "CTL" in pmc.columns
    assert "ATL" in pmc.columns
    assert "TSB" in pmc.columns
    assert len(pmc) > 100


def test_pmc_tsb_equals_ctl_minus_atl():
    pmc = build_pmc()
    if not pmc.empty:
        diff = abs(pmc["TSB"] - (pmc["CTL"] - pmc["ATL"]))
        assert diff.max() < 0.01


def test_current_fitness_returns_dict():
    result = current_fitness()
    assert isinstance(result, dict)
    assert "CTL" in result
    assert "ATL" in result
    assert "TSB" in result


def test_efficiency_factor():
    ef = efficiency_factor(1)
    assert isinstance(ef, float)


def test_if_distribution():
    """IF distribution should return histogram and floor/ceiling."""
    result = if_distribution(days_back=90)
    if result is None:
        return  # insufficient data
    assert "histogram" in result
    assert "floor" in result
    assert "ceiling" in result
    assert "compressed" in result
    assert isinstance(result["compressed"], bool)
    assert result["floor"] <= result["ceiling"]


# ── ftp_growth_curve tests ────────────────────────────────────────────────────

def _make_rolling_ftp_df(n=12, start_ftp=250.0, slope=5.0):
    """Build a synthetic rolling_ftp DataFrame with logarithmic growth."""
    dates = pd.date_range("2023-01-01", periods=n, freq="30D")
    weeks = (dates - dates[0]).days / 7.0
    ftp_vals = slope * np.log(weeks + 1) + start_ftp
    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "mFTP": ftp_vals})


def test_ftp_growth_curve_returns_expected_keys():
    """ftp_growth_curve should return all required keys when data is available."""
    synthetic = _make_rolling_ftp_df()
    with patch("wko5.training_load.ftp_growth_curve.__wrapped__" if hasattr(ftp_growth_curve, "__wrapped__") else "wko5.pdcurve.rolling_ftp", return_value=synthetic):
        with patch("wko5.pdcurve.rolling_ftp", return_value=synthetic):
            result = ftp_growth_curve(window_days=90, step_days=30)
    assert result is not None
    expected_keys = {"slope", "intercept", "r_squared", "improvement_rate_w_per_year",
                     "plateau_detected", "growth_phase", "training_age_weeks", "data_points"}
    assert expected_keys.issubset(result.keys())


def test_ftp_growth_curve_plateau_detection():
    """plateau_detected should be True when FTP is essentially flat."""
    # Flat FTP history — rate will be near zero
    dates = pd.date_range("2020-01-01", periods=10, freq="30D")
    flat_df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "mFTP": [280.0] * 10})
    with patch("wko5.pdcurve.rolling_ftp", return_value=flat_df):
        result = ftp_growth_curve(window_days=90, step_days=30)
    assert result is not None
    assert result["plateau_detected"] is True
    assert result["growth_phase"] == "plateau"


def test_ftp_growth_curve_insufficient_data_returns_none():
    """ftp_growth_curve should return None when fewer than 3 data points."""
    sparse = pd.DataFrame({"date": ["2023-01-01", "2023-02-01"], "mFTP": [250.0, 255.0]})
    with patch("wko5.pdcurve.rolling_ftp", return_value=sparse):
        result = ftp_growth_curve(window_days=90, step_days=30)
    assert result is None


# ── performance_trend tests ───────────────────────────────────────────────────

def test_performance_trend_returns_dataframe():
    """performance_trend should return a DataFrame with the expected columns."""
    # Build a fake activities DataFrame
    activities_df = pd.DataFrame({
        "id": [101],
        "start_time": ["2024-01-10T09:00:00"],
    })
    # 400 seconds of power data — enough for both 300s and the 1200s col (NaN)
    power_series = pd.Series([250.0] * 400)
    records_df = pd.DataFrame({"power": power_series})

    with patch("wko5.training_load.get_activities", return_value=activities_df), \
         patch("wko5.training_load.get_records", return_value=records_df):
        df = performance_trend(durations=[300, 1200], days_back=30)

    assert isinstance(df, pd.DataFrame)
    assert "date" in df.columns
    assert "activity_id" in df.columns
    assert "best_300s" in df.columns
    assert "best_1200s" in df.columns
    assert len(df) == 1
    assert abs(df.iloc[0]["best_300s"] - 250.0) < 1.0
    # 1200s > 400s of data, so should be NaN
    assert np.isnan(df.iloc[0]["best_1200s"])
