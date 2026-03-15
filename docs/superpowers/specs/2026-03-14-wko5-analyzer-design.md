# WKO5 Analyzer — Design Spec

## Overview

A Python library for WKO5-style cycling power analysis built on top of a local SQLite database of Garmin FIT file data. The system has three interfaces: an importable Python package, Jupyter notebooks for visualization, and a Claude skill for in-conversation analysis.

## Athlete Context

- Weight: 78 kg (172 lbs)
- FTP range: 285-299W (~3.7-3.8 W/kg)
- Data: 1,653 cycling activities (2018-2026), 11M+ per-second records
- DB: `wko5/cycling_power.db`
- Ride types: Zwift (782), road (580), indoor (219), other
- Note: Zwift power may differ from outdoor due to trainer calibration. Analysis functions accept an optional `sub_sport` filter to separate ride types when needed.

## Architecture

Multi-module Python package with each domain in its own file.

```
wko5/
  __init__.py           # Package init, convenience imports
  db.py                 # DB connection, common queries, athlete constants
  clean.py              # Data cleaning: spike removal, dropout handling, gap filling
  pdcurve.py            # MMP curve, PD model fitting, FTP/FRC/Pmax/TTE estimation
  training_load.py      # NP, TSS, IF, CTL/ATL/TSB (PMC)
  zones.py              # Coggan zones, iLevels, Seiler 3-zone, time-in-zone
  ride.py               # Single-ride analysis, interval detection, lap analysis
  profile.py            # Power profile, strengths/limiters, phenotype, trends
notebooks/
  power_duration.ipynb   # MMP curve, PD model, rolling FTP, period comparisons
  training_load.ipynb    # PMC chart, weekly TSS, volume trends
  ride_analysis.ipynb    # Template for single-ride breakdown with plots
```

Dependencies: `numpy`, `pandas`, `scipy`, `matplotlib`, `fitdecode`

## Data Cleaning (`clean.py`)

All analysis modules pass power data through cleaning before computation.

**Power spike removal:**
- Remove single-second readings >2000W (sensor glitches)
- Replace with interpolated value from neighbors

**Dropout handling:**
- Power = 0 is treated as coasting (legitimate zero) by default
- Power = None/NaN is treated as sensor dropout — forward-fill up to 5s gaps, mark longer gaps as NaN

**Timestamp gap handling:**
- Detect gaps >2s between consecutive records
- Fill gaps <=5s with interpolated values
- Gaps >5s are left as NaN (ride was paused/stopped)

**Functions:**
- `clean_power(power_series: pd.Series) -> pd.Series` — apply spike removal and dropout handling
- `clean_records(records_df: pd.DataFrame) -> pd.DataFrame` — full cleaning pipeline on a records DataFrame

## Module Specifications

### `db.py` — Core Data Layer

Foundation module that all others import. Handles DB access and provides data as DataFrames.

**Constants:**
- `DB_PATH` — path to `cycling_power.db`
- `WEIGHT_KG = 78.0`
- `FTP_RANGE = (285, 299)`
- `FTP_DEFAULT = 292` — midpoint, used as fallback

**Functions:**
- `get_connection() -> sqlite3.Connection`
- `get_activities(start=None, end=None, sub_sport=None) -> pd.DataFrame` — filtered activity list
- `get_records(activity_id) -> pd.DataFrame` — per-second data for one ride (cleaned via `clean.clean_records`)

**Error handling convention (applies to all modules):**
- Functions that return DataFrames return empty DataFrames when no data matches
- Functions that return dicts return empty dicts when no data matches
- Functions that return floats return `float('nan')` when computation is not possible
- `fit_pd_model` returns `None` when curve fitting fails to converge
- No module raises exceptions for missing/empty data — callers check results before proceeding
- All modules log warnings via `logging` for unexpected conditions (e.g., all-NaN power series, zero rides in range)

### `pdcurve.py` — Power Duration Model

Builds the MMP curve and fits a multi-component model to derive physiological parameters.

**MMP computation algorithm:**
- Uses cumulative sum approach for O(n) per duration: `cumsum[i+d] - cumsum[i]` divided by `d`, then take max
- Per-ride MMP arrays are cached in a DB table `mmp_cache` (columns: `activity_id`, `duration_s`, `max_avg_power`) to avoid recomputation
- Cache is populated lazily: computed on first access, stored permanently
- Envelope MMP across rides: for each duration, take max across all per-ride MMP values in the date range

**MMP array length handling:**
- Each ride's MMP extends only to its actual duration
- When computing envelope, shorter rides simply don't contribute at longer durations
- Envelope length = max ride duration in the date range

