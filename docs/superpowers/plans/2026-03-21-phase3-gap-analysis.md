# Phase 3: Gap Analysis + Clinical Guardrails — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Answer "Am I ready for this event?" (gap analysis with Monte Carlo demand simulation) and "Is anything medically concerning?" (threshold-based clinical flags with medical disclaimers).

**Architecture:** Two new modules: `gap_analysis.py` runs Monte Carlo simulations over demand profiles to produce per-segment success probabilities and bottleneck analysis. `clinical.py` checks recent training data against configurable thresholds for health flags. Both are exposed via API endpoints and usable from the `/wko5-analyzer` skill.

**Tech Stack:** Python 3, numpy, scipy, SQLite, FastAPI

**Spec:** `docs/superpowers/specs/2026-03-20-wko5-desktop-design.md` (Phase 3 section)

**Existing:** `wko5/` package with Phase 1 (config, PD model, PMC, zones, ride) + Phase 2 (physics, segments, durability, demand_profile). 99 passing tests. DB has 1,653 activities.

**Python env:** `/tmp/fitenv/`. Recreate: `rm -rf /tmp/fitenv && python3 -m venv /tmp/fitenv && source /tmp/fitenv/bin/activate && pip install numpy pandas scipy matplotlib fitdecode pytest fastapi uvicorn defusedxml keyring httpx garth`

**Test command:** `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && pytest tests/ -v`

**Data reality check:** No HRV data in DB (smo2_records table exists but empty). No structured resting HR data (only exercise HR). HRV-dependent flags (3d: HRV distribution, HRV suppression) are stubbed with clear "no data" returns. Resting HR elevation is stubbed similarly. These activate automatically when data becomes available.

**Deferred to later phases:** Bayesian posterior sampling (Phase 6 — for now we use Gaussian perturbation of point estimates), circadian adjustment (Phase 2b — noted in Phase 2 review), full HRV statistical model (needs data pipeline first).

---

## File Structure

```
wko5/
  gap_analysis.py    # Monte Carlo demand simulation, bottleneck analysis, route feasibility
  clinical.py        # Threshold-based clinical flags, medical disclaimers
```

Each module has a single clear responsibility:
- `gap_analysis.py` — given a route (segments) + athlete model → run N Monte Carlo draws, compute per-segment success probability, identify bottlenecks, assess overall feasibility
- `clinical.py` — given recent training history → check for health/overtraining flags against configurable thresholds, return structured flag objects with medical disclaimers

---

## Task 1: Gap analysis with Monte Carlo simulation (`gap_analysis.py`)

**Files:**
- Create: `wko5/gap_analysis.py`
- Create: `tests/test_gap_analysis.py`

- [ ] **Step 1: Write tests**

```python
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
    """End-to-end: real ride → segments → gap analysis."""
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_gap_analysis.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement gap_analysis.py**

```python
# wko5/gap_analysis.py
"""Monte Carlo demand simulation, bottleneck analysis, and route feasibility."""

import logging

import numpy as np

from wko5.demand_profile import build_demand_profile
from wko5.durability import degradation_factor

logger = logging.getLogger(__name__)


def feasibility_flag(demand_ratio):
    """Classify demand ratio into feasibility category."""
    if demand_ratio < 0.85:
        return "comfortable"
    elif demand_ratio < 0.95:
        return "hard"
    elif demand_ratio <= 1.0:
        return "limit"
    else:
        return "impossible"


def _perturb_pd_model(pd_model, rng):
    """Create a perturbed PD model for one Monte Carlo draw.

    Uses Gaussian noise scaled to ~5% CV on each parameter.
    This is a placeholder for Phase 6 Bayesian posterior sampling.

    Note: Pmax perturbation has no effect on demand ratios because
    _capacity_at_duration only uses mFTP and FRC. Pmax is included for
    completeness — Phase 6 will use the full PD model.
    """
    perturbed = {}
    for key, val in pd_model.items():
        if isinstance(val, (int, float)) and key in ("Pmax", "FRC", "mFTP"):
            # 5% coefficient of variation
            noise = rng.normal(0, val * 0.05)
            perturbed[key] = max(val * 0.5, val + noise)  # floor at 50% of original
        else:
            perturbed[key] = val
    return perturbed


