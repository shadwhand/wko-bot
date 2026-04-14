# WKO5 Analyzer

A Python library for WKO5-style cycling power analysis built on a local DuckDB database of Garmin FIT file data. Includes a power duration model, training load tracking (CTL/ATL/TSB), individualized training zones, ride analysis, power profiling, and Jupyter notebooks for visualization.

**Your data stays local.** This repo provides the tools and training science knowledge base. You bring your own ride data by syncing from Garmin Connect, Strava, or importing FIT files. Your ride database, personal ride logs, race plans, and reports are gitignored — they live on your machine only.

## Quick Start

The fastest way to get up and running:

```bash
bash setup.sh
```

This walks you through Python environment, athlete config, data source connection, and knowledge base setup interactively.

Or follow the manual steps below.

### 1. Create Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install numpy pandas scipy matplotlib fitdecode garth httpx duckdb
```

### 2. Get your data

You need cycling activities with power meter data. Choose one:

**Option A: Garmin Connect (recommended)**

Syncs directly from your Garmin account. First run prompts for credentials; tokens are saved to `~/.garth/` for future syncs.

```bash
python wko5/garmin_sync.py --days 90
```

```bash
# Sync since last activity in DB
python wko5/garmin_sync.py

# Sync from a specific date
python wko5/garmin_sync.py --from 2024-01-01

# Also save FIT files locally
python wko5/garmin_sync.py --save-fit
```

**Option B: Strava**

Syncs via the Strava API. Requires a free Strava API app (one-time setup):

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create an application (set callback domain to `localhost`)
3. Note your Client ID and Client Secret
4. Run the sync:

```bash
python wko5/strava_sync.py --days 90
```

First run prompts for credentials and opens a browser for OAuth authorization. Tokens are saved to `~/.strava_tokens/` for future syncs.

```bash
# Sync since last activity in DB
python wko5/strava_sync.py

# Sync from a specific date
python wko5/strava_sync.py --from 2024-01-01
```

**Option C: Bulk FIT file import**

If you have FIT files from any source (Garmin export, Wahoo, Hammerhead, etc.):

1. Place `.fit` files in `fit-files/`
2. Run the ingestion:

```bash
python wko5/ingest_missing.py
```

This scans all FIT files, identifies cycling activities with power data, and ingests them into `wko5/cycling_power.duckdb`.

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

DuckDB database (`wko5/cycling_power.duckdb`) with the following tables:

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

## Knowledge Base (qmd)

The platform includes a compiled knowledge wiki over 2,012 TrainingPeaks articles, 53 Empirical Cycling podcast episodes, and nutrition research — searchable via qmd.

### Requirements

- Node.js 20+ (`node --version`)
- npm (`npm --version`)

### Setup

```bash
# Install qmd
npm install -g @tobilu/qmd

# Index all collections (first time)
qmd update
qmd embed
```

This downloads ~2GB of GGUF models (EmbeddingGemma 300M + Qwen3-Reranker 0.6B) on first run.

### Configuration

- **qmd config:** `.qmd/qmd.yml` (6 collections: wiki, empirical-cycling, trainingpeaks, nutrition, reports, code)
- **Wiki schema:** `docs/research/wiki/SCHEMA.md` (page structure, evidence tags, operations)
- **Index:** `docs/research/wiki/index.md` (master catalog of all wiki pages)

### Usage

```bash
# Search the wiki (recommended — compiled knowledge)
qmd search "FTP plateau" -c wiki
qmd query "how to pace a 200km ride" -c wiki

# Search all default collections (wiki + EC + nutrition + reports)
qmd query "durability fatigue modeling"

# Search raw TP articles (opt-in, 2,012 articles)
qmd search "Tour de France power analysis" -c trainingpeaks
```

### Claude Code Integration

qmd runs as an MCP server — configured in `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "qmd": {
      "command": "qmd",
      "args": ["mcp"]
    }
  }
}
```

This gives Claude Code direct access to `query`, `get`, `multi_get`, and `status` tools.

### HTTP API

For programmatic access (FastAPI integration):

```bash
# Start the HTTP daemon
qmd mcp --http --daemon

# Health check
curl http://localhost:8181/health

# Search via FastAPI
curl "http://localhost:8000/api/knowledge?q=pacing+strategy&collections=wiki"
```

### Wiki Operations

- **Ingest new sources:** Follow `tools/wiki-ingest.md`
- **Lint pass:** Follow `tools/wiki-lint.md`
- **Re-index after changes:** `qmd update && qmd embed`

See `docs/research/wiki/SCHEMA.md` for the full Karpathy-style wiki workflow (ingest, query, lint, maintenance).

## Dependencies

- Python 3.10+
- Node.js 20+ (for qmd)
- numpy
- pandas
- scipy
- matplotlib
- fitdecode
- duckdb
- httpx (for knowledge client)
