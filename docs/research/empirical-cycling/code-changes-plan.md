# Code Changes Plan — Empirical Cycling Podcast Synthesis

Specific changes to Python modules based on insights from 53 EC podcast episodes.
Each change cites the source episode and evidence level.

---

## 1. `durability.py` — 5 Changes

### Change 1.1: Switch from raw kJ to kJ/kg

**Function:** `degradation_factor()`, `compute_windowed_mmp()`, `fit_durability_model()`
**What:** Add `weight_kg` parameter. Normalize `cumulative_kj` to `cumulative_kj_per_kg = cumulative_kj / weight_kg`. Use kJ/kg in bins of 10 as the standard analysis unit.
**Why:** van Erp et al. 2021 (first kJ/kg paper) established kJ/kg as the standard for durability measurement. Raw kJ is misleading — 2000 kJ is huge for a 55kg woman but warmup for a 75kg pro male (WD-60) [R].
**Details:**
- `degradation_factor(cumulative_kj, elapsed_hours, params, weight_kg=None)` — if weight_kg provided, normalize internally
- `compute_windowed_mmp()` — add `cumulative_kj_per_kg` field to output dicts
- `fit_durability_model()` — fit against kJ/kg, not raw kJ; read weight from config
- Keep backward compatibility: if weight_kg is None, use raw kJ (existing behavior)

### Change 1.2: Add fresh baseline staleness check

**Function:** NEW `check_fresh_baseline(days=90)`
**What:** Query database for max efforts at key durations (60s, 300s, 1200s) in fresh state (first 2 hours of ride, cumulative kJ < 500). Flag if no fresh baseline exists within `days`.
**Why:** WD-60 identifies missing fresh baseline as a critical measurement error: "If your only 1-min max effort happened after 20 kJ/kg, that becomes your '0% loss' baseline — completely misleading" [E].
**Details:**
```python
def check_fresh_baseline(days=90, durations=[60, 300, 1200]):
    """Check if fresh baselines exist for key durations.
    Returns dict: {duration: {exists: bool, date: str, value: float, staleness_days: int}}
    Fresh = first 2 hours of ride AND cumulative kJ < 500.
    """
```

### Change 1.3: Add pre-effort intensity tracking

**Function:** `compute_windowed_mmp()` — add `pre_effort_intensity` field
**What:** For each window, compute the average IF of the riding that preceded it. Classify as "endurance_preload" (IF < 0.65), "tempo_preload" (0.65-0.80), or "race_preload" (IF > 0.80).
**Why:** WD-60: "2000 kJ at endurance pace then testing is VERY different from racing 2000 kJ then testing." Pre-effort intensity is a critical confounder [E].
**Details:** Add to each window dict:
```python
"pre_effort_avg_if": round(pre_power_np / ftp, 2),
"pre_effort_class": "endurance_preload" | "tempo_preload" | "race_preload"
```

### Change 1.4: Add durability benchmarks

**Function:** NEW `durability_benchmark(drop_pct)`
**What:** Classify a power drop percentage against EC podcast benchmarks.
**Why:** WD-60 coaching benchmarks [E].
```python
def durability_benchmark(drop_pct_at_50kjkg):
    if drop_pct_at_50kjkg < 2: return "elite_pro"
    elif drop_pct_at_50kjkg < 10: return "strong_amateur"
    elif drop_pct_at_50kjkg < 20: return "good_amateur"
    elif drop_pct_at_50kjkg < 40: return "average_amateur"
    else: return "needs_work"
```

### Change 1.5: Add TTE-fueling interaction flag

**Function:** `fit_durability_model()` — add to return dict
**What:** When durability model shows steep degradation (high `b` coefficient), add a `fueling_confound_warning` flag noting that poor durability may reflect fueling, not fitness.
**Why:** WD-60, TMT-73: "TTE extension is tied to better fueling"; nutrition is a "dangling confounder" in all field durability data [E].

---

## 2. `clinical.py` — 6 Changes

### Change 2.1: Add IF floor diagnostic

