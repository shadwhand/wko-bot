# Pacing + Nutrition Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a durability-aware pacing solver and nutrition engine that takes a ride plan (target time, equipment, fueling plan) and produces per-segment pacing targets, a glycogen/hydration timeline, feed schedule evaluation, and bonk risk assessment.

**Architecture:** Three new modules. `pacing.py` solves for per-segment power/speed given a target time, accounting for durability decay and drafting. `nutrition.py` models energy expenditure, substrate partitioning, glycogen depletion, and hydration from the pacing output + a user-provided nutrition plan. `ride_planner.py` is the top-level orchestrator that chains pacing → nutrition → gap analysis into one actionable output. A `/wko5-nutrition` Claude skill interprets the results conversationally.

**Tech Stack:** Python 3, numpy, scipy (brentq)

**Existing:** `wko5/` package with physics (power equation, speed solver), segments, durability, demand_profile, gap_analysis, clinical. 119 passing tests.

**Research reference:** `docs/research/nutrition-racing.md`, `docs/research/nutrition-ultra.md`, `docs/research/nutrition-modeling.md`

**Python env:** `/tmp/fitenv/`

**Test command:** `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && pytest tests/ -v`

---

## File Structure

```
wko5/
  pacing.py          # Durability-aware pacing solver with CdA/drafting
  nutrition.py       # Energy math, glycogen budget, hydration, feed schedule evaluation
  ride_planner.py    # Top-level: chains pacing → nutrition → gap analysis
```

- `pacing.py` — given segments + ride plan → per-segment power/speed/duration accounting for durability decay and drafting
- `nutrition.py` — given per-segment power timeline + nutrition plan → glycogen state, hydration state, bonk risk, feed schedule gaps
- `ride_planner.py` — given segments + full ride plan (time target, equipment, nutrition) → complete ride assessment

---

## Task 1: Durability-aware pacing solver (`pacing.py`)

**Files:**
- Create: `wko5/pacing.py`
- Create: `tests/test_pacing.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_pacing.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.pacing import solve_pacing, RidePlan


def test_ride_plan_defaults():
    """RidePlan should have sensible defaults for non-config fields."""
    plan = RidePlan(target_riding_hours=10, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert plan.rest_hours == 0
    assert plan.drafting_pct == 0.0
    assert plan.drafting_savings == 0.30
    assert plan.starting_glycogen_g == 500


def test_solve_pacing_flat():
    """Flat route should return uniform power across segments."""
    segments = [
        {"type": "flat", "distance_m": 5000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
        {"type": "flat", "distance_m": 5000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
    ]
    plan = RidePlan(target_riding_hours=1, cda=0.35, weight_rider=78, weight_bike=9)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = solve_pacing(segments, plan, dur_params)
    assert "base_power" in result
    assert "segments" in result
    assert len(result["segments"]) == 2
    for seg in result["segments"]:
        assert "target_power" in seg
        assert "estimated_speed_kmh" in seg
        assert "estimated_duration_s" in seg


def test_solve_pacing_matches_target_time():
    """Total segment time should approximately match target."""
    segments = [
        {"type": "flat", "distance_m": 20000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
        {"type": "climb", "distance_m": 5000, "avg_grade": 0.05, "cumulative_kj_at_start": 0},
        {"type": "descent", "distance_m": 10000, "avg_grade": -0.03, "cumulative_kj_at_start": 0},
    ]
    plan = RidePlan(target_riding_hours=2, cda=0.35, weight_rider=78, weight_bike=9)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = solve_pacing(segments, plan, dur_params)
    total_s = sum(s["estimated_duration_s"] for s in result["segments"])
    target_s = 2 * 3600
    assert abs(total_s - target_s) < 60, f"Off by {abs(total_s - target_s):.0f}s"


def test_pacing_power_fades_with_durability():
    """Later segments should have lower target power due to durability decay."""
    segments = [
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 3000},
    ]
    plan = RidePlan(target_riding_hours=6, cda=0.35, weight_rider=78, weight_bike=9)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = solve_pacing(segments, plan, dur_params)
    p1 = result["segments"][0]["target_power"]
    p2 = result["segments"][1]["target_power"]
    assert p2 < p1, f"Second segment power {p2:.0f}W should be < first {p1:.0f}W"


def test_pacing_with_drafting():
    """Drafting should reduce required power on flat segments."""
    segments = [
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
    ]
    plan_solo = RidePlan(target_riding_hours=2, cda=0.35, weight_rider=78, weight_bike=9, drafting_pct=0.0)
    plan_draft = RidePlan(target_riding_hours=2, cda=0.35, weight_rider=78, weight_bike=9, drafting_pct=0.4, drafting_savings=0.30)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    r_solo = solve_pacing(segments, plan_solo, dur_params)
    r_draft = solve_pacing(segments, plan_draft, dur_params)
    assert r_draft["base_power"] < r_solo["base_power"]


def test_pacing_with_aerobars():
    """Lower CdA (aerobars) should reduce required power."""
    segments = [
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
    ]
    plan_hoods = RidePlan(target_riding_hours=2, cda=0.35, weight_rider=78, weight_bike=9)
    plan_aero = RidePlan(target_riding_hours=2, cda=0.28, weight_rider=78, weight_bike=9)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    r_hoods = solve_pacing(segments, plan_hoods, dur_params)
    r_aero = solve_pacing(segments, plan_aero, dur_params)
    assert r_aero["base_power"] < r_hoods["base_power"]


def test_pacing_with_real_ride():
    """Pacing solver should work with real ride segments."""
    from wko5.segments import analyze_ride_segments
    from wko5.durability import fit_durability_model
    ride = analyze_ride_segments(1628)  # 300km ride
    if not ride["segments"]:
        return
    dur_params = fit_durability_model()
    if dur_params is None:
        return

    plan = RidePlan(target_riding_hours=11, cda=0.28, weight_rider=78, weight_bike=9)
    result = solve_pacing(ride["segments"], plan, dur_params)
    assert 100 < result["base_power"] < 300
    total_h = sum(s["estimated_duration_s"] for s in result["segments"]) / 3600
    assert abs(total_h - 11) < 0.1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_pacing.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement pacing.py**

```python
# wko5/pacing.py
"""Durability-aware pacing solver with CdA and drafting support."""

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import brentq

