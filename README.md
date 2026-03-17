# WKO5 Analyzer

A Python library for WKO5-style cycling power analysis built on a local SQLite database of Garmin FIT file data. Includes a power duration model, training load tracking (CTL/ATL/TSB), individualized training zones, ride analysis, power profiling, and Jupyter notebooks for visualization.

## Quick Start

### 1. Create Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install numpy pandas scipy matplotlib fitdecode
```

### 2. Get your data

**Option A: Garmin bulk export (historical data)**

1. Request your data export from [Garmin Account](https://www.garmin.com/account/datamanagement/)
2. Extract the FIT files from the zip into `fit-files/`
3. Run the ingestion script:

```bash
python wko5/ingest_missing.py
```

This scans all FIT files, identifies cycling activities with power data, and ingests them into `wko5/cycling_power.db`.

**Option B: Sync new activities from Garmin Connect**

```bash
python wko5/garmin_sync.py
```

First run prompts for Garmin credentials and MFA. Session tokens are saved to `~/.garmin_tokens/` for future runs.

```bash
# Sync since last activity in DB
python wko5/garmin_sync.py

# Sync last 30 days
python wko5/garmin_sync.py --days 30

# Sync from a specific date
python wko5/garmin_sync.py --from 2024-01-01

# Also save FIT files locally
python wko5/garmin_sync.py --save-fit
```

### 3. Use the library

```python
from wko5.training_load import current_fitness
print(current_fitness())
# {'CTL': 72.1, 'ATL': 48.8, 'TSB': 23.3, 'date': '2025-08-09'}
```

## Library Modules

| Module | Description |
|---|---|
| `wko5.db` | DB connection, queries, athlete constants |
| `wko5.clean` | Power spike removal, dropout handling, gap filling |
| `wko5.pdcurve` | MMP computation (cached), PD model fitting (Pmax, FRC, mFTP, TTE, VO2max) |
| `wko5.training_load` | Normalized Power, TSS (cached), CTL/ATL/TSB, efficiency factor |
| `wko5.zones` | Coggan 7-zone, iLevels, Seiler 3-zone, HR zones, time-in-zone |
| `wko5.ride` | Ride summary, interval detection, lap analysis, HR decoupling, best efforts |
| `wko5.profile` | Power profile, Coggan ranking, strengths/limiters, phenotype, fatigue resistance |

### Examples

```python
# Power Duration Model
from wko5.pdcurve import compute_envelope_mmp, fit_pd_model
mmp = compute_envelope_mmp(days=90)
model = fit_pd_model(mmp)
print(f"mFTP: {model['mFTP']}W  Pmax: {model['Pmax']}W  FRC: {model['FRC']} kJ  TTE: {model['TTE']} min")

# Power profile and ranking
from wko5.profile import power_profile, coggan_ranking, strengths_limiters
profile = power_profile(days=90)
ranking = coggan_ranking(profile)
sl = strengths_limiters(profile)
print(f"Strength: {sl['strength']['label']} ({sl['strength']['category']})")
print(f"Limiter: {sl['limiter']['label']} ({sl['limiter']['category']})")

# Analyze a ride
from wko5.db import get_activities
from wko5.ride import ride_summary, detect_intervals
acts = get_activities(start="2025-08-10", end="2025-08-10")
summary = ride_summary(acts.iloc[0]['id'])
intervals = detect_intervals(acts.iloc[0]['id'])

# Training zones
from wko5.zones import coggan_zones, ilevels
zones = coggan_zones(292)  # Classic Coggan zones at FTP=292W
izones = ilevels(model)    # Individualized from PD model

# Rolling FTP over training history
from wko5.pdcurve import rolling_ftp
ftp_trend = rolling_ftp(window_days=90, step_days=14)
```

## Notebooks

Three Jupyter notebooks in `notebooks/` for visual analysis:

| Notebook | Contents |
|---|---|
| `power_duration.ipynb` | MMP curve, PD model overlay, rolling FTP chart, period comparison |
| `training_load.ipynb` | PMC chart (CTL/ATL/TSB), weekly TSS, EF trend |
| `ride_analysis.ipynb` | Single-ride template: power/HR/cadence plots, intervals, zones, best efforts |

```bash
pip install jupyter
cd notebooks
jupyter notebook
```

## Database Schema

The SQLite database (`wko5/cycling_power.db`) has the following tables:

- **activities** — one row per ride (session summary: power, HR, cadence, distance, elevation, TSS, NP, IF)
- **records** — per-second data (power, HR, cadence, speed, altitude, temperature, GPS)
- **laps** — device-reported laps
- **mmp_cache** — cached Mean Max Power arrays per activity (populated lazily)
- **tss_cache** — cached TSS values per activity (populated lazily)

## Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

58 tests covering all modules.

## Configuration

Athlete constants are in `wko5/db.py`:

```python
WEIGHT_KG = 78.0
FTP_RANGE = (285, 299)
FTP_DEFAULT = 292
```

Update these for your own data.

## Dependencies

- Python 3.10+
- numpy
- pandas
- scipy
- matplotlib
- fitdecode