**Function:** NEW `check_if_floor(days_back=90)`
**What:** Compute IF for all rides in period. Flag if the floor of endurance rides (rides >1.5h, no intervals) is consistently above 0.70.
**Why:** TMT-69, TMT-68: IF distribution is the #1 first diagnostic coaches check. Floor at 0.70-0.75 = "easy gains available" from riding easier [E].
```python
def check_if_floor(days_back=90):
    """Check if endurance ride IF floor is too high.
    Returns flag dict if floor > 0.70 consistently.
    Severity: yellow if >0.70, red if >0.75.
    """
```

### Change 2.2: Add RED-S / LEA flags

**Function:** NEW `check_reds_flags()`
**What:** Check for RED-S warning signs from training data:
- Performance declining + training load maintained + weight stable/gaining
- Illness frequency > 1x per 6-8 weeks (from activity gaps + annotations)
- Overlap with overtraining syndrome detection
**Why:** Persp-36 (Traci Carson): RED-S and OTS have "almost just a circle" Venn diagram overlap; weight is NOT a reliable indicator of LEA [R].
```python
def check_reds_flags(days_back=180):
    """Screen for RED-S risk factors from training data.
    Returns: {risk_level, flags[], recommendation}
    """
```

### Change 2.3: Add within-day energy deficit tracking

**Function:** NEW `check_within_day_deficit(ride_end_time, ride_kj, next_meal_delay_hours=None)`
**What:** Estimate within-day energy deficit magnitude. Flag when a high-kJ ride ends with likely delayed refueling (ride ending late evening, back-to-back rides without refueling gap).
**Why:** WD-59: delayed post-exercise carbs impair next-day performance by ~30% despite identical glycogen levels (effect size 2.03) [R]. Persp-36: within-day deficits >1100 kcal trigger hormonal stress response [R].
```python
def check_within_day_deficit(activity_id):
    """Estimate within-day energy deficit risk.
    Uses ride kJ, end time, and distance to next activity.
    """
```

### Change 2.4: Add panic training detection

**Function:** NEW `check_panic_training(days_back=42)`
**What:** Detect sudden intensity spikes after extended low-load periods. Flag when:
- 2+ weeks of low CTL/low intensity
- Followed by sudden CTL ramp >7 TSS/day
- Especially in January-March (pre-season)
**Why:** TMT-71: "Panic training almost always backfires: too much intensity too soon leads to fatigue, not fitness" [E].
```python
def check_panic_training(days_back=42):
    """Detect panic training pattern: sudden intensity spike after low-load period.
    Returns flag dict or None.
    """
```

### Change 2.5: Add intensity black hole detection

**Function:** NEW `check_intensity_black_hole(days_back=30)`
**What:** Analyze IF distribution. Flag if >70% of ride time falls in IF 0.65-0.80, with <10% below 0.50 and <10% above 0.90.
**Why:** TMT-58, TMT-69: Athletes who don't polarize settle into "middle intensity black hole — 80-90% capacity, never truly hard or easy" [E].
```python
def check_intensity_black_hole(days_back=30):
    """Detect intensity black hole — most rides in moderate zone.
    Returns flag dict or None.
    """
```

### Change 2.6: Integrate new checks into `get_clinical_flags()`

**Function:** `get_clinical_flags()`
**What:** Add calls to all new check functions: `check_if_floor()`, `check_reds_flags()`, `check_panic_training()`, `check_intensity_black_hole()`.
**Why:** All new diagnostics should be part of the standard clinical flag scan.

---

## 3. `zones.py` — 3 Changes

### Change 3.1: Add sweet spot TTE tracking

**Function:** NEW `sweet_spot_band(ftp)` and `sweet_spot_tte(activity_id, ftp)`
**What:** Define sweet spot as 88-93% of FTP. Track time spent in this band per ride. Estimate TTE at sweet spot from longest sustained effort.
**Why:** TMT-44: Sweet spot TTE is a key fitness marker independent of FTP. Ranges: untrained 40-60 min, trained 90-120 min, elite 180+ min [E].
```python
def sweet_spot_band(ftp):
    """Return (low, high) power for sweet spot band (~88-93% FTP)."""
    return (int(ftp * 0.88), int(ftp * 0.93))

def sweet_spot_tte(activity_id, ftp):
    """Estimate TTE at sweet spot from longest sustained effort in band."""
```

### Change 3.2: Add endurance IF validation

