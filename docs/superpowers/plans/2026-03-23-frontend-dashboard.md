# Frontend Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the D3.js dashboard from hardcoded panel wiring to a dynamic, configurable panel system with localStorage layouts, edit mode, and 8 new chart panels.

**Architecture:** Three-phase approach: (1) Build panel registry + layout manager as new infrastructure alongside existing code, (2) Migrate existing panels to the new registry interface then switch over, (3) Add new chart panels + edit mode on top of the working system. Each phase produces a working dashboard — no big-bang cutover.

**Tech Stack:** D3.js v7, SortableJS (~8KB), plain browser JS (no bundler/framework), CSS custom properties

**Spec:** `docs/superpowers/specs/2026-03-23-p3-dashboard-design-v2.md` (Frontend sections)

**Backend:** All 8 P3 API endpoints are already implemented and tested (214 tests passing).

**Test method:** Manual browser testing at `http://localhost:8000` (run API with `source /tmp/fitenv/bin/activate && python run_api.py`)

**CRITICAL:** The existing dashboard must work throughout migration. No phase should break what's already rendering. Verify all existing panels still work after each task.

---

## File Structure

```
frontend/
  js/
    panel-registry.js      — NEW: panel catalog, metadata, create/destroy/refresh wrappers
    layout-manager.js      — NEW: localStorage load/save, dynamic tab/panel DOM, edit mode
    dashboard.js           — MAJOR REFACTOR: replace loadTab switch with registry-driven dispatch
    app.js                 — MODIFY: wire layout manager into init flow
    api.js                 — MINOR: add helper methods for new endpoints
    charts/
      health-status.js     — NEW: clinical flag cards grid
      if-floor.js          — NEW: IF floor specific flag card
      panic-training.js    — NEW: panic training specific flag card
      if-distribution.js   — NEW: IF histogram with floor/ceiling markers
      ftp-growth.js        — NEW: logarithmic FTP growth curve
      opportunity-cost.js  — NEW: horizontal bar chart (training priorities)
      glycogen-budget.js   — NEW: interactive form + timeline chart
      rolling-pd.js        — NEW: multi-line PD params over time
      pmc.js               — WRAP: add registry interface
      mmp.js               — WRAP: add registry interface
      clinical.js          — WRAP: add registry interface
      segment-profile.js   — WRAP: add registry interface
      ride-timeseries.js   — WRAP: add registry interface (if used as panel)
      zones.js             — WRAP: add registry interface
  lib/
    Sortable.min.js        — NEW: SortableJS vendor (~8KB)
  index.html               — MODIFY: remove static panels, add edit mode UI
  css/styles.css           — MODIFY: edit mode, error states, new panel styles
```

---

## Task 1: Panel Registry — the foundation

**Files:**
- Create: `frontend/js/panel-registry.js`
- Create: `frontend/lib/Sortable.min.js` (download vendor file)

This is the core data structure. Every panel (existing + new) gets registered here with metadata and a standard interface.

- [ ] **Step 1: Download SortableJS**

```bash
curl -sL "https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js" -o frontend/lib/Sortable.min.js
```

Verify file exists and is ~8KB.

- [ ] **Step 2: Create panel-registry.js**