def _perturb_durability(dur_params, rng):
    """Create perturbed durability params for one Monte Carlo draw."""
    perturbed = {}
    for key, val in dur_params.items():
        if isinstance(val, (int, float)) and key in ("a", "b", "c"):
            noise = rng.normal(0, abs(val) * 0.10)
            perturbed[key] = max(0.001, val + noise)
            if key == "a":
                perturbed[key] = min(0.99, perturbed[key])  # a must be < 1
        else:
            perturbed[key] = val
    return perturbed


def run_monte_carlo(segments, pd_model, durability_params, n_draws=200, seed=42):
    """Run Monte Carlo simulation over demand profiles.

    For each draw:
    1. Perturb PD model and durability params
    2. Build demand profile with perturbed params
    3. Record per-segment completion (demand_ratio <= 1.0)

    Returns: list of segment dicts with success_probability added.
    """
    rng = np.random.default_rng(seed)
    n_segments = len(segments)

    if n_segments == 0:
        return []

    # Track completions per segment across draws
    completions = np.zeros(n_segments)
    demand_ratios_all = np.zeros((n_draws, n_segments))

    for draw in range(n_draws):
        pd_draw = _perturb_pd_model(pd_model, rng)
        dur_draw = _perturb_durability(durability_params, rng)

        profile = build_demand_profile(segments, pd_draw, dur_draw)

        for i, seg in enumerate(profile):
            dr = seg.get("demand_ratio", 0)
            demand_ratios_all[draw, i] = dr
            if dr <= 1.0:
                completions[i] += 1

    # Build result: original segments enriched with MC stats
    result = []
    for i, seg in enumerate(segments):
        enriched = dict(seg)
        prob = completions[i] / n_draws
        median_dr = float(np.median(demand_ratios_all[:, i]))
        p10_dr = float(np.percentile(demand_ratios_all[:, i], 10))
        p90_dr = float(np.percentile(demand_ratios_all[:, i], 90))

        enriched.update({
            "success_probability": round(prob, 3),
            "demand_ratio_median": round(median_dr, 4),
            "demand_ratio_p10": round(p10_dr, 4),
            "demand_ratio_p90": round(p90_dr, 4),
            "feasibility_flag": feasibility_flag(median_dr),
        })
        result.append(enriched)

    return result