**PD model:**
- 3-component model: `P(t) = Pmax * e^(-t/τ) + FRC*1000/(t + t0) + mFTP`
- The `t0` offset (~5s) prevents the FRC term from going to infinity at short durations
- Fit via `scipy.optimize.curve_fit` on durations from 5s to max ride length
- Bounds: Pmax ~800-2500W, FRC ~5-30 kJ, mFTP ~150-400W, τ ~5-30s, t0 ~1-15s
- If curve_fit fails to converge, return None (caller must handle)

**Derived parameters:**
- `Pmax` — peak instantaneous power (neuromuscular)
- `FRC` — Functional Reserve Capacity in kJ (anaerobic energy above FTP)
- `mFTP` — modeled FTP from the curve
- `TTE` — time to exhaustion at mFTP: the duration where the modeled curve first drops below mFTP (the "kink" point)
- `mVO2max` — estimated VO2max in mL/min: `(mFTP * 12.35) + (WEIGHT_KG * 3.5)` using the ACSM cycling equation. Convert to mL/min/kg: `mVO2max / WEIGHT_KG`. Convert to L/min: `mVO2max / 1000`

**Functions:**
- `compute_mmp(power_series: pd.Series) -> np.ndarray` — MMP for one ride using cumsum
- `get_cached_mmp(activity_id) -> np.ndarray` — retrieve from cache or compute+store
- `compute_envelope_mmp(start=None, end=None, days=90, sub_sport=None) -> np.ndarray` — aggregate MMP from cached per-ride arrays
- `fit_pd_model(mmp: np.ndarray) -> dict | None` — returns {Pmax, FRC, mFTP, TTE, mVO2max, tau, t0} or None on failure
- `rolling_ftp(window_days=90, step_days=7) -> pd.DataFrame` — time series of modeled FTP (uses cached MMP, so each step is fast)
- `compare_periods(period1: tuple, period2: tuple) -> dict` — overlay two PD curves
- `power_at_durations(mmp: np.ndarray, durations=[5,60,300,1200,3600]) -> dict` — power at key timepoints
- `rebuild_mmp_cache() -> int` — recompute and store MMP for all activities, returns count processed

### `training_load.py` — Performance Management

TSS computation and PMC (CTL/ATL/TSB) tracking.

**Normalized Power:**
- 30s rolling average of power → raise each value to 4th power → mean of 4th powers → 4th root
- Zeros included (coasting is physiologically relevant to NP)
- NaN values excluded from rolling window

**TSS calculation:**
- Formula: `(duration_s * NP^2) / (FTP^2 * 3600) * 100`
- Equivalent to: `(duration_s * NP * IF) / (FTP * 3600) * 100` where `IF = NP / FTP`

**TSS source priority:**
1. Use device-reported TSS if available and > 0
2. Compute from records using the formula above
3. FTP source priority: device `threshold_power` > modeled mFTP > `FTP_DEFAULT` (292W)

**PMC:**
- Daily TSS aggregation (sum if multiple rides per day, 0 for rest days)
- CTL: EWMA with 42-day time constant
- ATL: EWMA with 7-day time constant
- TSB: CTL - ATL

**HR-based metrics:**
- `efficiency_factor(activity_id) -> float` — NP / avg HR (aerobic efficiency)
- `ef_trend(days=365) -> pd.DataFrame` — EF over time (should trend up as fitness improves)

**Functions:**
- `compute_np(power_series: pd.Series) -> float`
- `compute_tss(np_watts: float, duration_s: float, ftp: float) -> float`
- `build_pmc(start=None, end=None, ftp=None) -> pd.DataFrame` — daily CTL/ATL/TSB
- `current_fitness() -> dict` — latest CTL, ATL, TSB snapshot
- `fitness_trend(days=365) -> pd.DataFrame` — CTL trajectory
- `efficiency_factor(activity_id) -> float`
- `ef_trend(days=365) -> pd.DataFrame`

### `zones.py` — Training Zones

Multiple zone systems for power distribution analysis.

**Coggan classic (7 zones, % of FTP):**
- Active Recovery: <55%, Endurance: 56-75%, Tempo: 76-90%, Threshold: 91-105%, VO2max: 106-120%, Anaerobic: 121-150%, Neuromuscular: >150%

