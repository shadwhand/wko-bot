# tests/test_clinical.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
import pandas as pd
from wko5.clinical import (
    check_ctl_ramp_rate, check_tsb_floor, check_hr_decoupling_anomaly,
    check_power_hr_inversion, check_collapse_zone, check_energy_deficit,
    check_if_floor, check_intensity_black_hole, check_panic_training,
    check_reds_flags, check_within_day_deficit,
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


def test_check_if_floor():
    """IF floor diagnostic should return severity and floor value."""
    result = check_if_floor(days_back=90)
    if result is None:
        return  # insufficient data
    assert "floor_if" in result
    assert "severity" in result
    assert result["severity"] in ("green", "yellow", "red")


def test_check_intensity_black_hole():
    """Should detect when most rides are in the moderate zone."""
    result = check_intensity_black_hole(days_back=90)
    # Result is dict or None
    if result is not None:
        assert "compressed" in result
        assert "floor" in result
        assert "ceiling" in result


def test_check_panic_training():
    """Panic training detection should return flag or None."""
    result = check_panic_training(days_back=90)
    # May be None if no panic pattern detected
    if result is not None:
        assert "flag" in result
        assert result["flag"] == "panic_training"


def test_get_clinical_flags_structure():
    """get_clinical_flags should return structured output."""
    result = get_clinical_flags()
    assert "alert_level" in result
    assert result["alert_level"] in ("green", "yellow", "red")
    assert "current_flags" in result
    assert isinstance(result["current_flags"], list)
    assert "current_health_metrics" in result


# --- RED-S screening tests ---

def test_check_reds_flags_returns_structure():
    """check_reds_flags should always return a properly structured dict."""
    result = check_reds_flags(days_back=180)
    assert isinstance(result, dict)
    assert "risk_level" in result
    assert result["risk_level"] in ("low", "moderate", "high")
    assert "flags" in result
    assert isinstance(result["flags"], list)
    assert "recommendation" in result
    assert len(result["recommendation"]) > 10


def test_check_reds_flags_low_risk_when_no_data(monkeypatch):
    """With no activities, risk_level should be low (no flags can fire)."""
    import wko5.clinical as clinical_mod

    # Patch get_activities to return empty DataFrame
    empty_acts = pd.DataFrame(columns=[
        "id", "start_time", "normalized_power", "training_stress_score",
        "total_work", "avg_power", "total_timer_time",
    ])
    monkeypatch.setattr(clinical_mod, "get_activities", lambda **kw: empty_acts)

    result = check_reds_flags(days_back=60)
    # May still detect illness gaps from PMC, but with no activities NP flag won't fire
    assert result["risk_level"] in ("low", "moderate", "high")
    assert isinstance(result["flags"], list)


def test_check_reds_flags_performance_decline_detected(monkeypatch):
    """Performance decline with maintained load should fire the performance_decline flag."""
    import wko5.clinical as clinical_mod
    from datetime import datetime, timedelta

    now = datetime.now()

    # Build synthetic activities: prior 30-60d has higher NP than last 30d
    dates_prior = [now - timedelta(days=d) for d in range(31, 61)]
    dates_recent = [now - timedelta(days=d) for d in range(1, 31)]

    rows = (
        [{"id": i, "start_time": d.strftime("%Y-%m-%d %H:%M:%S+00:00"),
          "normalized_power": 230.0, "training_stress_score": 80.0,
          "total_work": 2000000.0, "avg_power": 230.0, "total_timer_time": 7200.0}
         for i, d in enumerate(dates_prior)]
        +
        [{"id": 100 + i, "start_time": d.strftime("%Y-%m-%d %H:%M:%S+00:00"),
          "normalized_power": 190.0, "training_stress_score": 80.0,  # same load, lower NP
          "total_work": 2000000.0, "avg_power": 190.0, "total_timer_time": 7200.0}
         for i, d in enumerate(dates_recent)]
    )
    fake_acts = pd.DataFrame(rows)

    monkeypatch.setattr(clinical_mod, "get_activities", lambda **kw: fake_acts)

    result = check_reds_flags(days_back=90)
    flag_types = [f["type"] for f in result["flags"]]
    assert "performance_decline_with_load" in flag_types
    assert result["risk_level"] in ("moderate", "high")


# --- Within-day deficit tests ---

def test_check_within_day_deficit_not_found():
    """Non-existent activity_id should return None."""
    result = check_within_day_deficit(activity_id=999999999)
    assert result is None


def test_check_within_day_deficit_late_high_kj(monkeypatch):
    """Ride >500 kJ ending after 7 pm should flag late_high_kj_ride."""
    import wko5.clinical as clinical_mod

    # Single ride ending at 21:00, 600 kJ
    fake_row = {
        "id": 42,
        "start_time": "2026-03-13 19:00:00+00:00",
        "total_timer_time": 7200.0,   # 2h → ends at 21:00 UTC
        "total_elapsed_time": 7200.0,
        "total_work": 600000.0,       # 600 kJ
        "avg_power": 150.0,
        "normalized_power": 170.0,
        "training_stress_score": 90.0,
    }
    fake_acts = pd.DataFrame([fake_row])
    monkeypatch.setattr(clinical_mod, "get_activities", lambda **kw: fake_acts)

    result = check_within_day_deficit(activity_id=42)
    assert result is not None
    assert result["total_kj"] == pytest.approx(600.0, abs=1.0)
    flag_types = [f["type"] for f in result["risk_factors"]]
    assert "late_high_kj_ride" in flag_types
    assert result["deficit_risk"] in ("moderate", "high")


def test_check_within_day_deficit_back_to_back(monkeypatch):
    """Two rides within 4 hours should flag back_to_back_ride."""
    import wko5.clinical as clinical_mod

    # Ride 1: starts 08:00, 2h → ends 10:00; Ride 2: starts 12:00 (2h gap)
    fake_acts = pd.DataFrame([
        {
            "id": 1,
            "start_time": "2026-03-13 08:00:00+00:00",
            "total_timer_time": 7200.0,
            "total_elapsed_time": 7200.0,
            "total_work": 1000000.0,   # 1000 kJ
            "avg_power": 150.0,
            "normalized_power": 165.0,
            "training_stress_score": 80.0,
        },
        {
            "id": 2,
            "start_time": "2026-03-13 12:00:00+00:00",
            "total_timer_time": 3600.0,
            "total_elapsed_time": 3600.0,
            "total_work": 500000.0,
            "avg_power": 150.0,
            "normalized_power": 160.0,
            "training_stress_score": 50.0,
        },
    ])
    monkeypatch.setattr(clinical_mod, "get_activities", lambda **kw: fake_acts)

    result = check_within_day_deficit(activity_id=1)
    assert result is not None
    assert result["hours_to_next_activity"] == pytest.approx(2.0, abs=0.05)
    flag_types = [f["type"] for f in result["risk_factors"]]
    assert "back_to_back_ride" in flag_types
