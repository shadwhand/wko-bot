import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.clean import clean_power, clean_records


def test_spike_removal():
    """Power readings >2000W should be replaced with interpolated values."""
    s = pd.Series([200, 210, 3000, 220, 230])
    cleaned = clean_power(s)
    assert cleaned[2] < 2000
    assert cleaned[2] == 215.0  # interpolated between 210 and 220


def test_spike_at_start():
    """Spike at start should use forward fill."""
    s = pd.Series([5000, 200, 210])
    cleaned = clean_power(s)
    assert cleaned[0] == 200.0


def test_spike_at_end():
    """Spike at end should use backward fill."""
    s = pd.Series([200, 210, 5000])
    cleaned = clean_power(s)
    assert cleaned[2] == 210.0


def test_nan_dropout_short_gap():
    """NaN gaps <=5 samples should be forward-filled."""
    s = pd.Series([200.0, 210.0, np.nan, np.nan, 230.0, 240.0])
    cleaned = clean_power(s)
    assert cleaned[2] == 210.0  # forward filled
    assert cleaned[3] == 210.0


def test_nan_dropout_long_gap():
    """NaN gaps >5 samples should remain NaN."""
    s = pd.Series([200.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 300.0])
    cleaned = clean_power(s)
    assert np.isnan(cleaned[3])  # still NaN (gap of 6)


def test_zeros_preserved():
    """Zero power (coasting) should be kept as-is."""
    s = pd.Series([200, 0, 0, 0, 200])
    cleaned = clean_power(s)
    assert cleaned[1] == 0
    assert cleaned[2] == 0


def test_clean_records_has_power_column():
    """clean_records should clean the power column."""
    df = pd.DataFrame({
        "power": [200, 3000, 210, 220],
        "heart_rate": [120, 121, 122, 123],
        "timestamp": ["t1", "t2", "t3", "t4"],
    })
    cleaned = clean_records(df)
    assert cleaned["power"][1] < 2000
