# tests/test_blocks.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from wko5.blocks import (
    block_stats, weekly_summary, detect_phase, compare_blocks,
    feasibility_projection, set_training_phase, get_training_phases,
)


def test_block_stats_basic():
    """Block stats should return volume, intensity, and power metrics."""
    result = block_stats("2025-01-01", "2025-03-31")
    assert "volume" in result
    assert "intensity" in result
    assert "power" in result
    assert result["volume"]["ride_count"] > 0
    assert result["volume"]["hours"] > 0
    assert result["volume"]["km"] > 0
    assert result["volume"]["kj"] > 0


def test_block_stats_volume():
    """Volume metrics should be reasonable."""
    result = block_stats("2025-01-01", "2025-01-31")
    vol = result["volume"]
    assert 0 < vol["hours"] < 200
    assert 0 < vol["ride_count"] < 60
    assert "elevation_m" in vol


def test_block_stats_intensity():
    """Intensity distribution should sum to ~100%."""
    result = block_stats("2025-06-01", "2025-06-30")
    intensity = result["intensity"]
    if "seiler_zone1_pct" in intensity:
        total = intensity["seiler_zone1_pct"] + intensity["seiler_zone2_pct"] + intensity["seiler_zone3_pct"]
        assert 90 < total < 110, f"Seiler zones sum to {total}%"


def test_block_stats_power():
    """Power metrics should include key durations."""
    result = block_stats("2025-06-01", "2025-08-31")
    power = result["power"]
    assert "avg_power" in power
    assert "avg_np" in power
    assert "avg_if" in power
    assert "avg_tss_per_ride" in power


def test_weekly_summary():
    """Weekly summary should return a DataFrame."""
    df = weekly_summary("2025-06-01", "2025-08-31")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "week" in df.columns
    assert "hours" in df.columns
    assert "tss" in df.columns
    assert "ride_count" in df.columns


def test_detect_phase():
    """Phase detection should return a valid phase."""
    phase = detect_phase("2025-06-01", "2025-06-30")
    assert phase["phase"] in ("base", "build", "peak", "recovery", "unknown")
    assert 0 < phase["confidence"] <= 1.0


def test_compare_blocks():
    """Block comparison should show differences."""
    diff = compare_blocks(
        ("2025-01-01", "2025-03-31"),
        ("2025-04-01", "2025-06-30"),
    )
    assert "volume_change" in diff
    assert "intensity_change" in diff
    assert "power_change" in diff


def test_set_and_get_training_phase():
    """Should store and retrieve coach-assigned phases."""
    set_training_phase("2025-07-01", "2025-08-31", "build", source="coach", notes="targeting fall event")
    phases = get_training_phases("2025-01-01", "2025-12-31")
    assert len(phases) > 0
    coach_phases = [p for p in phases if p["source"] == "coach"]
    assert any(p["phase"] == "build" for p in coach_phases)


def test_feasibility_projection():
    """Feasibility should estimate if CTL target is reachable."""
    result = feasibility_projection(target_ctl=80, weeks_available=12)
    assert "current_ctl" in result
    assert "target_ctl" in result
    assert "feasible" in result
    assert "required_ramp_rate" in result
    assert isinstance(result["feasible"], bool)


def test_block_stats_with_tp_enrichment():
    """Block stats should include TP data when available."""
    result = block_stats("2025-06-01", "2025-06-30")
    if "tp" in result:
        tp = result["tp"]
        assert "prescribed_count" in tp
        assert "compliance_rate" in tp
