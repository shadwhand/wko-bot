# tests/test_ride.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.ride import (
    ride_summary, detect_intervals, lap_analysis,
    hr_decoupling, best_efforts, power_histogram,
)


def test_ride_summary_returns_dict():
    result = ride_summary(1)
    assert isinstance(result, dict)
    assert "avg_power" in result
    assert "np" in result
    assert "duration_s" in result
    assert result["avg_power"] > 0


def test_ride_summary_invalid_id():
    result = ride_summary(999999)
    assert result == {}


def test_detect_intervals():
    result = detect_intervals(1)
    assert isinstance(result, list)
    if result:
        assert "avg_power" in result[0]
        assert "duration_s" in result[0]


def test_lap_analysis():
    result = lap_analysis(1)
    assert isinstance(result, pd.DataFrame)


def test_best_efforts():
    result = best_efforts(1, durations=[60, 300])
    assert isinstance(result, dict)
    if result:
        assert 60 in result
        assert result[60] > 0


def test_power_histogram():
    result = power_histogram(1, bin_width=25)
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_hr_decoupling():
    result = hr_decoupling(1)
    assert isinstance(result, float)