**iLevels (individualized, 7 zones):**
- Uses the fitted PD model to find zone boundaries at physiologically meaningful transition points
- Zone 1 (Recovery): 0 to 55% mFTP
- Zone 2 (Endurance): 55% mFTP to aerobic threshold (~76% mFTP, adjusted by TTE)
- Zone 3 (Tempo): aerobic threshold to 90% mFTP
- Zone 4 (Threshold): 90% mFTP to mFTP
- Zone 5 (VO2max): mFTP to mFTP + 15% of FRC-derived power (duration from PD curve at ~3-8min)
- Zone 6 (Anaerobic): VO2max ceiling to mFTP + 50% of FRC-derived power (~30s-3min range)
- Zone 7 (Neuromuscular): above Zone 6 ceiling
- Key difference from Coggan: boundaries shift based on individual FRC and TTE, not fixed percentages

**Seiler 3-zone:**
- Zone 1: <80% FTP (below aerobic threshold)
- Zone 2: 80-100% FTP (between thresholds)
- Zone 3: >100% FTP (above lactate threshold)

**HR zones (Coggan 5-zone):**
- Zone 1: <68% max HR, Zone 2: 69-83%, Zone 3: 84-94%, Zone 4: 95-105% LTHR, Zone 5: >105% LTHR
- Requires max HR and LTHR (estimated from data if not set)

**Functions:**
- `coggan_zones(ftp: float) -> dict` — zone name → (low, high) watts
- `ilevels(pd_model: dict) -> dict` — individualized zones from PD model (7 zones with names and watt ranges)
- `seiler_zones(ftp: float) -> dict` — 3-zone boundaries
- `hr_zones(max_hr: int, lthr: int) -> dict` — HR zone boundaries
- `time_in_zones(power_series: pd.Series, zones: dict) -> dict` — seconds per zone
- `ride_distribution(activity_id, zone_system="coggan") -> dict` — zone breakdown for a ride
- `period_distribution(start, end, zone_system="coggan") -> dict` — aggregate across rides

### `ride.py` — Single Ride Analysis

Deep dives into individual rides.

**Ride summary:** Duration, distance, avg/NP/max power, avg/max HR, cadence, elevation, kJ, IF, TSS. Computed from records when device values are missing.

**Interval detection:**
- Find sustained efforts where power > threshold (default: 90% FTP) for > min_duration (default: 30s)
- Use 10s smoothing on power to avoid false splits from momentary dips
- Group into work/rest pairs
- Report: avg power, duration, avg HR, avg cadence per interval
- Pattern detection: identify repeated interval sets (e.g., "5x5min")

**Lap analysis:** Per-lap stats from the laps table, pacing analysis (fade detection).

**Other analysis:**
- Power histogram (configurable bin width)
- HR decoupling: compare HR:power ratio first half vs second half (>5% suggests aerobic drift)
- Best efforts within the ride at key durations

**Functions:**
- `ride_summary(activity_id) -> dict`
- `detect_intervals(activity_id, min_power_pct=0.9, min_duration=30) -> list[dict]`
- `lap_analysis(activity_id) -> pd.DataFrame`
- `hr_decoupling(activity_id) -> float` — decoupling percentage
- `best_efforts(activity_id, durations=[60,300,1200]) -> dict`
- `power_histogram(activity_id, bin_width=10) -> pd.DataFrame`

### `profile.py` — Power Profile & Phenotype

Benchmarking, strengths/limiters, and trend analysis.

**Power profile:**
- Extract power at key durations: 5s, 1min, 5min, 20min, 60min
- Report in both watts and W/kg

**Coggan power profile table (W/kg, male):**

| Category | 5s | 1min | 5min | 20min | 60min |
|---|---|---|---|---|---|
| World Class | >24.04 | >11.50 | >7.60 | >6.40 | >6.10 |
| Exceptional | 22.22-24.04 | 10.44-11.50 | 6.95-7.60 | 5.69-6.40 | 5.36-6.10 |
| Very Good | 19.31-22.21 | 8.87-10.43 | 5.97-6.94 | 4.92-5.68 | 4.62-5.35 |
| Good | 16.85-19.30 | 7.42-8.86 | 5.05-5.96 | 4.23-4.91 | 3.90-4.61 |
| Moderate | 14.18-16.84 | 5.97-7.41 | 4.19-5.04 | 3.52-4.22 | 3.23-3.89 |
| Fair | 11.51-14.17 | 4.63-5.96 | 3.34-4.18 | 2.78-3.51 | 2.53-3.22 |
| Untrained | <11.51 | <4.63 | <3.34 | <2.78 | <2.53 |

**Strengths & limiters:**
- Compare athlete's relative ranking across durations
- Highest-ranked duration = strength, lowest = limiter
- Uses position within category (percentile within range) for finer granularity

**Phenotype classification thresholds:**
- Sprinter: Pmax/mFTP > 6.0 and FRC/mFTP > 0.08 kJ/W
- Pursuiter: Pmax/mFTP 4.5-6.0 and FRC/mFTP > 0.06 kJ/W
- TTer: Pmax/mFTP < 4.5 and TTE > 50min
- All-rounder: does not strongly fit any of the above

