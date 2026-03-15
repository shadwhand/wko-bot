import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.training_load import compute_np, compute_tss, build_pmc, current_fitness, efficiency_factor


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
