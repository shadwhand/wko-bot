# WKO5 Analyzer — Design Spec

## Overview

A Python library for WKO5-style cycling power analysis built on top of a local SQLite database of Garmin FIT file data. The system has three interfaces: an importable Python package, Jupyter notebooks for visualization, and a Claude skill for in-conversation analysis.

## Athlete Context

- Weight: 78 kg (172 lbs)
- FTP range: 285-299W (~3.7-3.8 W/kg)
- Data: 1,653 cycling activities (2018-2026), 11M+ per-second records
- DB: `wko5/cycling_power.db`
- Ride types: Zwift (782), road (580), indoor (219), other

## Architecture

Multi-module Python package with each domain in its own file.

```
wko5/
  __init__.py           # Package init, version
  db.py                 # DB connection, common queries, athlete constants
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
- `get_records(activity_id) -> pd.DataFrame` — per-second data for one ride
- `get_mmp_data(activity_id) -> np.ndarray` — mean-max power array for one ride
- `get_all_mmp(start=None, end=None, days=None) -> np.ndarray` — envelope MMP across rides in date range

### `pdcurve.py` — Power Duration Model

Builds the MMP curve and fits a multi-component model to derive physiological parameters.

**MMP computation:**
- For each duration d (1s to max ride length), find highest average power across all rides in range
- Uses a rolling-window approach on per-second power data

**PD model:**
- 3-component model: `P(t) = Pmax * e^(-t/τ) + FRC*1000/t + mFTP`
- Fit via `scipy.optimize.curve_fit` with physiologically reasonable bounds
- Pmax bounded ~800-2500W, FRC ~5-30 kJ, mFTP ~150-400W, τ ~5-30s

**Derived parameters:**
- `Pmax` — peak instantaneous power (neuromuscular)
- `FRC` — Functional Reserve Capacity in kJ (anaerobic energy above FTP)
- `mFTP` — modeled FTP from the curve
- `TTE` — time to exhaustion at mFTP (found as the "kink" point where sustained power drops below mFTP)
- `mVO2max` — estimated VO2max: `mFTP / (WEIGHT_KG * 0.00105 * 0.23)` adjusted for ~23% gross efficiency

**Functions:**
- `compute_mmp(power_series: pd.Series) -> np.ndarray` — MMP for one ride
- `compute_envelope_mmp(start=None, end=None, days=90) -> np.ndarray` — aggregate MMP
- `fit_pd_model(mmp: np.ndarray) -> dict` — returns {Pmax, FRC, mFTP, TTE, mVO2max, tau}
- `rolling_ftp(window_days=90, step_days=7) -> pd.DataFrame` — time series of modeled FTP
- `compare_periods(period1: tuple, period2: tuple) -> dict` — overlay two PD curves
- `power_at_durations(mmp: np.ndarray, durations=[5,60,300,1200,3600]) -> dict` — power at key timepoints

### `training_load.py` — Performance Management

TSS computation and PMC (CTL/ATL/TSB) tracking.

**Normalized Power:**
- 30s rolling average of power → 4th power → mean → 4th root
- Handles gaps/zeros in power data

**TSS calculation priority:**
1. Use device-reported TSS if available and > 0
2. Compute from records: `(duration_s * NP * IF) / (FTP * 3600) * 100`
3. FTP source priority: device `threshold_power` > modeled mFTP > `FTP_DEFAULT` (292W)

**PMC:**
- Daily TSS aggregation (sum if multiple rides per day)
- CTL: EWMA with 42-day time constant
- ATL: EWMA with 7-day time constant
- TSB: CTL - ATL

**Functions:**
- `compute_np(power_series: pd.Series) -> float`
- `compute_tss(np_watts: float, duration_s: float, ftp: float) -> float`
- `build_pmc(start=None, end=None, ftp=None) -> pd.DataFrame` — daily CTL/ATL/TSB
- `current_fitness() -> dict` — latest CTL, ATL, TSB snapshot
- `fitness_trend(days=365) -> pd.DataFrame` — CTL trajectory

### `zones.py` — Training Zones

Multiple zone systems for power distribution analysis.

**Coggan classic (7 zones, % of FTP):**
- Active Recovery: <55%, Endurance: 56-75%, Tempo: 76-90%, Threshold: 91-105%, VO2max: 106-120%, Anaerobic: 121-150%, Neuromuscular: >150%

**iLevels (individualized):**
- Zone boundaries derived from inflection points in the fitted PD model
- Requires a `pd_model` dict from `pdcurve.fit_pd_model()`
- Auto-updates as the model changes with new data

**Seiler 3-zone:**
- Zone 1: <80% FTP (below aerobic threshold)
- Zone 2: 80-100% FTP (between thresholds)
- Zone 3: >100% FTP (above lactate threshold)

**Functions:**
- `coggan_zones(ftp: float) -> dict` — zone name → (low, high) watts
- `ilevels(pd_model: dict) -> dict` — individualized zones from PD model
- `seiler_zones(ftp: float) -> dict` — 3-zone boundaries
- `time_in_zones(power_series: pd.Series, zones: dict) -> dict` — seconds per zone
- `ride_distribution(activity_id, zone_system="coggan") -> dict` — zone breakdown for a ride
- `period_distribution(start, end, zone_system="coggan") -> dict` — aggregate across rides

### `ride.py` — Single Ride Analysis

Deep dives into individual rides.

**Ride summary:** Duration, distance, avg/NP/max power, avg/max HR, cadence, elevation, kJ, IF, TSS. Computed from records when device values are missing.

**Interval detection:**
- Find sustained efforts where power > threshold (default: 90% FTP) for > min_duration (default: 30s)
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
- Rank against Coggan's power profile table (Untrained / Fair / Moderate / Good / Very Good / Exceptional / World Class)

**Strengths & limiters:**
- Compare athlete's relative ranking across durations
- Highest-ranked duration = strength, lowest = limiter
- e.g., "5min is Very Good, 1min is Moderate → VO2max strength, anaerobic limiter"

**Phenotype:**
- Classify as Sprinter / Pursuiter / TTer / All-rounder
- Based on Pmax:mFTP and FRC:mFTP ratios from the PD model

**Trend tracking:**
- Rolling power at any duration over time
- W/kg progression
- Period comparisons

**Functions:**
- `power_profile(days=90) -> dict` — watts and W/kg at key durations
- `coggan_ranking(profile: dict) -> dict` — category per duration
- `strengths_limiters(profile: dict) -> dict` — identifies relative strengths and limiters
- `phenotype(pd_model: dict) -> str` — classification with rationale
- `profile_trend(duration_s, window_days=90, step_days=7) -> pd.DataFrame` — rolling power over time
- `compare_profiles(period1: tuple, period2: tuple) -> dict`

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

## Testing Strategy

- Validate mFTP output falls within known 285-299W range
- Validate NP >= avg power for all rides
- Validate TSS ≈ 100 for a 1-hour ride at FTP
- Validate CTL/ATL/TSB arithmetic (TSB = CTL - ATL)
- Validate zone boundaries sum to cover full power range
- Spot-check against Garmin/WKO5 reported values where available

## Dependencies

```
numpy
pandas
scipy
matplotlib
fitdecode
```

All installed in `/tmp/fitenv/` venv (needs recreating after system restart).