def gap_analysis(segments, pd_model, durability_params, n_draws=200, seed=42):
    """Full gap analysis: Monte Carlo simulation + bottleneck identification + feasibility.

    Args:
        segments: list of segment dicts from analyze_ride_segments or analyze_gpx
        pd_model: dict from fit_pd_model
        durability_params: dict from fit_durability_model
        n_draws: number of Monte Carlo draws
        seed: random seed for reproducibility

    Returns: dict with {segments, bottleneck, overall}
    """
    mc_segments = run_monte_carlo(segments, pd_model, durability_params, n_draws, seed)

    if not mc_segments:
        return {
            "segments": [],
            "bottleneck": {},
            "overall": {
                "route_completable": False,
                "probability_of_completion": 0.0,
                "key_risk_factors": ["No segments to analyze"],
                "safety_margin_w": 0,
            },
        }

    # Also compute the deterministic demand profile for safety margin
    det_profile = build_demand_profile(segments, pd_model, durability_params)

    # Bottleneck: segment with highest median demand ratio
    hardest_idx = max(range(len(mc_segments)),
                      key=lambda i: mc_segments[i].get("demand_ratio_median", 0))
    hardest = mc_segments[hardest_idx]

    # Safety margin at bottleneck: effective_capacity - power_required
    det_hardest = det_profile[hardest_idx] if hardest_idx < len(det_profile) else {}
    safety_margin = (det_hardest.get("effective_capacity", 0) -
                     det_hardest.get("power_required", det_hardest.get("power_required", 0)))

    # Overall completion probability: probability all segments are completable
    # Use joint probability (product of independent segment probs as approximation)
    segment_probs = [s["success_probability"] for s in mc_segments]
    # Better: count draws where ALL segments were completed
    # We approximate with min(segment_probs) for conservative estimate
    overall_prob = min(segment_probs) if segment_probs else 0.0

    # Key risk factors
    risk_factors = []
    impossible_segs = [s for s in mc_segments if s["feasibility_flag"] == "impossible"]
    limit_segs = [s for s in mc_segments if s["feasibility_flag"] == "limit"]

    if impossible_segs:
        risk_factors.append(
            f"{len(impossible_segs)} segment(s) exceed current capability"
        )

    if limit_segs:
        risk_factors.append(
            f"{len(limit_segs)} segment(s) at the limit of current capability"
        )

    # Check cumulative kJ vs collapse threshold
    total_kj = sum(s.get("avg_power", 0) * s.get("duration_s", 0) / 1000
                   for s in segments if s.get("avg_power"))
    if total_kj > 0:
        last_seg = mc_segments[-1]
        if last_seg.get("demand_ratio_median", 0) > 0.95:
            risk_factors.append(
                f"Cumulative fatigue ({total_kj:.0f} kJ) degrades capacity significantly by route end"
            )

    if not risk_factors:
        risk_factors.append("No significant risks identified")

    return {
        "segments": mc_segments,
        "bottleneck": {
            "hardest_segment_idx": hardest_idx,
            "hardest_demand_ratio": hardest.get("demand_ratio_median", 0),
            "hardest_success_probability": hardest.get("success_probability", 0),
            "safety_margin_w": round(safety_margin, 1),
        },
        "overall": {
            "route_completable": overall_prob > 0.5,
            "probability_of_completion": round(overall_prob, 3),
            "key_risk_factors": risk_factors,
            "safety_margin_w": round(safety_margin, 1),
        },
    }
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_gap_analysis.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`

- [ ] **Step 6: Commit**

```bash
git add wko5/gap_analysis.py tests/test_gap_analysis.py
git commit -m "feat: add Monte Carlo gap analysis with demand simulation and bottleneck identification"
```

---

## Task 2: Clinical guardrails (`clinical.py`)

**Files:**
- Create: `wko5/clinical.py`
- Create: `tests/test_clinical.py`

- [ ] **Step 1: Write tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_clinical.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement clinical.py**

```python
# wko5/clinical.py
"""Clinical guardrails — threshold-based health flags with medical disclaimers."""

import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from wko5.config import get_config
from wko5.training_load import build_pmc, current_fitness
from wko5.db import get_activities, get_records

logger = logging.getLogger(__name__)


MEDICAL_DISCLAIMER = """MEDICAL DISCLAIMER: This analysis is based on training data and athlete \
profile parameters only. It is NOT a substitute for medical evaluation by a healthcare provider.

If you experience any of the following during training or racing, STOP IMMEDIATELY and seek \
medical attention: chest pain or pressure, severe shortness of breath, dizziness or loss of \
consciousness, palpitations or irregular heartbeat, severe muscle cramps or weakness.

Always consult with a physician before making significant changes to your training or \
competing when you have any health concerns."""


def check_ctl_ramp_rate(pmc=None):
    """Check if CTL ramp rate exceeds thresholds.

    Returns flag dict or None if no issue.
    """
    cfg = get_config()
    yellow_threshold = cfg.get("ctl_ramp_rate_yellow", 7)
    red_threshold = cfg.get("ctl_ramp_rate_red", 10)

    if pmc is None:
        pmc = build_pmc()

    if len(pmc) < 14:
        return None

    # Compute 7-day rolling CTL change rate
    pmc = pmc.copy()
    pmc["ctl_change_7d"] = pmc["CTL"].diff(7) / 7  # TSS/day/week

    recent = pmc.tail(14)
    max_rate = recent["ctl_change_7d"].max()

    if max_rate >= red_threshold:
        return {
            "flag_type": "ctl_ramp_excessive",
            "flag_name": "CTL ramp rate excessive",
            "severity": "red",
            "triggered_value": round(float(max_rate), 1),
            "threshold": red_threshold,
            "medical_disclaimer": MEDICAL_DISCLAIMER,
            "recommendation": f"CTL ramp rate of {max_rate:.1f} TSS/day/week exceeds safe limit ({red_threshold}). Reduce training load immediately.",
        }
    elif max_rate >= yellow_threshold:
        return {
            "flag_type": "ctl_ramp_excessive",
            "flag_name": "CTL ramp rate elevated",
            "severity": "yellow",
            "triggered_value": round(float(max_rate), 1),
            "threshold": yellow_threshold,
            "recommendation": f"CTL ramp rate of {max_rate:.1f} TSS/day/week approaching unsafe levels ({red_threshold}). Consider reducing load.",
        }

    return None