```javascript
/**
 * WKO5 Panel Registry
 *
 * Every dashboard panel is registered here with metadata and a standard interface.
 * The layout manager uses this registry to instantiate panels dynamically.
 *
 * Panel interface: { create(container, api), destroy(), refresh(api) }
 * - create: fetch data, render into container DOM element
 * - destroy: cleanup listeners, abort fetches, remove SVG
 * - refresh: re-fetch and re-render (called on manual refresh)
 */

(function () {
  'use strict';

  // Request deduplication cache (shared across panels hitting same endpoint)
  const _fetchCache = new Map();
  const CACHE_TTL = 5000; // 5 seconds

  function cachedFetch(api, method, args) {
    const key = method + ':' + JSON.stringify(args || {});
    const cached = _fetchCache.get(key);
    if (cached && Date.now() - cached.time < CACHE_TTL) {
      return Promise.resolve(cached.data);
    }
    return api[method](args).then(function (data) {
      _fetchCache.set(key, { data: data, time: Date.now() });
      return data;
    });
  }

  // Clear cache when tab switches
  function clearFetchCache() {
    _fetchCache.clear();
  }

  /**
   * Panel catalog. Each entry:
   * - category: grouping for the add-panel modal
   * - label: display name
   * - description: one-line help text
   * - endpoint: API endpoint (informational, panels fetch their own data)
   * - interactive: true if panel has input form (glycogen-budget)
   * - factory: function(container, api) that creates the panel and returns { destroy, refresh }
   */
  const panels = {
    // ── Existing panels (wrapped) ──────────────────────────────────────
    'tsb-status':       { category: 'status',     label: 'TSB Status',           description: 'Current form (TSB), fitness (CTL), fatigue (ATL)', factory: null /* set in wrap phase */ },
    'recent-rides':     { category: 'status',     label: 'Recent Rides',         description: 'Last 5-10 rides with key metrics', factory: null },
    'clinical-alert':   { category: 'status',     label: 'Clinical Alert',       description: 'Summary alert banner (RED/AMBER/GREEN)', factory: null },
    'pmc':              { category: 'fitness',    label: 'PMC Chart',            description: 'Performance Management Chart — CTL, ATL, TSB over time', factory: null },
    'mmp':              { category: 'fitness',    label: 'MMP / PD Curve',       description: 'Mean Maximal Power and Power-Duration model', factory: null },
    'rolling-ftp':      { category: 'fitness',    label: 'Rolling FTP',          description: 'FTP trend over time from rolling 90-day windows', factory: null },
    'power-profile':    { category: 'fitness',    label: 'Power Profile',        description: 'Coggan power profile — 5s, 1min, 5min, 20min rankings', factory: null },
    'segment-profile':  { category: 'event-prep', label: 'Segment Profile',      description: 'Elevation and power demands per route segment', factory: null },
    'demand-heatmap':   { category: 'event-prep', label: 'Demand Heatmap',       description: 'Power demand ratios across route segments', factory: null },
    'pacing':           { category: 'event-prep', label: 'Pacing Plan',          description: 'Durability-aware pacing with target power per segment', factory: null },
    'gap-analysis':     { category: 'event-prep', label: 'Gap Analysis',         description: 'Monte Carlo feasibility with bottleneck identification', factory: null },
    'rides-table':      { category: 'history',    label: 'Rides Table',          description: 'Sortable table of all rides with key metrics', factory: null },
    'training-blocks':  { category: 'history',    label: 'Training Blocks',      description: 'Block-level stats — volume, intensity, compliance', factory: null },
    'phase-timeline':   { category: 'history',    label: 'Phase Timeline',       description: 'Detected training phases (base/build/peak/recovery)', factory: null },
    'intensity-dist':   { category: 'history',    label: 'Intensity Distribution', description: 'Seiler 3-zone and Coggan 7-zone time distribution', factory: null },
    'coggan-ranking':   { category: 'profile',    label: 'Coggan Ranking',       description: 'Power profile vs Coggan classification table', factory: null },
    'phenotype':        { category: 'profile',    label: 'Phenotype',            description: 'Sprinter / Pursuiter / TTer / All-rounder classification', factory: null },
    'athlete-config':   { category: 'profile',    label: 'Athlete Config',       description: 'Weight, FTP, CdA, and other configurable parameters', factory: null },
    'posterior-summary': { category: 'profile',   label: 'Posterior Summary',    description: 'Bayesian model confidence — mFTP, FRC, durability posteriors', factory: null },

    // ── New panels (P3) ────────────────────────────────────────────────
    'clinical-flags':   { category: 'health',     label: 'Health Status',        description: 'RED/AMBER/GREEN flags from all clinical checks', factory: null },
    'if-floor':         { category: 'health',     label: 'IF Floor Alert',       description: 'Endurance ride intensity floor — flags if riding too hard', factory: null },
    'panic-training':   { category: 'health',     label: 'Panic Training',       description: 'Detects sudden intensity spikes after low-load periods', factory: null },
    'reds-screen':      { category: 'health',     label: 'RED-S Screen',         description: 'Relative Energy Deficiency screening from training data', factory: null },
    'if-distribution':  { category: 'health',     label: 'IF Distribution',      description: 'Histogram of ride intensity factors with floor/ceiling markers', factory: null },
    'ftp-growth':       { category: 'fitness',    label: 'FTP Growth Curve',     description: 'Logarithmic fit to FTP history — growth phase and plateau detection', factory: null },
    'rolling-pd':       { category: 'fitness',    label: 'Rolling PD Profile',   description: 'mFTP, Pmax, FRC, TTE tracked over time (default: mFTP only)', factory: null },
    'opportunity-cost': { category: 'event-prep', label: 'Opportunity Cost',     description: 'Ranked training priorities for a specific event route', factory: null },
    'glycogen-budget':  { category: 'event-prep', label: 'Glycogen Budget',      description: 'Interactive glycogen timeline — input ride params, see bonk risk', interactive: true, factory: null },
    'short-power':      { category: 'fitness',    label: 'Short Power Consistency', description: 'Peak vs typical power at 1min — capacity vs consistency diagnosis', factory: null },
    'fresh-baseline':   { category: 'health',     label: 'Fresh Baseline',       description: 'Staleness check for max efforts at key durations', factory: null },
  };

  // Category metadata for the add-panel modal
  const categories = {
    'status':     { label: 'Status',     order: 0 },
    'health':     { label: 'Health',     order: 1 },
    'fitness':    { label: 'Fitness',    order: 2 },
    'event-prep': { label: 'Event Prep', order: 3 },
    'history':    { label: 'History',    order: 4 },
    'profile':    { label: 'Profile',    order: 5 },
  };

  /**
   * Register a panel factory. Called by chart JS files after they define their class.
   * @param {string} id - Panel ID matching a key in the panels object
   * @param {function(HTMLElement, WKO5API): {destroy: function, refresh: function}} factory
   */
  function registerFactory(id, factory) {
    if (panels[id]) {
      panels[id].factory = factory;
    } else {
      console.warn('[Registry] Unknown panel ID:', id);
    }
  }

  /**
   * Get panel metadata by ID.
   */
  function getPanel(id) {
    return panels[id] || null;
  }

  /**
   * Get all panels, optionally filtered by category.
   */
  function getPanels(category) {
    if (!category) return panels;
    var result = {};
    for (var id in panels) {
      if (panels[id].category === category) result[id] = panels[id];
    }
    return result;
  }

  /**
   * Get categories with their panels.
   */
  function getCatalog() {
    var catalog = [];
    var catKeys = Object.keys(categories).sort(function (a, b) {
      return categories[a].order - categories[b].order;
    });
    catKeys.forEach(function (catId) {
      var catPanels = [];
      for (var id in panels) {
        if (panels[id].category === catId) {
          catPanels.push({ id: id, label: panels[id].label, description: panels[id].description });
        }
      }
      catalog.push({ id: catId, label: categories[catId].label, panels: catPanels });
    });
    return catalog;
  }

  // Export
  window.WKO5Registry = {
    panels: panels,
    categories: categories,
    registerFactory: registerFactory,
    getPanel: getPanel,
    getPanels: getPanels,
    getCatalog: getCatalog,
    cachedFetch: cachedFetch,
    clearFetchCache: clearFetchCache,
  };
})();
```