**Function:** NEW `validate_endurance_rides(days_back=30, ftp=None)`
**What:** Check all rides classified as "endurance" (by duration >1.5h and no high-intensity intervals). Flag if IF > 0.65.
**Why:** TMT-69: Endurance ride IF target is 0.50-0.65; above this, the athlete is riding too hard for endurance adaptation. Floor at 0.70-0.75 is a red flag [E].
```python
def validate_endurance_rides(days_back=30, ftp=None):
    """Check if endurance rides are actually easy enough.
    Returns: list of rides with IF > 0.65, with IF values.
    """
```

### Change 3.3: Add RPE targets per zone

**Function:** Modify `coggan_zones()` return value to include RPE targets
**What:** Add RPE field to zone dict output.
**Why:** TMT-49, TMT-51: Power + HR + RPE triangulation is the gold standard for workout quality. RPE targets by zone guide auto-regulation [E].
```python
# Updated zone dict entries include RPE targets:
"Active Recovery": {"power": (0, int(ftp * 0.55)), "rpe": "1-2/10"},
"Endurance": {"power": (int(ftp * 0.56), int(ftp * 0.75)), "rpe": "2-3/10"},
"Tempo": {"power": (int(ftp * 0.76), int(ftp * 0.90)), "rpe": "4-5/10"},
"Sweet Spot": {"power": (int(ftp * 0.88), int(ftp * 0.93)), "rpe": "6-7/10"},
"Threshold": {"power": (int(ftp * 0.91), int(ftp * 1.05)), "rpe": "7-8/10"},
"VO2max": {"power": (int(ftp * 1.06), int(ftp * 1.20)), "rpe": "9-9.5/10"},
"Anaerobic": {"power": (int(ftp * 1.21), int(ftp * 1.50)), "rpe": "10/10"},
"Neuromuscular": {"power": (int(ftp * 1.51), 9999), "rpe": "max"},
```
Note: This changes the return format. Existing callers that destructure `(low, high)` need updating, or provide a backward-compatible wrapper.

---

## 4. `training_load.py` — 5 Changes

### Change 4.1: Add indoor training multiplier

**Function:** `_get_activity_tss()` or `_get_cached_tss()`
**What:** Detect indoor rides (via `sub_sport` field: "indoor_cycling", "virtual_ride") and apply a 1.1-1.2x multiplier to TSS.
**Why:** TMT-51: "Indoor training requires longer recovery than equivalent outdoor (thermoregulation strain)" [E]. Indoor rides generate equivalent power meter TSS but higher physiological cost due to heat stress.
```python
# In _get_activity_tss:
if activity_row.get("sub_sport") in ("indoor_cycling", "virtual_ride"):
    tss *= 1.15  # indoor multiplier (midpoint of 1.1-1.2 range)
```

### Change 4.2: Add IF distribution analysis

**Function:** NEW `if_distribution(days_back=90)`
**What:** Compute IF for all rides in period. Return histogram, floor, ceiling, and compression diagnostic.
**Why:** TMT-68, TMT-69: IF distribution is the #1 diagnostic metric coaches check. Compressed IF spread (floor >0.70, ceiling <0.85) = "easy gains available" [E].
```python
def if_distribution(days_back=90, ftp=None):
    """Analyze IF distribution across recent rides.
    Returns: {
        histogram: {bin: count},
        floor: float,  # 10th percentile IF
        ceiling: float,  # 90th percentile IF
        spread: float,  # ceiling - floor
        compressed: bool,  # True if floor > 0.70
        rides_analyzed: int,
    }
    """
```

### Change 4.3: Add rolling FTP from training data

**Function:** Already exists as `rolling_ftp()` — ADD interpretation layer
**What:** Add `ftp_growth_curve()` function that fits a logarithmic model to rolling FTP data and estimates: training age position on growth curve, expected improvement rate, whether athlete is at plateau.
**Why:** WD-61: Diminishing returns follow a logarithmic growth curve. Log-transformed time yields linear fit [R].
```python
def ftp_growth_curve(window_days=90, step_days=30):
    """Fit logarithmic growth model to FTP history.
    Returns: {
        slope: float,  # log-linear slope (W/log-week)
        r_squared: float,
        improvement_rate_w_per_year: float,  # current estimated rate
        plateau_detected: bool,  # True if slope < 1W/year
        training_age_weeks: int,
        growth_phase: str,  # "early", "intermediate", "mature", "plateau"
    }
    """
```

