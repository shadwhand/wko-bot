# P3 Code Changes + Configurable Dashboard — Design Spec (v2)

> Revised after spec review. Changes from v1: localStorage with backend-ready architecture (not SQLite layout storage), explicit dashboard.js refactor section, auth.py fix, deferred allostatic_load, added if-floor/panic-training standalone panels, glycogen budget as interactive form, SortableJS, edit mode cancel button.

## Goal

Implement 15 P3 code changes from EC podcast insights, expose them via API endpoints, and build a configurable D3.js dashboard with localStorage-based layouts (backend-ready architecture) and edit mode.

## Audience

- **Primary:** Athlete (JinUk) — side-by-side with Claude skills
- **Secondary:** Coach (Fabiano) — Health tab first, clinical flags at a glance
- **Future:** Multi-athlete, multi-coach — architecture designed for backend migration

## Architecture

### Backend

Python modules (`wko5/`) provide computation. FastAPI (`wko5/api/`) exposes REST endpoints. No new backend layout storage — layouts live in browser localStorage with a schema designed for future backend migration.

**Existing stack:** Python 3.14, FastAPI, SQLite, numpy, pandas, D3.js (no bundler, plain browser JS).

### Frontend

Static HTML/CSS/JS. D3.js for charts. SortableJS for drag-and-drop. Each chart panel is a self-contained module with `{ create(container), destroy(), refresh() }` interface. Layouts stored in localStorage keyed by `?user=` param (default: `athlete`).

### Backend-Ready Migration Path

When multi-tenant is needed:
1. Add `users` table: `{id, name, token_hash, role, created_at}`
2. Add `dashboard_layouts` table keyed by `user_id` (not raw token)
3. Add `GET/PUT /layout` endpoints
4. Frontend swaps `localStorage.getItem/setItem` for `fetch('/layout')` — everything else unchanged

---

## P0 Fixes (from spec review)

### Fix 1: auth.py fail-open bug

Change `auth.py` lines 16-17 from:
```python
if _token is None:
    return
```
To:
```python
if _token is None:
    raise HTTPException(status_code=503, detail="Auth not configured")
```

### Fix 2: Explicit dashboard.js refactor

The existing `dashboard.js` (~1,250 lines) has hardcoded `loadToday()`, `loadFitness()`, etc. functions that assume static DOM structure. This must be refactored to a dynamic panel system:

- Replace tab-specific loaders with generic `loadTab(tabConfig)`
- Each panel registered with `{ create(container), destroy(), refresh() }` interface
- `loadTab` iterates `tabConfig.panels`, instantiates each from registry, calls `create()`
- All existing panels (pmc, mmp, clinical, segment-profile, zones, ride-timeseries) must be wrapped in the new interface
- This is the highest-risk integration point

---

## Backend — P3 Code Changes (15 functions)

### 1. clinical.py — 2 new functions

**1.1 `check_reds_flags(days_back=180)`**
Screen for RED-S risk factors:
- Performance declining + training load maintained + weight stable/gaining
- Illness detection: 5+ consecutive days with no activity, excluding rest weeks (prior week TSS > 200)
- Returns: `{risk_level, flags[], recommendation}`

**1.2 `check_within_day_deficit(activity_id)`**
Estimate within-day energy deficit risk using ride kJ, end time, distance to next activity.

Integrate both into `get_clinical_flags()`.

### 2. training_load.py — 2 new functions

**2.1 `ftp_growth_curve(window_days=90, step_days=30)`**
Fit logarithmic model to rolling FTP. Returns slope, r_squared, improvement_rate, plateau_detected, growth_phase.

**2.2 `performance_trend(durations=[300, 1200], days_back=30)`**
Track best effort at key durations per ride. 7-day rolling trend. Flag if declining.

*`allostatic_load_estimate` DEFERRED — RPE not in FIT files, data contract too weak.*

### 3. gap_analysis.py — 2 new functions

**3.1 `opportunity_cost_analysis(route_id)`**
Simplified version: derives race demands from route segments (via `analyze_ride_segments`), compares against current power profile + durability model. Ranks training dimensions by estimated time saved. Uses existing segment/demand infrastructure.

