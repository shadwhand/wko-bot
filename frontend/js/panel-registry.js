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