from wko5.config import get_config
from wko5.physics import power_required, speed_from_power
from wko5.durability import degradation_factor


@dataclass
class RidePlan:
    """Ride plan input — describes how the rider intends to ride."""
    target_riding_hours: float
    rest_hours: float = 0
    cda: float = None            # defaults to config
    crr: float = None            # defaults to config
    weight_rider: float = None   # defaults to config
    weight_bike: float = None    # defaults to config
    drafting_pct: float = 0.0    # fraction of flat/rolling time in draft (0-1)
    drafting_savings: float = 0.30  # aero reduction when drafting
    starting_glycogen_g: float = 500
    nutrition: dict = field(default_factory=dict)

    def __post_init__(self):
        cfg = get_config()
        if self.cda is None:
            self.cda = cfg["cda"]
        if self.crr is None:
            self.crr = cfg["crr"]
        if self.weight_rider is None:
            self.weight_rider = cfg["weight_kg"]
        if self.weight_bike is None:
            self.weight_bike = cfg["bike_weight_kg"]


def _effective_cda(cda, segment_type, drafting_pct, drafting_savings):
    """Compute effective CdA accounting for drafting on flat/rolling segments."""
    if segment_type in ("flat", "rolling", "rolling_descent", "descent") and drafting_pct > 0:
        return cda * (1 - drafting_pct * drafting_savings)
    return cda


def _segment_time(base_power, seg, plan, elapsed_hours, cumulative_kj, dur_params):
    """Compute time for one segment given base power and fatigue state."""
    # Apply durability decay to base power
    deg = degradation_factor(cumulative_kj, elapsed_hours, dur_params)
    target_power = base_power * deg

    # Effective CdA with drafting
    eff_cda = _effective_cda(plan.cda, seg.get("type", "flat"),
                             plan.drafting_pct, plan.drafting_savings)

    # Compute speed at this power on this grade
    v = speed_from_power(
        power=target_power,
        grade=seg.get("avg_grade", 0),
        weight_rider=plan.weight_rider,
        weight_bike=plan.weight_bike,
        cda=eff_cda,
        crr=plan.crr,
    )

    # Cap descent speed at 70 km/h (19.4 m/s) for safety/realism
    MAX_DESCENT_SPEED = 70 / 3.6
    if seg.get("type") in ("descent", "rolling_descent") and v > MAX_DESCENT_SPEED:
        v = MAX_DESCENT_SPEED

    distance_m = seg.get("distance_m", 0)
    if distance_m <= 0 or v <= 0:
        return 0.0, target_power, v

    duration_s = distance_m / v
    return duration_s, target_power, v


def _total_time(base_power, segments, plan, dur_params):
    """Compute total riding time at a given base power."""
    total_s = 0
    elapsed_s = 0
    cumulative_kj = 0

    for seg in segments:
        elapsed_hours = elapsed_s / 3600
        cum_kj = seg.get("cumulative_kj_at_start", cumulative_kj)

        dt, target_p, v = _segment_time(base_power, seg, plan, elapsed_hours, cum_kj, dur_params)

        total_s += dt
        elapsed_s += dt
        cumulative_kj = cum_kj + target_p * dt / 1000

    return total_s