**3.2 `short_power_consistency(duration_s=60, days_back=365)`**
Peak vs median ratio. >1.3 = consistency problem.

### 4. nutrition.py — 3 new functions

**4.1 `check_absorption_ceiling(intake_g_hr, ceiling_g_hr=90)`**
Flag when prescribed intake exceeds likely absorption ceiling.

**4.2 `glycogen_budget_daily(ride_kj, ride_duration_h, on_bike_carbs_g, post_ride_delay_h, daily_carb_target_g_kg, weight_kg)`**
Model daily glycogen budget with recovery timing. Returns next-day estimate + warnings.

**4.3 `energy_expenditure()` — add `with_uncertainty=False`**
When True, return `(estimate, low, high)` reflecting efficiency + label error.

### 5. pdcurve.py — 2 additions

**5.1 `rolling_pd_profile(window_days=90, step_days=14)`**
Full PD params at regular intervals. Returns DataFrame with mFTP, Pmax, FRC, TTE over time.

**5.2 `fit_pd_model()` — add `sub_cp_note` to return dict**
Documentation note for durations beyond TTE.

### 6. zones.py — 1 change

**6.1 `coggan_zones()` — add `rpe` field to zone dicts**
Backward-compatible addition. E.g., `"rpe": "7-8/10"` for threshold.

### 7. durability.py — 2 additions

**7.1 `compute_windowed_mmp()` — add `pre_effort_avg_if` field**
Classify preceding riding as endurance/tempo/race preload.

**7.2 `fit_durability_model()` — add `fueling_confound_warning`**
Flag when high degradation coefficient may reflect fueling, not fitness.

---

## Backend — New API Endpoints (8 total)

| Method | Path | Handler | Cache |
|--------|------|---------|-------|
| GET | `/if-distribution` | `if_distribution()` | 5min |
| GET | `/ftp-growth` | `ftp_growth_curve()` | warmup + 5min |
| GET | `/performance-trend` | `performance_trend()` | 5min |
| GET | `/opportunity-cost/{route_id:int}` | `opportunity_cost_analysis()` | 5min |
| POST | `/glycogen-budget` | `glycogen_budget_daily()` | none (interactive) |
| GET | `/rolling-pd-profile` | `rolling_pd_profile()` | warmup + 5min |
| GET | `/fresh-baseline` | `check_fresh_baseline()` | 5min |
| GET | `/short-power-consistency` | `short_power_consistency()` | 5min |

All GET endpoints use `Depends(verify_token)`. POST `/glycogen-budget` also requires auth. `route_id` is typed as `int` in FastAPI path definition.

Add `rolling_pd_profile` and `ftp_growth_curve` to `warmup_cache()`.

---

## Frontend — Layout System

### localStorage Schema (backend-ready)

```json
{
  "version": 1,
  "preset": "athlete",
  "tabs": [
    {"id": "today", "label": "Today", "panels": ["tsb-status", "recent-rides", "clinical-alert"]},
    {"id": "health", "label": "Health", "panels": ["clinical-flags", "if-distribution", "if-floor", "panic-training", "reds-screen"]},
    {"id": "fitness", "label": "Fitness", "panels": ["pmc", "mmp", "rolling-ftp", "ftp-growth", "rolling-pd"]},
    {"id": "event-prep", "label": "Event Prep", "panels": ["gap-analysis", "opportunity-cost", "pacing", "glycogen-budget", "segment-profile", "demand-heatmap"]},
    {"id": "history", "label": "History", "panels": ["rides-table", "training-blocks", "phase-timeline"]},
    {"id": "profile", "label": "Profile", "panels": ["coggan-ranking", "phenotype", "power-profile", "athlete-config", "posterior-summary"]}
  ]
}
```

Storage key: `wko5-layout-{user}` where `{user}` comes from `?user=` URL param (default: `athlete`).

### Two Default Presets

**Athlete:** Today → Health → Fitness → Event Prep → History → Profile
**Coach:** Health → Today → Fitness → History → Profile → Event Prep

### Panel Registry

Every panel registered with metadata and interface:

