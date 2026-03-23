# P3 Code Changes + Configurable Dashboard — Design Spec

## Goal

Implement the remaining 16 P3 code changes from the EC podcast insights analysis, expose them via API endpoints, and build a configurable D3.js dashboard with per-user layouts and edit mode. The dashboard serves both athlete (JinUk) and coach (Fabiano) with customizable tab/panel arrangements.

## Audience

- **Primary:** Athlete (JinUk) — side-by-side with Claude skills for training analysis
- **Secondary:** Coach (Fabiano) — reviews Health tab first, spots clinical flags at a glance
- **Per-user layouts:** each viewer gets their own tab/panel arrangement stored in SQLite

## Architecture

### Backend

Python modules (`wko5/`) provide computation. FastAPI (`wko5/api/`) exposes REST endpoints. A new `layout.py` module manages per-user dashboard configurations in SQLite.

**Existing stack:** Python 3.14, FastAPI, SQLite, numpy, pandas, D3.js (no bundler, plain browser JS).

### Frontend

Static HTML/CSS/JS served alongside the API. D3.js for charts. No framework — plain browser JS matching the existing `frontend/` structure. Each chart panel is a self-contained module that fetches its own data.

---

## Backend — P3 Code Changes

### 1. clinical.py — 2 new functions

**1.1 `check_reds_flags(days_back=180)`**
Screen for RED-S risk factors from training data:
- Performance declining + training load maintained + weight stable/gaining
- Illness frequency > 1x per 6-8 weeks (from activity gaps)
- Returns: `{risk_level, flags[], recommendation}`
- Source: Persp-36 (Traci Carson), Stellingwerff

**1.2 `check_within_day_deficit(activity_id)`**
Estimate within-day energy deficit risk using ride kJ, end time, and distance to next activity.
- Flag when high-kJ ride ends late evening or back-to-back rides without refueling gap
- Source: WD-59 (effect size 2.03), Persp-36

Integrate both into `get_clinical_flags()`.

### 2. training_load.py — 3 new functions

**2.1 `ftp_growth_curve(window_days=90, step_days=30)`**
Fit logarithmic model to rolling FTP history. Returns:
- `slope` (W/log-week), `r_squared`, `improvement_rate_w_per_year`
- `plateau_detected` (True if slope < 1W/year)
- `growth_phase` ("early", "intermediate", "mature", "plateau")
- Source: WD-61 (Steel et al., N=14,690)

**2.2 `allostatic_load_estimate(days_back=7)`**
Combine ATL with life-stress proxies (missed sessions, RPE trend, comment sentiment if TP data available).
- Returns: `{training_load, life_stress_indicators, combined_load, recommendation}`
- Source: TMT-48 (McEwen), TMT-57

**2.3 `performance_trend(durations=[300, 1200], days_back=30)`**
Track best effort at key durations per ride. Compute 7-day rolling trend. Flag if consistently declining.
- Source: TMT-73

### 3. gap_analysis.py — 2 new functions

**3.1 `opportunity_cost_analysis(power_profile, race_demands, durability_params)`**
Rank training priorities by event-specific impact. For each dimension (FTP, VO2max, durability, sprint, nutrition), estimate time saved from a 10W/2% improvement. Returns ranked list.
- Source: TMT-70, TMT-60

**3.2 `short_power_consistency(duration_s=60, days_back=365)`**
Compare peak vs median effort at a duration across the year. Ratio > 1.3 = consistency problem (not capacity).
- Source: TMT-64

### 4. nutrition.py — 3 new functions

**4.1 `check_absorption_ceiling(intake_g_hr, ceiling_g_hr=90)`**
Flag when prescribed intake exceeds likely absorption ceiling.
- Source: Persp-41

**4.2 `glycogen_budget_daily(ride_kj, ride_duration_h, on_bike_carbs_g, post_ride_delay_h, daily_carb_target_g_kg, weight_kg)`**
Model daily glycogen budget with recovery timing. Returns next-day glycogen estimate and warnings if recovery budget is squeezed.
- Source: WD-59, Persp-41

**4.3 `energy_expenditure()` — add `with_uncertainty=False` parameter**
When True, return `(estimate, low, high)` reflecting ~900 kcal swing from efficiency (20-25% GE) + nutrition label error (~20%).
- Source: Persp-41

### 5. pdcurve.py — 2 new functions