### Change 4.4: Add allostatic load model stub

**Function:** NEW `allostatic_load_estimate(days_back=7)`
**What:** Combine TSS with available life-stress proxies to estimate total allostatic load. Proxies: missed sessions (from gaps in training), workout comment sentiment (if TrainingPeaks data), session RPE trend, illness gaps.
**Why:** TMT-48: "Body has ONE pool for ALL stress — allostasis" (McEwen) [R]. TMT-57: high work stress doubles recovery cost [E].
```python
def allostatic_load_estimate(days_back=7):
    """Estimate total stress load (training + life).
    Returns: {
        training_load: float,  # ATL
        life_stress_indicators: {
            missed_sessions: int,
            comment_sentiment: str,  # if available
            rpe_trend: str,  # "stable", "rising", "falling"
        },
        combined_load: str,  # "low", "moderate", "high", "critical"
        recommendation: str,
    }
    """
```

### Change 4.5: Add day-to-day performance variability tracking

**Function:** NEW `performance_trend(durations=[300, 1200], days_back=30)`
**What:** Track best effort at key durations on a per-ride basis. Compute 7-day rolling trend. Flag if trending down consistently.
**Why:** TMT-73: "If daily performance is trending down, investigate immediately (nutrition, sleep, stress, overreaching)" [E].
```python
def performance_trend(durations=[300, 1200], days_back=30):
    """Track day-to-day performance at key durations.
    Returns: DataFrame with date, duration, best_power, 7day_trend
    """
```

---

## 5. `gap_analysis.py` — 3 Changes

### Change 5.1: Show durability alongside absolute power

**Function:** `gap_analysis()` return dict
**What:** Add `absolute_power_check` field that compares the athlete's fresh 5-min, 20-min power to the minimum required by the route, independent of durability.
**Why:** WD-60: "You need sufficient power to begin with." Better cyclists start with more power AND lose less. Over-indexing on durability misses the fundamental limiter [E].
```python
# In gap_analysis return dict, add:
"absolute_power_check": {
    "fresh_5min_w": ...,
    "fresh_20min_w": ...,
    "required_5min_w": ...,  # hardest 5-min segment demand
    "required_20min_w": ...,
    "absolute_sufficient": bool,
    "message": "Durability is secondary — absolute power is {sufficient/insufficient} for this route."
}
```

### Change 5.2: Add opportunity cost framework

**Function:** NEW `opportunity_cost_analysis(power_profile, race_demands)`
**What:** Given the athlete's power profile at all durations and race demands, rank which duration improvements would yield the largest benefit. Show what each 10W gain at each duration would mean for the specific event.
**Why:** TMT-70: "Opportunity cost must be weighed for every training decision. 20 more watts of 1-min power vs 10 more watts of FTP — which matters more for YOUR racing?" [E]
```python
def opportunity_cost_analysis(power_profile, race_demands):
    """Rank training priorities by opportunity cost for a specific event.
    Returns: ranked list of {duration, current_gap, improvement_value, training_cost}
    """
```

### Change 5.3: Add consistency check for short-duration power

**Function:** Modify `gap_analysis()` or add helper
**What:** For 1-min power, compare peak vs typical across the year. If ratio > 1.3, flag as consistency problem (not capacity problem).
**Why:** TMT-64: "Two peak performances at 600W but normally 450W = consistency problem, not capacity problem" [E].
```python
def short_power_consistency(duration_s=60, days_back=365):
    """Check consistency of short-duration power across the year.
    Returns: {peak, typical (median), ratio, diagnosis: "capacity" | "consistency"}
    """
```

---

## 6. `nutrition.py` — 4 Changes

### Change 6.1: Update default carb targets

**Function:** `NutritionPlan` default + documentation
**What:** Change `baseline_intake_g_hr` default from 60 to 75 (midpoint of 60-90 range). Add docstring noting 60-90g/hr is the evidence-based range (TMT-73, Persp-41).
**Why:** TMT-73: "Fueling on the bike is the #1 thing coaches wish they knew earlier; old paradigm of 25g/hr was grossly insufficient" [E]. Persp-41: 60-120+ g/hr depending on context [R].
```python
@dataclass
class NutritionPlan:
    baseline_intake_g_hr: float = 75  # Updated: 60-90g/hr standard (EC podcast)
```