```javascript
WKO5.panels = {
  "clinical-flags":   { category: "health",     label: "Health Status",        description: "RED/AMBER/GREEN flags from all clinical checks", endpoint: "/clinical-flags" },
  "if-floor":         { category: "health",     label: "IF Floor Alert",       description: "Endurance ride intensity floor — flags if riding too hard", endpoint: "/clinical-flags" },
  "panic-training":   { category: "health",     label: "Panic Training",       description: "Detects sudden intensity spikes after low-load periods", endpoint: "/clinical-flags" },
  "reds-screen":      { category: "health",     label: "RED-S Screen",         description: "Relative Energy Deficiency screening from training data", endpoint: "/clinical-flags" },
  "if-distribution":  { category: "health",     label: "IF Distribution",      description: "Histogram of ride intensity factors with floor/ceiling markers", endpoint: "/if-distribution" },
  "ftp-growth":       { category: "fitness",    label: "FTP Growth Curve",     description: "Logarithmic fit to FTP history — growth phase and plateau detection", endpoint: "/ftp-growth" },
  "rolling-pd":       { category: "fitness",    label: "Rolling PD Profile",   description: "mFTP, Pmax, FRC, TTE tracked over time (default: mFTP only)", endpoint: "/rolling-pd-profile" },
  "opportunity-cost": { category: "event-prep", label: "Opportunity Cost",     description: "Ranked training priorities for a specific event route", endpoint: "/opportunity-cost/{route_id}" },
  "glycogen-budget":  { category: "event-prep", label: "Glycogen Budget",      description: "Interactive glycogen timeline — input ride params, see bonk risk", endpoint: "/glycogen-budget", interactive: true },
  // ... all existing panels ...
};
```

- `if-floor`, `panic-training`, `reds-screen` are standalone panels that extract specific flags from `/clinical-flags` response
- `rolling-pd` defaults to showing mFTP line only; Pmax, FRC, TTE toggleable via legend
- `glycogen-budget` has `interactive: true` — renders input form + chart
- `opportunity-cost` defaults to athlete's primary event route from config; dropdown to change

---

## Frontend — Dashboard Refactor

### Current State (dashboard.js ~1,250 lines)

```
loadTab() → switch(tab) → loadToday() / loadFitness() / ...
loadToday() → renderTSBStatus(qs('[data-chart="tsb-status"]'), data)
```

Each `loadX()` hardcodes panel selectors and data mapping.

### Target State

```
loadTab(tabConfig) → for panel of tabConfig.panels → registry[panel].create(container)
```

Each panel in registry implements:
```javascript
{
  create(container) { /* fetch data, render D3 chart into container */ },
  destroy()         { /* cleanup listeners, abort in-flight fetches */ },
  refresh()         { /* re-fetch and re-render */ }
}
```

### Migration Strategy

1. Wrap each existing chart function in the `{ create, destroy, refresh }` interface
2. Register all existing panels in `panel-registry.js`
3. Replace `loadToday()` etc. with generic `loadTab(tabConfig)`
4. Remove hardcoded panel `<div>`s from `index.html` — generated dynamically
5. Verify all 19 existing panels work through the new system before adding new ones

---

## Frontend — Edit Mode

### Enter/Exit

- Gear icon top-right → `<body class="editing">`
- **Done** button saves to localStorage, exits edit mode
- **Cancel** button restores pre-edit snapshot, exits edit mode (no save)
- Pre-edit layout snapshot stored in JS variable on edit mode entry

### Panel Operations

- **Remove:** X button on panel → panel removed from tab (tooltip: "Removed from tab. Still available in catalog.")
- **Reorder:** Drag via SortableJS (vertical sort within tab)
- **Add:** "+" button at bottom of tab → modal with panel catalog (grouped by category, each panel has description)

### Tab Operations

- **Remove:** X on tab → confirm dialog → removes tab
- **Reorder:** Drag via SortableJS (horizontal sort in tab bar)
- **Add:** "+" at end of tab bar → prompt for name (max 20 chars, no duplicates, non-empty)
- **Rename:** Double-click tab label in edit mode

### Empty Tab State

- Show "+" prompt in empty area: "This tab has no panels. Click + to add some."
- Saving an empty tab is allowed (user may be building it up)

### Error States