def solve_pacing(segments, plan, dur_params):
    """Solve for the base power that produces the target riding time.

    Base power is the fresh, flat-road power. Actual per-segment power is:
    target_power = base_power * degradation_factor(cumulative_kj, elapsed_hours)

    Uses Brent's method to find the base power where total time = target.

    Args:
        segments: list of segment dicts from analyze_ride_segments or analyze_gpx
        plan: RidePlan with target time, equipment, drafting
        dur_params: dict with {a, b, c} from fit_durability_model

    Returns: dict with base_power and enriched segments
    """
    target_s = plan.target_riding_hours * 3600

    # Binary search on base power
    def residual(bp):
        return _total_time(bp, segments, plan, dur_params) - target_s

    try:
        base_power = brentq(residual, 20, 600, xtol=0.5)
    except ValueError:
        # If no solution in range, find closest
        t_low = _total_time(600, segments, plan, dur_params)
        t_high = _total_time(20, segments, plan, dur_params)
        if t_low > target_s:
            base_power = 600  # even 600W isn't fast enough
        else:
            base_power = 20

    # Build enriched segments with pacing details
    result_segments = []
    elapsed_s = 0
    cumulative_kj = 0

    for seg in segments:
        elapsed_hours = elapsed_s / 3600
        cum_kj = seg.get("cumulative_kj_at_start", cumulative_kj)

        dt, target_p, v = _segment_time(base_power, seg, plan, elapsed_hours, cum_kj, dur_params)

        enriched = dict(seg)
        enriched.update({
            "target_power": round(target_p, 1),
            "estimated_speed_kmh": round(v * 3.6, 1),
            "estimated_duration_s": round(dt, 1),
            "elapsed_hours": round(elapsed_s / 3600, 2),
            "degradation": round(degradation_factor(cum_kj, elapsed_hours, dur_params), 4),
        })
        result_segments.append(enriched)

        elapsed_s += dt
        cumulative_kj = cum_kj + target_p * dt / 1000

    return {
        "base_power": round(base_power, 1),
        "total_riding_time_h": round(elapsed_s / 3600, 2),
        "segments": result_segments,
    }
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_pacing.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`

- [ ] **Step 6: Commit**

```bash
git add wko5/pacing.py tests/test_pacing.py
git commit -m "feat: add durability-aware pacing solver with CdA and drafting support"
```

---

## Task 2: Nutrition engine (`nutrition.py`)

**Files:**
- Create: `wko5/nutrition.py`
- Create: `tests/test_nutrition.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_nutrition.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from wko5.nutrition import (
    energy_expenditure, cho_burn_rate, fat_burn_rate,
    glycogen_timeline, time_to_bonk, sweat_rate, sodium_loss,
    evaluate_nutrition_plan, NutritionPlan, FeedEvent,
)


def test_energy_expenditure_200w():
    """200W at 23% efficiency should be ~715 kcal/hr."""
    ee = energy_expenditure(power_watts=200, efficiency=0.23)
    assert 680 < ee < 750


def test_energy_expenditure_scales_with_power():
    ee1 = energy_expenditure(150)
    ee2 = energy_expenditure(300)
    assert ee2 > ee1 * 1.9  # should roughly double


def test_cho_burn_rate_increases_with_intensity():
    """Higher intensity = more carb burning."""
    cho_low = cho_burn_rate(power_watts=150, ftp=290)
    cho_high = cho_burn_rate(power_watts=260, ftp=290)
    assert cho_high > cho_low * 1.5


def test_fat_burn_rate_peaks_at_moderate_intensity():
    """Fat burning should peak around 55-65% FTP."""
    fat_low = fat_burn_rate(power_watts=100, ftp=290)
    fat_mid = fat_burn_rate(power_watts=175, ftp=290)  # ~60% FTP
    fat_high = fat_burn_rate(power_watts=260, ftp=290)
    assert fat_mid > fat_low
    assert fat_mid > fat_high  # peaks at moderate, drops at high intensity


def test_time_to_bonk_without_fueling():
    """Without fueling at threshold, should bonk in 3-5 hours."""
    ttb = time_to_bonk(power_watts=290, ftp=290, intake_g_hr=0, starting_glycogen_g=500)
    assert 2 < ttb < 6


def test_time_to_bonk_with_fueling():
    """With fueling, bonk time should extend significantly."""
    ttb_none = time_to_bonk(power_watts=200, ftp=290, intake_g_hr=0, starting_glycogen_g=500)
    ttb_fed = time_to_bonk(power_watts=200, ftp=290, intake_g_hr=80, starting_glycogen_g=500)
    assert ttb_fed > ttb_none * 1.5


def test_glycogen_timeline():
    """Glycogen should decrease over time."""
    timeline = glycogen_timeline(
        power_series=[200] * 7200,  # 2 hours at 200W
        ftp=290,
        intake_g_hr=60,
        starting_glycogen_g=500,
    )
    assert len(timeline) > 0
    assert timeline[-1]["glycogen_g"] < 500
    assert timeline[0]["glycogen_g"] == 500