- [ ] **Step 3: Add script tags to index.html**

Add before `dashboard.js` in index.html:
```html
<script defer src="lib/Sortable.min.js"></script>
<script defer src="js/panel-registry.js"></script>
```

- [ ] **Step 4: Verify page still loads**

Open `http://localhost:8000` — existing dashboard should work unchanged. Open browser console — should see no errors. `window.WKO5Registry` should exist.

- [ ] **Step 5: Commit**

```bash
git add frontend/js/panel-registry.js frontend/lib/Sortable.min.js frontend/index.html
git commit -m "feat: panel registry — foundation for configurable dashboard"
```

---

## Task 2: Layout Manager — localStorage + dynamic DOM

**Files:**
- Create: `frontend/js/layout-manager.js`

- [ ] **Step 1: Create layout-manager.js**

This manages: loading layout from localStorage, saving layout, generating tab/panel DOM dynamically, and (later) edit mode.

```javascript
/**
 * WKO5 Layout Manager
 *
 * Manages dashboard layout: load/save from localStorage, generate tabs + panels,
 * and (phase 2) edit mode with drag/drop.
 */

(function () {
  'use strict';

  const LAYOUT_VERSION = 1;

  // Default presets
  const PRESETS = {
    athlete: {
      version: LAYOUT_VERSION,
      preset: 'athlete',
      tabs: [
        { id: 'today',      label: 'Today',      panels: ['tsb-status', 'recent-rides', 'clinical-alert'] },
        { id: 'health',     label: 'Health',      panels: ['clinical-flags', 'if-distribution', 'if-floor', 'panic-training', 'reds-screen'] },
        { id: 'fitness',    label: 'Fitness',     panels: ['pmc', 'mmp', 'rolling-ftp', 'ftp-growth', 'rolling-pd'] },
        { id: 'event-prep', label: 'Event Prep',  panels: ['gap-analysis', 'opportunity-cost', 'pacing', 'glycogen-budget', 'segment-profile', 'demand-heatmap'] },
        { id: 'history',    label: 'History',     panels: ['rides-table', 'training-blocks', 'phase-timeline', 'intensity-dist'] },
        { id: 'profile',    label: 'Profile',     panels: ['coggan-ranking', 'phenotype', 'power-profile', 'athlete-config', 'posterior-summary'] },
      ],
    },
    coach: {
      version: LAYOUT_VERSION,
      preset: 'coach',
      tabs: [
        { id: 'health',     label: 'Health',      panels: ['clinical-flags', 'if-distribution', 'if-floor', 'panic-training', 'reds-screen', 'fresh-baseline'] },
        { id: 'today',      label: 'Today',      panels: ['tsb-status', 'recent-rides', 'clinical-alert'] },
        { id: 'fitness',    label: 'Fitness',     panels: ['pmc', 'mmp', 'rolling-ftp', 'ftp-growth', 'rolling-pd', 'short-power'] },
        { id: 'history',    label: 'History',     panels: ['rides-table', 'training-blocks', 'phase-timeline'] },
        { id: 'profile',    label: 'Profile',     panels: ['coggan-ranking', 'phenotype', 'power-profile', 'posterior-summary'] },
        { id: 'event-prep', label: 'Event Prep',  panels: ['gap-analysis', 'opportunity-cost', 'pacing', 'glycogen-budget'] },
      ],
    },
  };

  /**
   * Get the user slug from URL param (?user=athlete|coach).
   * Sanitized: alphanumeric + dash/underscore, max 40 chars.
   */
  function getUser() {
    var params = new URLSearchParams(window.location.search);
    var user = (params.get('user') || 'athlete').replace(/[^a-zA-Z0-9_-]/g, '').substring(0, 40);
    return user || 'athlete';
  }

  function storageKey() {
    return 'wko5-layout-' + getUser();
  }

  /**
   * Load layout from localStorage. Falls back to preset.
   */
  function loadLayout() {
    try {
      var raw = localStorage.getItem(storageKey());
      if (raw) {
        var layout = JSON.parse(raw);
        if (layout.version === LAYOUT_VERSION) {
          return layout;
        }
        // Version mismatch — reset to default
        console.warn('[Layout] Version mismatch, resetting to default');
      }
    } catch (e) {
      console.warn('[Layout] Failed to load:', e);
    }
    // Return default preset
    var user = getUser();
    return JSON.parse(JSON.stringify(PRESETS[user] || PRESETS.athlete));
  }

  /**
   * Save layout to localStorage.
   */
  function saveLayout(layout) {
    try {
      localStorage.setItem(storageKey(), JSON.stringify(layout));
      return true;
    } catch (e) {
      console.error('[Layout] Failed to save:', e);
      return false;
    }
  }

  /**
   * Reset to default preset.
   */
  function resetLayout() {
    localStorage.removeItem(storageKey());
    return loadLayout();
  }

  // Export
  window.WKO5Layout = {
    PRESETS: PRESETS,
    LAYOUT_VERSION: LAYOUT_VERSION,
    getUser: getUser,
    loadLayout: loadLayout,
    saveLayout: saveLayout,
    resetLayout: resetLayout,
  };
})();
```