**Fatigue resistance:**
- Compare power at key durations when fresh (first 30min of a ride) vs. fatigued (after 60min+ of riding)
- Stamina ratio: power at duration X after Y kJ of work / power at duration X when fresh
- Tracked over time to see if durability is improving

**Trend tracking:**
- Rolling power at any duration over time
- W/kg progression
- Period comparisons

**Functions:**
- `power_profile(days=90, sub_sport=None) -> dict` — watts and W/kg at key durations
- `coggan_ranking(profile: dict) -> dict` — category per duration
- `strengths_limiters(profile: dict) -> dict` — identifies relative strengths and limiters
- `phenotype(pd_model: dict) -> str` — classification with rationale
- `profile_trend(duration_s, window_days=90, step_days=7) -> pd.DataFrame` — rolling power over time
- `compare_profiles(period1: tuple, period2: tuple) -> dict`
- `fatigue_resistance(days=90, fresh_minutes=30, fatigue_kj=1500) -> dict` — stamina ratios at key durations

## `__init__.py`

```python
from wko5.db import get_connection, get_activities, get_records, WEIGHT_KG, FTP_DEFAULT
from wko5.pdcurve import compute_envelope_mmp, fit_pd_model, rolling_ftp
from wko5.training_load import build_pmc, current_fitness, compute_np
from wko5.zones import coggan_zones, ilevels, time_in_zones
from wko5.ride import ride_summary, detect_intervals
from wko5.profile import power_profile, strengths_limiters, phenotype
```

## MMP Cache Schema

Added to `cycling_power.db`:

```sql
CREATE TABLE IF NOT EXISTS mmp_cache (
    activity_id INTEGER,
    duration_s INTEGER,
    max_avg_power REAL,
    PRIMARY KEY (activity_id, duration_s),
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);
```

Populated lazily by `pdcurve.get_cached_mmp()`. Can be rebuilt with `pdcurve.rebuild_mmp_cache()`.

## Notebooks

### `power_duration.ipynb`
- MMP curve plot (log-scale x-axis for duration)
- PD model overlay on MMP
- Key parameters table (Pmax, FRC, mFTP, TTE, mVO2max)
- Rolling FTP chart over full history
- Period comparison overlay (e.g., this year vs last year)

### `training_load.ipynb`
- Full PMC chart (CTL, ATL, TSB on same axes)
- Weekly TSS bar chart
- Monthly volume trends (hours, kJ, distance)
- Current fitness snapshot
- EF trend chart

### `ride_analysis.ipynb`
- Set `ACTIVITY_ID` at top, run all cells for full breakdown
- Power/HR/cadence time series plot
- Detected intervals table
- Lap comparison chart
- Zone distribution pie/bar chart
- Best efforts table

## Claude Skill: `/wko5-analyzer`

The skill provides instructions for analyzing the athlete's data in conversation.

**Trigger:** When the user asks about their training, fitness, power, FTP, zones, ride analysis, or anything that can be answered from their cycling data.

**Behavior:**
- Import from the `wko5` package and run analysis against the DB
- Recreate `/tmp/fitenv/` venv if needed (numpy, pandas, scipy, matplotlib, fitdecode)
- Return results as formatted text/tables (not charts — those are for notebooks)
- Know which function to call for each type of question

**Example mappings:**
- "How's my fitness?" → `training_load.current_fitness()`
- "What's my FTP?" → `pdcurve.fit_pd_model()` → report mFTP
- "Analyze yesterday's ride" → find activity by date → `ride.ride_summary()` + `ride.detect_intervals()`
- "Am I improving?" → `pdcurve.rolling_ftp()` + `profile.profile_trend()`
- "What should I work on?" → `profile.strengths_limiters()`
- "Show my zones" → `zones.coggan_zones()` or `zones.ilevels()`
- "Compare this month to last month" → `profile.compare_profiles()`
- "How efficient am I?" → `training_load.ef_trend()`

## Testing Strategy

- Validate mFTP output falls within known 285-299W range
- Validate NP >= avg power for all rides
- Validate TSS ≈ 100 for a 1-hour ride at FTP
- Validate CTL/ATL/TSB arithmetic (TSB = CTL - ATL)
- Validate zone boundaries sum to cover full power range
- Spot-check MMP values against Garmin/WKO5 reported values
- Validate PD model converges on real data
- Validate MMP cache matches fresh computation

## Dependencies

```
numpy
pandas
scipy
matplotlib
fitdecode
```

All installed in `/tmp/fitenv/` venv (needs recreating after system restart).