def test_sweat_rate_increases_with_heat():
    """Hotter = more sweat."""
    sr_cool = sweat_rate(power_watts=200, temp_c=15, humidity_pct=50, weight_kg=78)
    sr_hot = sweat_rate(power_watts=200, temp_c=35, humidity_pct=50, weight_kg=78)
    assert sr_hot > sr_cool


def test_sodium_loss():
    """Sodium loss should be proportional to sweat rate."""
    na = sodium_loss(sweat_rate_l_hr=1.0, sweat_na_mmol=45)
    assert 900 < na < 1200  # ~1035 mg at 45 mmol/L


def test_evaluate_nutrition_plan_basic():
    """Evaluate a simple nutrition plan."""
    paced_segments = [
        {"type": "flat", "distance_m": 50000, "target_power": 180,
         "estimated_duration_s": 3600, "elapsed_hours": 0},
        {"type": "climb", "distance_m": 5000, "target_power": 250,
         "estimated_duration_s": 1200, "elapsed_hours": 1},
        {"type": "flat", "distance_m": 50000, "target_power": 170,
         "estimated_duration_s": 3600, "elapsed_hours": 1.33},
    ]
    plan = NutritionPlan(
        baseline_intake_g_hr=60,
        feed_events=[
            FeedEvent(km=50, carbs_g=80, fluid_ml=750),
        ],
        starting_glycogen_g=500,
    )
    result = evaluate_nutrition_plan(paced_segments, plan, ftp=290, temp_c=25)
    assert "glycogen_timeline" in result
    assert "hydration_timeline" in result
    assert "bonk_risk_km" in result
    assert "total_carbs_needed_g" in result
    assert "total_fluid_needed_L" in result
    assert "warnings" in result


def test_evaluate_plan_detects_bonk_risk():
    """A long ride with low fueling should flag bonk risk."""
    # 6 hours at 250W with only 30g/hr
    paced_segments = [
        {"type": "flat", "distance_m": 30000, "target_power": 250,
         "estimated_duration_s": 3600, "elapsed_hours": i}
        for i in range(6)
    ]
    plan = NutritionPlan(baseline_intake_g_hr=30, starting_glycogen_g=500)
    result = evaluate_nutrition_plan(paced_segments, plan, ftp=290, temp_c=20)
    assert result["bonk_risk_km"] is not None
    assert result["bonk_risk_km"] < 180  # should bonk within 180km
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_nutrition.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement nutrition.py**