- [ ] **Step 2: Add script tag to index.html**

Add after panel-registry.js, before dashboard.js:
```html
<script defer src="js/layout-manager.js"></script>
```

- [ ] **Step 3: Verify page loads, test in console**

```javascript
WKO5Layout.loadLayout()  // should return athlete preset
WKO5Layout.getUser()     // should return "athlete"
```

- [ ] **Step 4: Commit**

```bash
git add frontend/js/layout-manager.js frontend/index.html
git commit -m "feat: layout manager — localStorage presets for athlete + coach"
```

---

## Task 3: Wrap existing panels in registry interface

**Files:**
- Modify: `frontend/js/charts/pmc.js`
- Modify: `frontend/js/charts/mmp.js`
- Modify: `frontend/js/charts/clinical.js`
- Modify: `frontend/js/charts/segment-profile.js`
- Modify: `frontend/js/charts/zones.js`

Each existing chart class already has `constructor(selector)`, `render(data)`, and `destroy()`. We add a factory function that wraps them for the registry.

- [ ] **Step 1: Add factory registration to each chart file**

At the bottom of each chart file, add the factory registration. Example for `pmc.js`:

```javascript
// At the very end of pmc.js, after the class definition:
if (window.WKO5Registry) {
  WKO5Registry.registerFactory('pmc', function (container, api) {
    var chart = new PMCChart(container);
    // Fetch and render
    api.getFitness().then(function (data) {
      if (data && data.pmc) chart.render(data.pmc);
    }).catch(function (err) {
      container.innerHTML = '<div class="panel-error">Unable to load PMC: ' + err.message + '</div>';
    });
    return {
      destroy: function () { chart.destroy(); },
      refresh: function () {
        api.getFitness().then(function (data) {
          if (data && data.pmc) chart.render(data.pmc);
        });
      },
    };
  });
}
```