### Change 6.2: Add absorption ceiling check

**Function:** NEW `check_absorption_ceiling(intake_g_hr, athlete_ceiling_g_hr=90)`
**What:** Flag when prescribed intake exceeds likely absorption ceiling. Default ceiling 90g/hr unless athlete has tested higher.
**Why:** Persp-41: Carb absorption ranges from 50-150g/hr; individual variation is massive [R]. Platform fueling recommendations should cap at ~90g/hr unless lab-tested higher.
```python
def check_absorption_ceiling(intake_g_hr, athlete_ceiling_g_hr=90):
    """Check if intake exceeds likely absorption ceiling.
    Returns warning dict if intake > ceiling.
    """
```

### Change 6.3: Add glycogen periodization model

**Function:** NEW `glycogen_budget_daily(rides, meals, weight_kg)`
**What:** Model daily glycogen budget accounting for on-bike depletion, post-ride repletion rate (1.2g/kg/hr), and next-day starting glycogen. Flag when post-ride fueling delay squeezes recovery carb budget.
**Why:** WD-59: delayed post-exercise carbs impair next-day performance by ~30% [R]. Persp-41: 120g/hr on-bike can leave insufficient carbs for recovery [R].
```python
def glycogen_budget_daily(ride_kj, ride_duration_h, on_bike_carbs_g,
                          post_ride_delay_h, daily_carb_target_g_kg, weight_kg):
    """Model daily glycogen budget with recovery timing.
    Returns: {
        on_bike_carbs_used_g, recovery_carbs_needed_g,
        recovery_window_available_h, recovery_rate_achievable_g_kg_hr,
        next_day_glycogen_estimate_pct,
        warning: str or None  # if recovery budget is squeezed
    }
    """
```

### Change 6.4: Add energy estimation confidence interval

**Function:** `energy_expenditure()` — add `with_uncertainty=False` parameter
**What:** When `with_uncertainty=True`, return a tuple `(estimate, low, high)` where low/high reflect the ~900 kcal swing from efficiency assumptions (20-25% GE range) plus nutrition label error (~20%).
**Why:** Persp-41: "A 5% change in efficiency yields ~900 kcal difference on a 4000 kJ day. Nutrition labels have 20% error. Absorption is 85-95%." [R]
```python
def energy_expenditure(power_watts, efficiency=0.23, with_uncertainty=False):
    if not with_uncertainty:
        return _base_ee(power_watts, efficiency)
    low = _base_ee(power_watts, 0.25)   # higher efficiency = lower EE
    high = _base_ee(power_watts, 0.20)   # lower efficiency = higher EE
    mid = _base_ee(power_watts, efficiency)
    return (mid, low, high)
```

---

## 7. `pdcurve.py` — 3 Changes

### Change 7.1: Decompose PD curve changes into CP vs W'

**Function:** NEW `decompose_pd_change(model_old, model_new)`
**What:** Compare two PD models and attribute changes to CP (mFTP) vs W' (FRC) vs neuromuscular (Pmax). Report which component drove the change at each duration.
**Why:** WD-55: Ramp test improvements may reflect W', not VO2max. 30/15 study gains were most parsimoniously explained by anaerobic capacity improvement, not VO2max [R].
```python
def decompose_pd_change(model_old, model_new):
    """Decompose PD curve change into component contributions.
    Returns: {
        mFTP_change_w: float,
        FRC_change_kj: float,
        Pmax_change_w: float,
        TTE_change_min: float,
        dominant_change: str,  # "aerobic", "anaerobic", "neuromuscular", "endurance"
        at_durations: {60: {old, new, delta, driver}, 300: {...}, ...}
    }
    """
```

### Change 7.2: Add rolling PD curves from training data