```python
# wko5/nutrition.py
"""Nutrition engine — energy math, glycogen budget, hydration, feed schedule evaluation."""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Constants
KCAL_PER_G_CHO = 4.0
KCAL_PER_G_FAT = 9.0
KJ_TO_KCAL = 1 / 4.184
NA_MOLECULAR_WEIGHT = 23  # g/mol


@dataclass
class FeedEvent:
    """A planned feeding event at a specific point on the route."""
    km: float
    carbs_g: float = 0
    fluid_ml: float = 0
    sodium_mg: float = 0
    description: str = ""


@dataclass
class NutritionPlan:
    """Rider's nutrition plan for a ride."""
    baseline_intake_g_hr: float = 60    # carbs from gels/drink while riding
    feed_events: List[FeedEvent] = field(default_factory=list)
    starting_glycogen_g: float = 500    # normal diet; 650 if carb loaded
    bottles_capacity_ml: float = 1500
    sweat_na_mmol: float = 45           # individual sweat sodium concentration


def energy_expenditure(power_watts, efficiency=0.23):
    """Compute energy expenditure in kcal/hr from power output.

    EE = P * 3.6 / (GE * 4.184) kcal/hr
    """
    if power_watts <= 0:
        return 80.0  # basal metabolic rate while coasting
    return power_watts * 3.6 / (efficiency * 4.184)


def _cho_fraction(intensity_pct):
    """Fraction of energy from carbohydrate at a given intensity (% of FTP).

    Based on crossover concept. Trained cyclist crossover ~60% FTP.
    """
    # Sigmoid: 0.30 at rest, ~0.50 at 60% FTP, ~0.90 at FTP
    x = max(0, min(intensity_pct, 1.5))
    return 0.30 + 0.65 / (1 + np.exp(-10 * (x - 0.60)))


def cho_burn_rate(power_watts, ftp, efficiency=0.23):
    """Carbohydrate burn rate in g/hr at a given power."""
    ee_kcal_hr = energy_expenditure(power_watts, efficiency)
    intensity = power_watts / ftp if ftp > 0 else 0
    cho_frac = _cho_fraction(intensity)
    return ee_kcal_hr * cho_frac / KCAL_PER_G_CHO


def fat_burn_rate(power_watts, ftp, efficiency=0.23):
    """Fat burn rate in g/hr at a given power."""
    ee_kcal_hr = energy_expenditure(power_watts, efficiency)
    intensity = power_watts / ftp if ftp > 0 else 0
    fat_frac = 1 - _cho_fraction(intensity)
    return ee_kcal_hr * fat_frac / KCAL_PER_G_FAT


def time_to_bonk(power_watts, ftp, intake_g_hr=0, starting_glycogen_g=500,
                 glycogen_critical_g=75, sparing_factor=0.35):
    """Estimate time to bonk (glycogen depletion) in hours.

    Args:
        power_watts: average power
        ftp: functional threshold power
        intake_g_hr: exogenous carb intake rate
        starting_glycogen_g: initial muscle + liver glycogen
        glycogen_critical_g: glycogen level where bonking occurs
        sparing_factor: fraction of exogenous CHO that spares endogenous

    Returns: hours until bonk, or float('inf') if intake matches burn
    """
    burn = cho_burn_rate(power_watts, ftp)
    effective_sparing = intake_g_hr * sparing_factor
    net_drain = burn - effective_sparing

    if net_drain <= 0:
        return float("inf")  # intake covers burn rate

    usable = (starting_glycogen_g - glycogen_critical_g) * 0.80  # ~80% usable
    return usable / net_drain


def glycogen_timeline(power_series, ftp, intake_g_hr=0, starting_glycogen_g=500,
                      glycogen_critical_g=75, sample_interval_s=300):
    """Compute glycogen remaining over time from a power series.

    Args:
        power_series: list/array of per-second power values
        ftp: functional threshold power
        intake_g_hr: baseline carb intake rate
        starting_glycogen_g: initial glycogen
        sample_interval_s: output sampling interval (default 5 min)

    Returns: list of dicts {time_s, time_h, glycogen_g, cho_burned_g, cho_ingested_g}
    """
    glycogen = starting_glycogen_g
    total_burned = 0
    total_ingested = 0
    timeline = [{"time_s": 0, "time_h": 0, "glycogen_g": glycogen,
                 "cho_burned_g": 0, "cho_ingested_g": 0}]

    n = len(power_series)
    for i in range(n):
        power = power_series[i] if power_series[i] is not None else 0

        # Per-second CHO burn
        intensity = power / ftp if ftp > 0 else 0
        ee_kcal_s = energy_expenditure(power) / 3600
        cho_frac = _cho_fraction(intensity)
        cho_burned_s = ee_kcal_s * cho_frac / KCAL_PER_G_CHO

        # Per-second intake (sparing)
        intake_s = intake_g_hr / 3600 * 0.35  # sparing factor

        glycogen = max(0, glycogen - cho_burned_s + intake_s)
        total_burned += cho_burned_s
        total_ingested += intake_g_hr / 3600

        if (i + 1) % sample_interval_s == 0:
            timeline.append({
                "time_s": i + 1,
                "time_h": round((i + 1) / 3600, 2),
                "glycogen_g": round(glycogen, 1),
                "cho_burned_g": round(total_burned, 1),
                "cho_ingested_g": round(total_ingested, 1),
            })

    return timeline


def sweat_rate(power_watts, temp_c=20, humidity_pct=50, weight_kg=78):
    """Estimate sweat rate in L/hr.

    Simplified model based on metabolic heat production and environment.
    """
    # Base sweat from metabolic heat
    heat_watts = power_watts * (1 / 0.23 - 1) if power_watts > 0 else 0
    base_sr = heat_watts / 2426000 * 3600  # latent heat of vaporization, convert to L/hr

    # Temperature modifier
    temp_factor = 0.5 + 0.5 * max(0, (temp_c - 10)) / 25
    temp_factor = min(temp_factor, 1.5)

    # Humidity modifier (less effective evaporation → more sweating)
    humidity_factor = 1.0 + 0.3 * max(0, (humidity_pct / 100 - 0.50)) / 0.50
    humidity_factor = min(humidity_factor, 1.3)

    # Weight modifier
    weight_factor = weight_kg / 75

    sr = base_sr * temp_factor * humidity_factor * weight_factor

    # Clamp to realistic range
    return max(0.3, min(sr, 3.0))


def sodium_loss(sweat_rate_l_hr, sweat_na_mmol=45):
    """Compute sodium loss in mg/hr from sweat rate and concentration."""
    return sweat_rate_l_hr * sweat_na_mmol * NA_MOLECULAR_WEIGHT


def evaluate_nutrition_plan(paced_segments, plan, ftp=None, temp_c=20, humidity_pct=50):
    """Evaluate a nutrition plan against paced segments.

    Takes paced segments (with target_power, estimated_duration_s, elapsed_hours)
    and a NutritionPlan, simulates glycogen and hydration state across the route.

    Returns: dict with glycogen_timeline, hydration_timeline, bonk_risk_km, warnings
    """
    from wko5.config import get_config
    cfg = get_config()
    if ftp is None:
        ftp = cfg["ftp_manual"]

    glycogen = plan.starting_glycogen_g
    fluid_deficit_ml = 0
    sodium_deficit_mg = 0
    cumulative_km = 0
    cumulative_cho_burned = 0
    cumulative_cho_ingested = 0
    bonk_risk_km = None
    glycogen_tl = []
    hydration_tl = []
    warnings = []

    # Index feed events by km
    feed_by_km = sorted(plan.feed_events, key=lambda f: f.km)
    feed_idx = 0

    for seg in paced_segments:
        power = seg.get("target_power", 0)
        duration_s = seg.get("estimated_duration_s", seg.get("duration_s", 0))
        distance_m = seg.get("distance_m", 0)
        duration_h = duration_s / 3600

        # CHO burn for this segment
        cho_burned = cho_burn_rate(power, ftp) * duration_h
        fat_burned = fat_burn_rate(power, ftp) * duration_h

        # Baseline intake for this segment
        cho_ingested = plan.baseline_intake_g_hr * duration_h

        # Check for feed events in this segment's km range
        seg_start_km = cumulative_km / 1000
        seg_end_km = (cumulative_km + distance_m) / 1000
        while feed_idx < len(feed_by_km) and feed_by_km[feed_idx].km <= seg_end_km:
            evt = feed_by_km[feed_idx]
            if evt.km >= seg_start_km:
                cho_ingested += evt.carbs_g
                fluid_deficit_ml -= evt.fluid_ml
                sodium_deficit_mg -= evt.sodium_mg
            feed_idx += 1

        # Glycogen update (sparing from exogenous intake)
        sparing = cho_ingested * 0.35
        glycogen = max(0, glycogen - cho_burned + sparing)
        cumulative_cho_burned += cho_burned
        cumulative_cho_ingested += cho_ingested

        # Hydration update
        sr = sweat_rate(power, temp_c, humidity_pct, cfg["weight_kg"])
        fluid_lost_ml = sr * duration_h * 1000
        fluid_deficit_ml += fluid_lost_ml

        na_lost = sodium_loss(sr, plan.sweat_na_mmol) * duration_h
        sodium_deficit_mg += na_lost

        cumulative_km += distance_m

        # Bonk risk check
        if glycogen <= 75 and bonk_risk_km is None:
            bonk_risk_km = cumulative_km / 1000

        glycogen_tl.append({
            "km": round(cumulative_km / 1000, 1),
            "glycogen_g": round(glycogen, 1),
            "cho_burned_cumulative_g": round(cumulative_cho_burned, 1),
            "cho_ingested_cumulative_g": round(cumulative_cho_ingested, 1),
        })

        hydration_tl.append({
            "km": round(cumulative_km / 1000, 1),
            "fluid_deficit_ml": round(fluid_deficit_ml, 0),
            "sodium_deficit_mg": round(sodium_deficit_mg, 0),
            "dehydration_pct": round(fluid_deficit_ml / (cfg["weight_kg"] * 10), 1),
        })

    # Generate warnings
    total_duration_h = sum(s.get("estimated_duration_s", s.get("duration_s", 0))
                          for s in paced_segments) / 3600

    if bonk_risk_km is not None:
        warnings.append(f"Glycogen critical at km {bonk_risk_km:.0f}. Increase intake or reduce intensity.")

    if hydration_tl and hydration_tl[-1]["dehydration_pct"] > 3.0:
        warnings.append(f"Dehydration reaches {hydration_tl[-1]['dehydration_pct']:.1f}% body mass. Increase fluid intake.")

    # Check for long gaps between feed events
    if len(feed_by_km) >= 2:
        for i in range(1, len(feed_by_km)):
            gap_km = feed_by_km[i].km - feed_by_km[i-1].km
            if gap_km > 60:
                warnings.append(f"Feed gap of {gap_km:.0f}km between km {feed_by_km[i-1].km:.0f} and {feed_by_km[i].km:.0f}. Consider adding a stop.")

    return {
        "glycogen_timeline": glycogen_tl,
        "hydration_timeline": hydration_tl,
        "bonk_risk_km": bonk_risk_km,
        "total_carbs_needed_g": round(cumulative_cho_burned, 0),
        "total_carbs_planned_g": round(cumulative_cho_ingested, 0),
        "total_fluid_needed_L": round(sum(
            sweat_rate(s.get("target_power", 0), temp_c, humidity_pct, cfg["weight_kg"])
            * s.get("estimated_duration_s", s.get("duration_s", 0)) / 3600
            for s in paced_segments
        ), 1),
        "total_sodium_needed_mg": round(sodium_deficit_mg, 0),
        "duration_hours": round(total_duration_h, 1),
        "warnings": warnings,
    }
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_nutrition.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`