- **Panel endpoint fails:** Red border card with "Unable to load — check connection" + retry button
- **No data in time range:** Gray card with "No data in the last N days"
- **Clinical panel empty:** Explicit "No flags — all clear" green card (never blank)

---

## Frontend — New Chart Components (8 files)

```
frontend/js/charts/
  health-status.js     — flag cards grid (RED/AMBER/GREEN), full-width at top of Health tab
  if-floor.js          — single flag card extracted from /clinical-flags (IF floor specific)
  panic-training.js    — single flag card extracted from /clinical-flags (panic training specific)
  if-distribution.js   — histogram of IF values, red highlight on bins > 0.70
  ftp-growth.js        — log curve + growth rate + phase label + TTE
  opportunity-cost.js  — horizontal bar chart, ranked by time saved, route dropdown
  glycogen-budget.js   — input form (ride kJ, duration, carbs, weight, timing) + timeline chart + bonk zone
  rolling-pd.js        — multi-line time series, mFTP default visible, others toggleable
```

---

## File Structure

```
wko5/
  clinical.py            — MODIFY: +2 functions, integrate into get_clinical_flags()
  training_load.py       — MODIFY: +2 functions
  gap_analysis.py        — MODIFY: +2 functions
  nutrition.py           — MODIFY: +3 functions
  pdcurve.py             — MODIFY: +1 function, +1 field
  zones.py               — MODIFY: +1 field to coggan_zones()
  durability.py          — MODIFY: +2 fields
  api/routes.py          — MODIFY: +8 endpoints, warmup_cache additions
  api/auth.py            — MODIFY: fix fail-open bug
tests/
  test_clinical.py       — MODIFY: +tests
  test_training_load.py  — MODIFY: +tests
  test_gap_analysis.py   — MODIFY: +tests
  test_nutrition.py      — MODIFY: +tests
  test_pdcurve.py        — MODIFY: +tests
  test_zones.py          — MODIFY: +tests
  test_durability.py     — MODIFY: +tests
frontend/
  js/
    panel-registry.js    — NEW: panel catalog with metadata + create/destroy/refresh
    layout-manager.js    — NEW: edit mode, localStorage save/load, SortableJS integration
    dashboard.js         — MAJOR REFACTOR: generic loadTab(), dynamic panel instantiation
    charts/
      health-status.js   — NEW
      if-floor.js        — NEW
      panic-training.js  — NEW
      if-distribution.js — NEW
      ftp-growth.js      — NEW
      opportunity-cost.js — NEW
      glycogen-budget.js — NEW (interactive form + chart)
      rolling-pd.js      — NEW
  lib/
    Sortable.min.js      — NEW vendor (SortableJS, ~8KB)
  index.html             — MODIFY: remove static panel divs, add edit mode UI, Health tab
  css/styles.css         — MODIFY: edit mode styles, error/empty states, new panel styles
```

---

## Testing

- Backend: pytest for all new functions. Target: ~210 tests (up from 189, ~2-3 per new function)
- Frontend: manual testing in browser
- Test command: `source /tmp/fitenv/bin/activate && pytest tests/ -v`

## Implementation Phases

| Phase | Work | Risk |
|-------|------|------|
| **0. Prep** | Fix auth.py fail-open. | Low |
| **1. Backend** | 15 P3 functions + tests across 7 modules. Parallelizable. | Low |
| **2. API** | 8 endpoints + warmup cache. | Low |
| **3. Dashboard refactor** | Refactor dashboard.js → dynamic panels. Wrap existing charts. | **HIGH** |
| **4. New charts** | 8 chart files. Register in panel registry. | Medium |
| **5. Edit mode** | layout-manager.js, SortableJS, localStorage, presets. | Medium |

## Success Criteria

1. All 15 P3 functions implemented with tests passing (~210 tests)
2. Auth.py fail-open bug fixed
3. All 8 new API endpoints return valid JSON
4. All 19 existing panels work through new dynamic panel system
5. 8 new chart panels render with real data
6. Edit mode: add/remove/reorder panels and tabs, with Cancel
7. Layout persists in localStorage across page reloads
8. Athlete and Coach presets load correctly via `?user=` param
9. Error states render for failed/empty panels (never blank)
10. Glycogen budget panel accepts interactive input