**5.1 `rolling_pd_profile(window_days=90, step_days=14)`**
Compute full PD model parameters at regular intervals. Returns DataFrame with date, mFTP, Pmax, FRC, TTE, mVO2max.
- Source: WD-62, TMT-66

**5.2 `fit_pd_model()` — add `sub_cp_note` to return dict**
Documentation note: "CP model may overestimate sustainable power at durations >TTE."
- Source: 1M AMA

### 6. zones.py — 1 change

**6.1 `coggan_zones()` — add RPE targets to return dict**
Add `rpe` field: Recovery "1-2/10", Endurance "2-3/10", Tempo "4-5/10", etc.
- Backward-compatible: add to existing dict, don't change structure
- Source: TMT-49, TMT-51

### 7. durability.py — 2 small additions

**7.1 `compute_windowed_mmp()` — add `pre_effort_avg_if` field**
For each window, compute average IF of preceding riding. Classify as endurance/tempo/race preload.
- Source: WD-60

**7.2 `fit_durability_model()` — add `fueling_confound_warning` flag**
When degradation coefficient `b` is high, warn that poor durability may reflect fueling, not fitness.
- Source: WD-60, TMT-73

---

## Backend — New API Endpoints

Add to `wko5/api/routes.py`:

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/if-distribution` | `if_distribution()` | IF histogram + floor/ceiling |
| GET | `/ftp-growth` | `ftp_growth_curve()` | Log model + plateau detection |
| GET | `/performance-trend` | `performance_trend()` | Day-to-day power tracking |
| GET | `/opportunity-cost/{route_id}` | `opportunity_cost_analysis()` | Ranked training priorities |
| GET | `/glycogen-budget` | `glycogen_budget_daily()` | Daily glycogen model |
| GET | `/rolling-pd-profile` | `rolling_pd_profile()` | All PD params over time |
| GET | `/fresh-baseline` | `check_fresh_baseline()` | Baseline staleness info |
| GET | `/short-power-consistency` | `short_power_consistency()` | Peak vs typical ratio |
| GET | `/layout` | load user layout | Dashboard config (JSON) |
| PUT | `/layout` | save user layout | Update dashboard config |

---

## Backend — Layout Storage

New table in SQLite:

```sql
CREATE TABLE IF NOT EXISTS dashboard_layouts (
    user_token TEXT PRIMARY KEY,
    layout_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

New module `wko5/layout.py`:

```python
def get_layout(user_token: str) -> dict:
    """Load layout for user. Returns default if none exists."""

def save_layout(user_token: str, layout: dict):
    """Save layout for user."""

def get_default_layout(preset: str = "athlete") -> dict:
    """Return default layout. Presets: 'athlete', 'coach'."""
```

### Default Layouts

**Athlete preset:**
```
Today → Health → Fitness → Event Prep → History → Profile
```

**Coach preset:**
```
Health → Today → Fitness → History → Profile → Event Prep
```

---

## Frontend — Layout Config System

### Config Schema

```json
{
  "preset": "athlete",
  "tabs": [
    {
      "id": "today",
      "label": "Today",
      "panels": ["tsb-status", "recent-rides", "clinical-alert"]
    },
    {
      "id": "health",
      "label": "Health",
      "panels": ["clinical-flags", "if-distribution", "if-floor", "panic-training", "reds-screen"]
    }
  ]
}
```

### Panel Registry

Each panel is registered with metadata:

```javascript
WKO5.panels = {
  "clinical-flags":    { category: "health",    label: "Health Status",        endpoint: "/clinical-flags" },
  "if-distribution":   { category: "health",    label: "IF Distribution",      endpoint: "/if-distribution" },
  "ftp-growth":        { category: "fitness",   label: "FTP Growth Curve",     endpoint: "/ftp-growth" },
  "opportunity-cost":  { category: "event-prep", label: "Opportunity Cost",    endpoint: "/opportunity-cost/{route_id}" },
  "glycogen-budget":   { category: "event-prep", label: "Glycogen Budget",     endpoint: "/glycogen-budget" },
  "rolling-pd":        { category: "fitness",   label: "Rolling PD Profile",   endpoint: "/rolling-pd-profile" },
  // ... all existing panels ...
};
```

Categories: Status, Fitness, Event Prep, Health, History, Profile.

---

## Frontend — Edit Mode

### Enter/Exit

- Gear icon (top-right of header bar)
- Click → adds `editing` class to `<body>`
- All panels get overlay: drag handle (top bar) + X button (top-right corner)
- All tabs get: drag handle (left of label) + X button (right)
- "+" button appears: end of tab bar (new tab) + bottom of each panel column (add panel)
- "Done" button replaces gear icon → saves layout via `PUT /layout`, removes `editing` class

### Add Panel Flow

1. Click "+" at bottom of tab
2. Modal opens with panel catalog, grouped by category
3. Click a panel → added to bottom of current tab
4. Modal closes

### Drag Reorder

- Panels: drag within a tab to reorder (vertical sort)
- Tabs: drag horizontally to reorder in tab bar
- Use HTML5 Drag and Drop API (no library needed for simple reorder)

### Delete

- Panel X → removes from current tab (panel remains in catalog for re-adding)
- Tab X → confirmation prompt → removes tab (panels return to catalog)

### New Tab

- "+" at end of tab bar → prompt for tab name → creates empty tab
- Add panels via "+" button

---

## Frontend — New Chart Components

6 new files in `frontend/js/charts/`:

### `health-status.js`
- Flag cards in a 2-column grid (RED/AMBER/GREEN color-coded)
- Each card: severity badge, title, one-line message
- Fetches from `/clinical-flags`

### `if-distribution.js`
- Histogram of IF values in 0.05 bins
- Floor/ceiling markers
- Red highlight on bins > 0.70
- Fetches from `/if-distribution`

### `ftp-growth.js`
- Logarithmic curve fitted to rolling FTP history
- Data points as scatter
- Current marker with growth rate, phase label, TTE
- Fetches from `/ftp-growth`

### `opportunity-cost.js`
- Horizontal bar chart ranking training dimensions
- Color gradient (HIGH=red-yellow, MEDIUM=yellow, LOW=green)
- Each bar labeled with estimated time savings
- Fetches from `/opportunity-cost/{route_id}`

### `glycogen-budget.js`
- Timeline (x=hours) with glycogen level line
- Feed event markers (green dots)
- Bonk zone shaded area at bottom
- Warning text if glycogen approaches danger zone
- Fetches from `/glycogen-budget`

### `rolling-pd.js`
- Multi-line time series: mFTP, Pmax (scaled), FRC, TTE
- Toggleable lines via legend
- Fetches from `/rolling-pd-profile`

---

## File Structure

```
wko5/
  layout.py                          # NEW — layout storage
  clinical.py                        # MODIFY — add check_reds_flags, check_within_day_deficit
  training_load.py                   # MODIFY — add ftp_growth_curve, allostatic_load, performance_trend
  gap_analysis.py                    # MODIFY — add opportunity_cost, short_power_consistency
  nutrition.py                       # MODIFY — add absorption_ceiling, glycogen_budget, energy_uncertainty
  pdcurve.py                         # MODIFY — add rolling_pd_profile, sub_cp_note
  zones.py                           # MODIFY — add RPE targets
  durability.py                      # MODIFY — add pre_effort_intensity, fueling_confound
  api/routes.py                      # MODIFY — add 10 new endpoints
tests/
  test_layout.py                     # NEW
  test_clinical.py                   # MODIFY — new test cases
  test_training_load.py              # MODIFY
  test_gap_analysis.py               # MODIFY
  test_nutrition.py                  # MODIFY
  test_pdcurve.py                    # MODIFY
  test_zones.py                      # MODIFY
  test_durability.py                 # MODIFY
frontend/
  js/
    layout-manager.js                # NEW — edit mode, drag/drop, save/load
    panel-registry.js                # NEW — panel catalog and metadata
    charts/
      health-status.js               # NEW
      if-distribution.js             # NEW
      ftp-growth.js                  # NEW
      opportunity-cost.js            # NEW
      glycogen-budget.js             # NEW
      rolling-pd.js                  # NEW
  index.html                         # MODIFY — add edit mode UI, Health tab
  css/styles.css                     # MODIFY — edit mode styles, new panel styles
```

---

## Testing

- Backend: pytest for all new functions (target: ~205 tests, up from 189)
- Frontend: manual testing via browser
- Test command: `source /tmp/fitenv/bin/activate && pytest tests/ -v`

## Success Criteria

1. All 16 P3 code changes implemented with tests passing
2. All new API endpoints return valid JSON
3. Dashboard loads with default "athlete" layout
4. Edit mode allows add/remove/reorder panels and tabs
5. Layout persists across page reloads (per user token)
6. Fabiano can load "coach" preset with Health tab first
7. New chart panels render with real data from the API