- [ ] **Step 6: Commit**

```bash
git add wko5/nutrition.py tests/test_nutrition.py
git commit -m "feat: add nutrition engine — energy math, glycogen budget, hydration, feed schedule evaluation"
```

---

## Task 3: Ride planner orchestrator (`ride_planner.py`)

**Files:**
- Create: `wko5/ride_planner.py`
- Create: `tests/test_ride_planner.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_ride_planner.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wko5.ride_planner import plan_ride
from wko5.pacing import RidePlan
from wko5.nutrition import NutritionPlan, FeedEvent


def test_plan_ride_basic():
    """plan_ride should return pacing, nutrition, and feasibility."""
    segments = [
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
        {"type": "climb", "distance_m": 5000, "avg_grade": 0.05, "cumulative_kj_at_start": 500},
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 800},
    ]
    ride_plan = RidePlan(target_riding_hours=4, cda=0.35, weight_rider=78, weight_bike=9)
    nutrition_plan = NutritionPlan(baseline_intake_g_hr=60)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600}

    result = plan_ride(segments, ride_plan, nutrition_plan, pd_model, dur_params, temp_c=20)
    assert "pacing" in result
    assert "nutrition" in result
    assert "feasibility" in result
    assert "base_power" in result["pacing"]
    assert "glycogen_timeline" in result["nutrition"]
    assert "overall" in result["feasibility"]


def test_plan_ride_with_feed_events():
    """Feed events should be reflected in the nutrition output."""
    segments = [
        {"type": "flat", "distance_m": 100000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
    ]
    ride_plan = RidePlan(target_riding_hours=4)
    nutrition_plan = NutritionPlan(
        baseline_intake_g_hr=60,
        feed_events=[FeedEvent(km=50, carbs_g=100, fluid_ml=750, description="control stop")],
    )
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600}

    result = plan_ride(segments, ride_plan, nutrition_plan, pd_model, dur_params)
    assert result["nutrition"]["total_carbs_planned_g"] > 240  # 60*4 baseline + 100 from stop


def test_plan_ride_with_real_ride():
    """End-to-end with real 300km ride."""
    from wko5.segments import analyze_ride_segments
    from wko5.pdcurve import compute_envelope_mmp, fit_pd_model
    from wko5.durability import fit_durability_model

    ride = analyze_ride_segments(1628)
    if not ride["segments"]:
        return

    pd_model = fit_pd_model(compute_envelope_mmp(days=90))
    dur_params = fit_durability_model()
    if pd_model is None or dur_params is None:
        return

    # Use manual FTP if model underestimates
    if pd_model["mFTP"] < 280:
        pd_model["mFTP"] = 292

    ride_plan = RidePlan(target_riding_hours=11, cda=0.28)
    nutrition_plan = NutritionPlan(
        baseline_intake_g_hr=60,
        feed_events=[
            FeedEvent(km=85, carbs_g=80, fluid_ml=750, description="control 1"),
            FeedEvent(km=170, carbs_g=120, fluid_ml=500, description="store"),
            FeedEvent(km=250, carbs_g=100, fluid_ml=400, description="burrito"),
        ],
    )

    result = plan_ride(ride["segments"], ride_plan, nutrition_plan, pd_model, dur_params, temp_c=25)
    assert result["pacing"]["base_power"] > 100
    assert result["nutrition"]["duration_hours"] > 10
    assert "warnings" in result["nutrition"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_ride_planner.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement ride_planner.py**

```python
# wko5/ride_planner.py
"""Ride planner — chains pacing, nutrition, and gap analysis into one output."""