Do the same pattern for: mmp.js, clinical.js, segment-profile.js, zones.js.

The key is: each factory takes `(container, api)`, creates the chart instance, fetches data, renders, and returns `{ destroy, refresh }`.

- [ ] **Step 2: Verify existing panels still work**

Open dashboard — all existing charts should render normally. The factory registrations are additive (only called when the registry is used).

- [ ] **Step 3: Commit**

```bash
git add frontend/js/charts/*.js
git commit -m "feat: wrap existing chart panels with registry factory interface"
```

---

## Task 4: Refactor dashboard.js — the critical migration

**Files:**
- Modify: `frontend/js/dashboard.js`

This is the HIGH RISK task. We replace the `loadTab` switch statement with registry-driven panel instantiation, while keeping all existing rendering logic working.

- [ ] **Step 1: Add registry-aware loadTab alongside existing**

Add a new function `loadTabFromLayout(tabConfig, api)` that:
1. Gets the tab's panel container
2. Clears it
3. For each panel ID in `tabConfig.panels`:
   - Creates a `<div class="chart-panel" data-chart="{id}">` with title and `.chart-content` div
   - Looks up the factory in `WKO5Registry`
   - If factory exists: calls `factory(contentDiv, api)` and stores the returned handle
   - If no factory: falls back to the existing inline render logic

- [ ] **Step 2: Replace the loadTab switch**

In the existing `loadTab` function, replace the switch statement:

```javascript
function loadTab(tabName, api, force) {
  if (!api) return;
  if (!force && _loaded[tabName]) return;
  _loaded[tabName] = true;

  // Clear fetch cache on tab switch
  if (window.WKO5Registry) WKO5Registry.clearFetchCache();

  // Try layout-driven loading first
  if (window.WKO5Layout) {
    var layout = WKO5Layout.loadLayout();
    var tabConfig = layout.tabs.find(function (t) { return t.id === tabName; });
    if (tabConfig) {
      loadTabFromLayout(tabConfig, api);
      return;
    }
  }

  // Fallback to original switch for tabs not in layout
  switch (tabName) {
    case 'today':      loadToday(api); break;
    case 'fitness':    loadFitness(api); break;
    case 'event-prep': loadEventPrep(api); break;
    case 'history':    loadHistory(api); break;
    case 'profile':    loadProfile(api); break;
  }
}
```

- [ ] **Step 3: Generate tab bar from layout**

In the `boot()` function, after initializing the API:
1. Load the layout via `WKO5Layout.loadLayout()`
2. Generate the tab bar dynamically from `layout.tabs` (replacing static HTML tabs)
3. Generate panel containers for the first tab

- [ ] **Step 4: Register inline render functions as factories**

For panels that are currently inline in dashboard.js (tsb-status, recent-rides, rides-table, etc.), register them as factories:

```javascript
// Example: tsb-status
WKO5Registry.registerFactory('tsb-status', function (container, api) {
  api.getFitness().then(function (fitness) {
    renderTSBStatus(container, fitness);
  });
  return {
    destroy: function () { container.innerHTML = ''; },
    refresh: function () {
      api.getFitness().then(function (fitness) {
        renderTSBStatus(container, fitness);
      });
    },
  };
});
```