**Function:** `rolling_ftp()` already exists — ADD `rolling_pd_profile()`
**What:** Compute full PD model parameters (not just mFTP) at regular intervals. Track Pmax, FRC, mFTP, TTE over time. This replaces isolated test days with continuous monitoring.
**Why:** WD-62, TMT-66: "Rolling PD curves from training data are more reliable than isolated test days. Over-testing is counterproductive" [R+E].
```python
def rolling_pd_profile(window_days=90, step_days=14):
    """Compute rolling PD model parameters over training history.
    Returns: DataFrame with date, mFTP, Pmax, FRC, TTE, mVO2max
    Uses compute_envelope_mmp + fit_pd_model at each step.
    """
```
Note: This is essentially what `rolling_ftp()` does but returns all parameters. Consider refactoring `rolling_ftp()` to call this.

### Change 7.3: Add sub-CP model correction

**Function:** `fit_pd_model()` — add note/correction factor
**What:** Add optional `sub_cp_correction=True` parameter. When enabled, apply empirical correction for the known underestimation of fatigue at sub-CP durations.
**Why:** 1M AMA: "Critical power models can underestimate below-CP power durations because the model doesn't fully account for durability loss" [R]. This is acknowledged as a known CP model limitation.
```python
# In fit_pd_model return dict, add:
"sub_cp_note": "CP model may overestimate sustainable power at durations >TTE. Use durability model for efforts beyond TTE."
```

---

## Implementation Priority

| Priority | Module | Change | Effort | Impact |
|----------|--------|--------|--------|--------|
| **P0** | clinical.py | IF floor diagnostic (2.1) | Small | High — #1 coaching diagnostic |
| **P0** | clinical.py | Intensity black hole (2.5) | Small | High — common amateur error |
| **P0** | training_load.py | IF distribution analysis (4.2) | Medium | High — feeds clinical + analyzer |
| **P1** | durability.py | kJ/kg normalization (1.1) | Medium | High — correctness fix |
| **P1** | durability.py | Fresh baseline check (1.2) | Small | High — prevents bad interpretations |
| **P1** | clinical.py | Panic training detection (2.4) | Medium | Medium — seasonal relevance |
| **P1** | pdcurve.py | Decompose CP vs W' (7.1) | Medium | High — prevents misinterpretation |
| **P1** | nutrition.py | Update carb defaults (6.1) | Trivial | Medium — aligns with evidence |
| **P2** | training_load.py | Indoor multiplier (4.1) | Small | Medium — applies to ~50% of rides |
| **P2** | training_load.py | FTP growth curve (4.3) | Medium | Medium — long-term insight |
| **P2** | gap_analysis.py | Absolute power check (5.1) | Small | Medium — prevents Goodhart's Law |
| **P2** | gap_analysis.py | Opportunity cost (5.2) | Large | High — key coaching tool |
| **P2** | zones.py | Sweet spot TTE (3.1) | Medium | Medium — new fitness marker |
| **P2** | zones.py | Endurance IF validation (3.2) | Small | Medium — feeds clinical |
| **P3** | clinical.py | RED-S flags (2.2) | Large | Medium — important but complex |
| **P3** | clinical.py | Within-day deficit (2.3) | Medium | Medium — data often unavailable |
| **P3** | nutrition.py | Glycogen periodization (6.3) | Large | Medium — advanced feature |
| **P3** | nutrition.py | Absorption ceiling (6.2) | Small | Low — simple warning |
| **P3** | nutrition.py | Energy confidence interval (6.4) | Small | Low — display improvement |
| **P3** | training_load.py | Allostatic load (4.4) | Large | Medium — proxy data limited |
| **P3** | training_load.py | Performance trend (4.5) | Medium | Medium — useful but manual check works |
| **P3** | pdcurve.py | Rolling PD profile (7.2) | Small | Medium — mostly refactoring |
| **P3** | pdcurve.py | Sub-CP correction (7.3) | Small | Low — documentation note |
| **P3** | zones.py | RPE targets (3.3) | Small | Low — breaking change to return format |
| **P3** | gap_analysis.py | Short power consistency (5.3) | Medium | Low — niche diagnostic |
| **P3** | durability.py | Benchmarks (1.4) | Trivial | Low — simple lookup |
| **P3** | durability.py | Fueling confound flag (1.5) | Trivial | Low — annotation |
| **P3** | durability.py | Pre-effort intensity (1.3) | Medium | Medium — improves model quality |