from wko5.pacing import solve_pacing, RidePlan
from wko5.nutrition import evaluate_nutrition_plan, NutritionPlan
from wko5.gap_analysis import gap_analysis


def plan_ride(segments, ride_plan, nutrition_plan, pd_model, dur_params,
              temp_c=20, humidity_pct=50, n_draws=100):
    """Plan a complete ride: pacing → nutrition → feasibility.

    Args:
        segments: list of segment dicts from analyze_ride_segments or analyze_gpx
        ride_plan: RidePlan with target time, equipment, drafting
        nutrition_plan: NutritionPlan with feed events and baseline intake
        pd_model: dict from fit_pd_model (with mFTP, FRC, etc)
        dur_params: dict from fit_durability_model
        temp_c: ambient temperature
        humidity_pct: ambient humidity
        n_draws: Monte Carlo draws for gap analysis

    Returns: dict with {pacing, nutrition, feasibility}
    """
    # Step 1: Solve pacing
    pacing = solve_pacing(segments, ride_plan, dur_params)

    # Step 2: Map pacing output fields for downstream consumers
    # build_demand_profile expects 'power_required' and 'duration_s'
    for seg in pacing["segments"]:
        seg["power_required"] = seg.get("target_power", seg.get("power_required", 0))
        seg["duration_s"] = seg.get("estimated_duration_s", seg.get("duration_s", 0))

    # Step 3: Evaluate nutrition against paced segments
    nutrition = evaluate_nutrition_plan(
        pacing["segments"], nutrition_plan,
        ftp=pd_model.get("mFTP", 290),
        temp_c=temp_c,
        humidity_pct=humidity_pct,
    )

    # Step 4: Gap analysis on paced segments
    feasibility = gap_analysis(
        pacing["segments"], pd_model, dur_params, n_draws=n_draws,
    )

    return {
        "pacing": pacing,
        "nutrition": nutrition,
        "feasibility": feasibility,
    }
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_ride_planner.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`

- [ ] **Step 6: Commit**

```bash
git add wko5/ride_planner.py tests/test_ride_planner.py
git commit -m "feat: add ride planner — chains pacing, nutrition, and gap analysis"
```

---

## Task 4: API endpoints

**Files:**
- Modify: `wko5/api/routes.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Add new routes**