Do this for all ~11 inline panels: tsb-status, recent-rides, clinical-alert, rolling-ftp, power-profile, demand-heatmap, pacing, gap-analysis, rides-table, training-blocks, phase-timeline, intensity-dist, coggan-ranking, phenotype, athlete-config, posterior-summary.

- [ ] **Step 5: Remove static panel divs from index.html**

Replace the static `<div class="chart-panel" data-chart="...">` elements with a single container per tab panel:

```html
<section class="tab-panel" data-panel="today" id="panel-today" role="tabpanel">
  <div class="panel-container"></div>
</section>
```

The layout manager will populate `.panel-container` dynamically.

- [ ] **Step 6: Verify ALL existing panels render correctly**

Open each tab in the browser. Verify:
- Today: TSB, recent rides, clinical alert
- Fitness: PMC, MMP, rolling FTP, power profile
- Event Prep: gap analysis, pacing, segment profile
- History: rides table, training blocks, phase timeline, intensity dist
- Profile: coggan ranking, phenotype, config, posteriors

This is the hard gate — do NOT proceed until all existing panels work.

- [ ] **Step 7: Commit**

```bash
git add frontend/js/dashboard.js frontend/index.html
git commit -m "feat: refactor dashboard.js — registry-driven dynamic panel loading"
```

---

## Task 5: New chart panels — Health tab

**Files:**
- Create: `frontend/js/charts/health-status.js`
- Create: `frontend/js/charts/if-floor.js`
- Create: `frontend/js/charts/panic-training.js`
- Create: `frontend/js/charts/if-distribution.js`

These panels power the new Health tab. They all consume `/clinical-flags` or `/if-distribution` endpoints.

- [ ] **Step 1: Create health-status.js**

Flag cards in a grid — the primary Health tab panel. Full-width at top. Fetches from `/clinical-flags`, renders each flag as a color-coded card.

- [ ] **Step 2: Create if-floor.js, panic-training.js**

Single flag card panels extracted from `/clinical-flags` response. Each filters for its specific flag type and renders a standalone card with severity color.

- [ ] **Step 3: Create if-distribution.js**

D3 histogram of IF values from `/if-distribution`. Red highlight on bins > 0.70. Floor/ceiling markers as vertical lines.

- [ ] **Step 4: Register all 4 factories**

Each file registers via `WKO5Registry.registerFactory(id, factory)`.

- [ ] **Step 5: Verify Health tab renders**

Open dashboard, switch to Health tab. All 5 panels should render (health-status, if-distribution, if-floor, panic-training, reds-screen).

- [ ] **Step 6: Commit**

```bash
git add frontend/js/charts/health-status.js frontend/js/charts/if-floor.js frontend/js/charts/panic-training.js frontend/js/charts/if-distribution.js frontend/index.html
git commit -m "feat: Health tab — clinical flags + IF distribution + IF floor + panic training panels"
```

---

## Task 6: New chart panels — Fitness + Event Prep

**Files:**
- Create: `frontend/js/charts/ftp-growth.js`
- Create: `frontend/js/charts/rolling-pd.js`
- Create: `frontend/js/charts/opportunity-cost.js`
- Create: `frontend/js/charts/glycogen-budget.js`

- [ ] **Step 1: Create ftp-growth.js**

D3 scatter + log curve from `/ftp-growth`. Shows current mFTP, growth rate, phase label, TTE as metric cards above the chart.

- [ ] **Step 2: Create rolling-pd.js**

D3 multi-line time series from `/rolling-pd-profile`. Default: mFTP only visible. Toggle legend for Pmax, FRC, TTE.

- [ ] **Step 3: Create opportunity-cost.js**

D3 horizontal bar chart from `/opportunity-cost/{route_id}`. Color gradient by impact level. Route dropdown (populated from `/routes`). Default route from athlete config.

- [ ] **Step 4: Create glycogen-budget.js**

Interactive form (ride_kj, duration, carbs, delay, daily target, weight) + D3 timeline chart from `POST /glycogen-budget`. Form submits on input change (debounced). Bonk zone shaded area. Feed event markers.

- [ ] **Step 5: Register all 4 factories**

- [ ] **Step 6: Verify new panels on Fitness + Event Prep tabs**

- [ ] **Step 7: Commit**