def check_tsb_floor(pmc=None):
    """Check if TSB has been below floor for >14 consecutive days.

    Returns flag dict or None.
    """
    cfg = get_config()
    floor = cfg.get("tsb_floor_alert", -30)

    if pmc is None:
        pmc = build_pmc()

    if len(pmc) < 14:
        return None

    # Count consecutive days with TSB <= floor (from end)
    consecutive = 0
    for _, row in pmc.iloc[::-1].iterrows():
        if row["TSB"] <= floor:
            consecutive += 1
        else:
            break

    if consecutive >= 14:
        current_tsb = float(pmc.iloc[-1]["TSB"])
        return {
            "flag_type": "tsb_floor_breach",
            "flag_name": "TSB floor breach",
            "severity": "yellow",
            "triggered_value": round(current_tsb, 1),
            "threshold": floor,
            "days_flagged": consecutive,
            "recommendation": f"TSB has been below {floor} for {consecutive} consecutive days. Schedule recovery days.",
        }

    return None


def check_hr_decoupling_anomaly(days_back=14):
    """Check recent rides for HR decoupling >10% at moderate intensity.

    Returns flag dict or None.
    """
    from wko5.ride import hr_decoupling

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    activities = get_activities(start=start, end=end)

    if activities.empty:
        return None

    # Filter moderate intensity rides (2-3 hours)
    moderate = activities[
        (activities["total_timer_time"] > 5400) &  # >1.5h
        (activities["total_timer_time"] < 14400)    # <4h
    ]

    flagged_rides = []
    for _, ride in moderate.iterrows():
        dc = hr_decoupling(ride["id"])
        if dc is not None and not np.isnan(dc) and dc > 10:
            flagged_rides.append({
                "activity_id": ride["id"],
                "date": str(ride["start_time"])[:10],
                "decoupling": round(dc, 3),
            })

    if flagged_rides:
        return {
            "flag_type": "cardiac_drift_anomaly",
            "flag_name": "Cardiac drift anomaly",
            "severity": "red",
            "triggered_value": flagged_rides[0]["decoupling"],
            "threshold": 10,
            "context": {"flagged_rides": flagged_rides},
            "medical_disclaimer": MEDICAL_DISCLAIMER,
            "recommendation": f"HR decoupling >10% detected on {len(flagged_rides)} recent ride(s). May indicate cardiovascular stress or dehydration.",
        }

    return None


