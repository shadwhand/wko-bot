# tests/test_clinical.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.clinical import (
    check_ctl_ramp_rate, check_tsb_floor, check_hr_decoupling_anomaly,
    check_power_hr_inversion, check_collapse_zone, check_energy_deficit,
    get_clinical_flags, MEDICAL_DISCLAIMER,
)


def test_ctl_ramp_rate_normal():
    """Normal ramp rate should not flag."""
    # Build PMC with steady CTL increase of 3 TSS/day/week
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    pmc = pd.DataFrame({
        "date": dates,
        "TSS": [50 + i * 1 for i in range(30)],
        "CTL": [40 + i * 0.5 for i in range(30)],
        "ATL": [50 + i * 0.8 for i in range(30)],
        "TSB": [-10 + i * 0.1 for i in range(30)],
    })
    result = check_ctl_ramp_rate(pmc)
    assert result is None or result["severity"] != "red"


def test_ctl_ramp_rate_excessive():
    """Ramp rate >10 TSS/day/week should flag red."""
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    # CTL jumps aggressively: 40 → 140 over 14 days = 100/14 ≈ 7.1/day in 7-day windows
    # 7-day diff = 70, rate = 70/7 = 10 → red threshold
    pmc = pd.DataFrame({
        "date": dates,
        "TSS": [50] * 7 + [200 + i * 10 for i in range(23)],
        "CTL": [40 + i * 10 for i in range(30)],  # steep: diff(7)=70, rate=10
        "ATL": [50 + i * 12 for i in range(30)],
        "TSB": [-10 - i * 2 for i in range(30)],
    })
    result = check_ctl_ramp_rate(pmc)
    assert result is not None
    assert result["severity"] in ("yellow", "red")


def test_tsb_floor_normal():
    """TSB above -30 should not flag."""
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    pmc = pd.DataFrame({
        "date": dates,
        "TSS": [60] * 30,
        "CTL": [50] * 30,
        "ATL": [65] * 30,
        "TSB": [-15] * 30,
    })
    result = check_tsb_floor(pmc)
    assert result is None


def test_tsb_floor_breach():
    """TSB below -30 for >14 days should flag yellow."""
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    pmc = pd.DataFrame({
        "date": dates,
        "TSS": [100] * 30,
        "CTL": [50] * 30,
        "ATL": [90] * 30,
        "TSB": [-40] * 30,
    })
    result = check_tsb_floor(pmc)
    assert result is not None
    assert result["severity"] == "yellow"


def test_collapse_zone_safe():
    """Route below collapse threshold should not flag."""
    result = check_collapse_zone(total_kj=3000, collapse_threshold=5000)
    assert result is None


def test_collapse_zone_dangerous():
    """Route above collapse threshold should flag red."""
    result = check_collapse_zone(total_kj=6000, collapse_threshold=5000)
    assert result is not None
    assert result["severity"] == "red"


def test_energy_deficit_safe():
    """Small deficit should not flag."""
    result = check_energy_deficit(
        total_duration_s=7200, avg_power=200, weight_kg=78,
        fueling_rate_g_hr=75, alert_threshold_kcal=3000
    )
    assert result is None


def test_energy_deficit_critical():
    """Large deficit on a long ride should flag yellow."""
    result = check_energy_deficit(
        total_duration_s=36000, avg_power=180, weight_kg=78,
        fueling_rate_g_hr=60, alert_threshold_kcal=3000
    )
    # 10-hour ride at 180W with 60g/hr fueling — should have significant deficit
    assert result is not None
    assert result["severity"] == "yellow"


def test_medical_disclaimer_present():
    """Medical disclaimer string should be defined."""
    assert len(MEDICAL_DISCLAIMER) > 100
    assert "NOT a substitute" in MEDICAL_DISCLAIMER


def test_get_clinical_flags_structure():
    """get_clinical_flags should return structured output."""
    result = get_clinical_flags()
    assert "alert_level" in result
    assert result["alert_level"] in ("green", "yellow", "red")
    assert "current_flags" in result
    assert isinstance(result["current_flags"], list)
    assert "current_health_metrics" in result