```bash
git add frontend/js/charts/ftp-growth.js frontend/js/charts/rolling-pd.js frontend/js/charts/opportunity-cost.js frontend/js/charts/glycogen-budget.js
git commit -m "feat: FTP growth, rolling PD, opportunity cost, glycogen budget panels"
```

---

## Task 7: Edit Mode

**Files:**
- Modify: `frontend/js/layout-manager.js`
- Modify: `frontend/css/styles.css`
- Modify: `frontend/index.html`

- [ ] **Step 1: Add edit mode toggle to header**

Add gear icon button in the header bar. Click adds `editing` class to `<body>`.

- [ ] **Step 2: Implement edit mode CSS**

When `body.editing`:
- Panels get a top bar overlay with drag handle + X button
- Tabs get drag handle + X button
- "+" buttons appear at end of tab bar and bottom of panel area
- "Done" and "Cancel" buttons replace gear icon

- [ ] **Step 3: Implement panel add/remove**

- X button removes panel from current tab's layout config
- "+" opens a modal with panel catalog (from `WKO5Registry.getCatalog()`)
- Clicking a panel in modal adds it to current tab

- [ ] **Step 4: Implement SortableJS drag reorder**

- Initialize `Sortable` on each `.panel-container` for vertical panel reorder
- Initialize `Sortable` on tab bar for horizontal tab reorder
- On drag end: update layout config

- [ ] **Step 5: Implement tab add/remove/rename**

- "+" at end of tab bar: prompt for name (max 20 chars, no duplicates)
- X on tab: confirm dialog → remove tab
- Double-click tab label: inline rename

- [ ] **Step 6: Implement Done/Cancel**

- **Done**: save layout to localStorage, exit edit mode, re-render tabs
- **Cancel**: restore pre-edit snapshot (stored on edit mode entry), exit without saving
- Toast notification: "Layout saved" or "Changes discarded"

- [ ] **Step 7: Handle empty tab state**

Empty tab shows: "This tab has no panels. Click + to add some."

- [ ] **Step 8: Verify edit mode end-to-end**

Test: add panel, remove panel, reorder panels, add tab, rename tab, remove tab, Done saves, Cancel discards. Reload page — layout persists.

- [ ] **Step 9: Commit**

```bash
git add frontend/js/layout-manager.js frontend/css/styles.css frontend/index.html
git commit -m "feat: edit mode — add/remove/reorder panels and tabs with SortableJS"
```

---

## Task 8: Error states + API helpers + polish

**Files:**
- Modify: `frontend/js/api.js`
- Modify: `frontend/css/styles.css`

- [ ] **Step 1: Add API helper methods for new endpoints**

Add to `WKO5API` class:
```javascript
getIFDistribution()         { return this._get('/if-distribution'); }
getFTPGrowth()              { return this._get('/ftp-growth'); }
getPerformanceTrend()       { return this._get('/performance-trend'); }
getOpportunityCost(routeId) { return this._get('/opportunity-cost/' + routeId); }
postGlycogenBudget(body)    { return this._post('/glycogen-budget', body); }
getRollingPDProfile()       { return this._get('/rolling-pd-profile'); }
getFreshBaseline()           { return this._get('/fresh-baseline'); }
getShortPowerConsistency()  { return this._get('/short-power-consistency'); }
```

- [ ] **Step 2: Add panel error/empty state CSS**

```css
.panel-error {
  border: 1px solid var(--danger);
  border-radius: 6px;
  padding: 16px;
  text-align: center;
  color: var(--danger);
}
.panel-error .retry-btn { /* ... */ }

.panel-empty {
  color: var(--text-secondary);
  text-align: center;
  padding: 24px;
}

.panel-ok {
  border-left: 4px solid var(--success);
  /* for clinical "all clear" state */
}
```

- [ ] **Step 3: Strip ?token= from URL after extraction**

In `api.js` `_resolveToken()`, add after saving to localStorage:
```javascript
if (window.history && window.history.replaceState) {
  var url = new URL(window.location);
  url.searchParams.delete('token');
  window.history.replaceState({}, '', url);
}
```

- [ ] **Step 4: Final verification**

Open dashboard with `?user=athlete` and `?user=coach`. Verify:
- Different tab ordering per preset
- All panels render
- Edit mode works
- Layout persists across reload
- Error states show when API is down

- [ ] **Step 5: Commit**

```bash
git add frontend/js/api.js frontend/css/styles.css
git commit -m "feat: API helpers + error states + token security hardening"
```