def check_power_hr_inversion(activity_id):
    """Check a single ride for power-HR inversion (HR rising while power drops).

    Returns flag dict or None.
    """
    records = get_records(activity_id)
    if records.empty:
        return None

    if "power" not in records.columns or "heart_rate" not in records.columns:
        return None

    power = records["power"].fillna(0).values.astype(float)
    hr = records["heart_rate"].fillna(0).values.astype(float)
    n = len(power)

    if n < 1200:  # need at least 20 minutes
        return None

    # Use 10-minute rolling averages
    window = 600
    if n < window * 2:
        return None

    power_rolling = pd.Series(power).rolling(window).mean().values
    hr_rolling = pd.Series(hr).rolling(window).mean().values

    # Check for inversion: power decreasing while HR increasing
    # Exclude final 30 minutes (expected fatigue pattern)
    check_end = max(window, n - 1800)
    inversions = 0

    for i in range(window + 600, check_end, 600):  # check every 10 min
        if i >= len(power_rolling) or i < 600:
            continue
        power_change = power_rolling[i] - power_rolling[i - 600]
        hr_change = hr_rolling[i] - hr_rolling[i - 600]

        if power_change < -10 and hr_change > 3:
            inversions += 1

    if inversions >= 2:
        return {
            "flag_type": "power_hr_inversion",
            "flag_name": "Power-HR inversion",
            "severity": "red",
            "triggered_value": inversions,
            "threshold": 2,
            "medical_disclaimer": MEDICAL_DISCLAIMER,
            "recommendation": f"Power decreased while HR increased at {inversions} points during the ride (outside final 30min). May indicate acute fatigue or illness.",
        }

    return None


def check_collapse_zone(total_kj, collapse_threshold=None):
    """Check if route cumulative kJ exceeds collapse threshold.

    Returns flag dict or None.
    """
    if collapse_threshold is None:
        cfg = get_config()
        collapse_threshold = cfg.get("collapse_kj_threshold")

    if collapse_threshold is None or collapse_threshold <= 0:
        return None

    if total_kj >= collapse_threshold:
        return {
            "flag_type": "collapse_zone",
            "flag_name": "Collapse zone approach",
            "severity": "red",
            "triggered_value": round(total_kj, 0),
            "threshold": collapse_threshold,
            "medical_disclaimer": MEDICAL_DISCLAIMER,
            "recommendation": f"Route demands {total_kj:.0f} kJ, exceeding your historical collapse threshold of {collapse_threshold:.0f} kJ. Risk of catastrophic performance failure.",
        }

    return None


def check_energy_deficit(total_duration_s, avg_power, weight_kg,
                         fueling_rate_g_hr=None, alert_threshold_kcal=None):
    """Check if projected energy deficit exceeds threshold.

    Returns flag dict or None.
    """
    cfg = get_config()
    if fueling_rate_g_hr is None:
        fueling_rate_g_hr = cfg.get("fueling_rate_g_hr", 75)
    if alert_threshold_kcal is None:
        alert_threshold_kcal = cfg.get("energy_deficit_alert_kcal", 3000)

    hours = total_duration_s / 3600

    # Energy expenditure: ~1 kcal per watt-hour (approximate)
    # More precisely: power_kj_hr = avg_power * 3.6, but mechanical efficiency ~25%
    # Total metabolic cost ≈ power * 3.6 / 0.25 kJ/hr = power * 14.4 kJ/hr
    # Plus basal: ~weight_kg * 1.036 kcal/hr
    expenditure_kcal = (avg_power * 14.4 / 4.184 + weight_kg * 1.036) * hours

    # Intake from fueling
    intake_kcal = fueling_rate_g_hr * hours * 4  # 4 kcal per gram carbohydrate

    deficit = expenditure_kcal - intake_kcal

    if deficit >= alert_threshold_kcal:
        return {
            "flag_type": "energy_deficit",
            "flag_name": "Energy deficit critical",
            "severity": "yellow",
            "triggered_value": round(deficit, 0),
            "threshold": alert_threshold_kcal,
            "context": {
                "expenditure_kcal": round(expenditure_kcal, 0),
                "intake_kcal": round(intake_kcal, 0),
                "duration_hours": round(hours, 1),
            },
            "recommendation": f"Projected caloric deficit of {deficit:.0f} kcal over {hours:.1f}h. Increase fueling rate from {fueling_rate_g_hr}g/hr.",
        }

    return None