Add to `wko5/api/routes.py`:

```python
from wko5.pacing import solve_pacing, RidePlan
from wko5.nutrition import NutritionPlan, FeedEvent
from wko5.ride_planner import plan_ride

@router.post("/plan-ride", dependencies=[Depends(verify_token)])
def plan_ride_endpoint(body: dict):
    """Plan a ride with pacing, nutrition, and feasibility analysis."""
    from wko5.segments import analyze_ride_segments
    activity_id = body.get("activity_id")
    if not activity_id:
        return {"error": "activity_id required"}

    ride_segments = analyze_ride_segments(activity_id)
    if not ride_segments["segments"]:
        return {"error": "No segments found"}

    pd_model = fit_pd_model(compute_envelope_mmp(days=90))
    if pd_model is None:
        return {"error": "PD model fitting failed"}

    # Override mFTP with manual if model underestimates
    cfg = get_config()
    if pd_model["mFTP"] < cfg["ftp_manual"] * 0.85:
        pd_model["mFTP"] = cfg["ftp_manual"]

    dur_params = fit_durability_model()
    if dur_params is None:
        return {"error": "Insufficient data for durability model"}

    ride_plan = RidePlan(
        target_riding_hours=body.get("target_riding_hours", 4),
        rest_hours=body.get("rest_hours", 0),
        cda=body.get("cda", cfg["cda"]),
        drafting_pct=body.get("drafting_pct", 0),
        drafting_savings=body.get("drafting_savings", 0.30),
    )

    feed_events = [FeedEvent(**e) for e in body.get("feed_events", [])]
    nutrition_plan = NutritionPlan(
        baseline_intake_g_hr=body.get("baseline_intake_g_hr", cfg["fueling_rate_g_hr"]),
        feed_events=feed_events,
        starting_glycogen_g=body.get("starting_glycogen_g", 500),
    )

    result = plan_ride(
        ride_segments["segments"], ride_plan, nutrition_plan, pd_model, dur_params,
        temp_c=body.get("temp_c", 20),
        humidity_pct=body.get("humidity_pct", 50),
    )
    return _sanitize_nans(result)
```

- [ ] **Step 2: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_api.py -v`

- [ ] **Step 3: Commit**

```bash
git add wko5/api/routes.py tests/test_api.py
git commit -m "feat: add POST /plan-ride API endpoint"
```

---

## Task 5: Package exports + skill update

**Files:**
- Modify: `wko5/__init__.py`
- Create: `~/.claude/skills/wko5-nutrition/skill.md`

- [ ] **Step 1: Update package exports**

Add to `wko5/__init__.py`:
```python
from wko5.pacing import solve_pacing, RidePlan
from wko5.nutrition import evaluate_nutrition_plan, NutritionPlan, FeedEvent, time_to_bonk, cho_burn_rate
from wko5.ride_planner import plan_ride
```

- [ ] **Step 2: Create the wko5-nutrition skill**

Create `~/.claude/skills/wko5-nutrition/skill.md` with the nutrition expert skill content. This skill:
- Uses the nutrition engine for deterministic calculations
- Asks about rider's GI tolerance, past experience, food preferences
- Creates ride-specific fueling plans
- Interprets post-ride nutrition issues
- References `docs/research/nutrition-ultra.md` and `docs/research/nutrition-racing.md`

- [ ] **Step 3: Update wko5-analyzer skill**

Add new entries to the Module Reference and Question → Function mapping.

- [ ] **Step 4: Run full test suite**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 5: Commit and push**

```bash
git add wko5/__init__.py
git commit -m "feat: export pacing, nutrition, and ride planner modules"
git push origin main
```