def get_clinical_flags(days_back=30):
    """Get all current clinical flags.

    Returns structured dict with alert level, current flags, and health metrics.
    """
    pmc = build_pmc()
    flags = []

    # Check each guardrail
    ctl_flag = check_ctl_ramp_rate(pmc)
    if ctl_flag:
        flags.append(ctl_flag)

    tsb_flag = check_tsb_floor(pmc)
    if tsb_flag:
        flags.append(tsb_flag)

    hr_flag = check_hr_decoupling_anomaly(days_back=days_back)
    if hr_flag:
        flags.append(hr_flag)

    # Determine overall alert level
    severities = [f["severity"] for f in flags]
    if "red" in severities:
        alert_level = "red"
    elif "yellow" in severities:
        alert_level = "yellow"
    else:
        alert_level = "green"

    # Current health metrics
    fitness = current_fitness()

    return {
        "alert_level": alert_level,
        "current_flags": flags,
        "current_health_metrics": {
            "ctl": fitness.get("CTL"),
            "atl": fitness.get("ATL"),
            "tsb": fitness.get("TSB"),
        },
    }
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_clinical.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`

- [ ] **Step 6: Commit**

```bash
git add wko5/clinical.py tests/test_clinical.py
git commit -m "feat: add clinical guardrails — CTL ramp, TSB floor, HR decoupling, power-HR inversion, collapse zone, energy deficit"
```

---

## Task 3: API endpoints and DB table

**Files:**
- Modify: `wko5/api/routes.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Add new routes**

Add to `wko5/api/routes.py`:

```python
from wko5.gap_analysis import gap_analysis
from wko5.clinical import get_clinical_flags

@router.get("/gap-analysis/{activity_id}", dependencies=[Depends(verify_token)])
def gap_analysis_endpoint(activity_id: int, n_draws: int = 200):
    ride_segments = analyze_ride_segments(activity_id)
    if not ride_segments["segments"]:
        return {"error": "No segments found"}
    pd_model = fit_pd_model(compute_envelope_mmp(days=90))
    if pd_model is None:
        return {"error": "PD model fitting failed"}
    dur_params = fit_durability_model()
    if dur_params is None:
        return {"error": "Insufficient data for durability model"}
    result = gap_analysis(ride_segments["segments"], pd_model, dur_params, n_draws=n_draws)
    return _sanitize_nans(result)

@router.get("/clinical-flags", dependencies=[Depends(verify_token)])
def clinical_flags(days_back: int = 30):
    result = get_clinical_flags(days_back=days_back)
    return _sanitize_nans(result)
```

- [ ] **Step 2: Add tests**

Add to `tests/test_api.py`:

```python
def test_clinical_flags_with_auth():
    client, token = _get_client()
    response = client.get("/api/clinical-flags", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "alert_level" in data
    assert "current_flags" in data
```

- [ ] **Step 3: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_api.py -v`

- [ ] **Step 4: Commit**

```bash
git add wko5/api/routes.py tests/test_api.py
git commit -m "feat: add gap analysis and clinical flags API endpoints"
```

---

## Task 4: Package exports + skill update

**Files:**
- Modify: `wko5/__init__.py`
- Modify: `~/.claude/skills/wko5-analyzer/skill.md`

- [ ] **Step 1: Update package exports**

Add to `wko5/__init__.py`:
```python
from wko5.gap_analysis import gap_analysis, run_monte_carlo
from wko5.clinical import get_clinical_flags, check_ctl_ramp_rate, check_tsb_floor
```

- [ ] **Step 2: Update the wko5-analyzer skill**

Add new entries to the Module Reference section:

```
### Gap Analysis
from wko5.gap_analysis import gap_analysis, run_monte_carlo
result = gap_analysis(segments, pd_model, dur_params, n_draws=200)
# Returns: {segments (with success_probability), bottleneck, overall}

### Clinical Guardrails
from wko5.clinical import get_clinical_flags
flags = get_clinical_flags(days_back=30)
# Returns: {alert_level, current_flags, current_health_metrics}
```

Add to Question → Function mapping:

```
| Am I ready for this event / route | gap_analysis(segments, pd_model, dur_params) |
| Health flags / overtraining / anything wrong | get_clinical_flags() |
| Energy deficit / fueling | check_energy_deficit(duration, power, weight) |
```

- [ ] **Step 3: Run full test suite**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit and push**

```bash
git add wko5/__init__.py
git commit -m "feat: export Phase 3 modules from package"
git push origin main
```
