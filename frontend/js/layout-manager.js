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

  /* ================================================================
   *  Edit mode state management
   * ================================================================ */

  /** Snapshot of layout before edits, used for cancel */
  var _snapshot = null;

  /**
   * Enter edit mode — snapshot the current layout for cancel support.
   */
  function enterEditMode() {
    _snapshot = JSON.parse(JSON.stringify(loadLayout()));
    document.body.classList.add('editing');
  }

  /**
   * Exit edit mode.
   * @param {boolean} save - true to keep changes, false to restore snapshot
   */
  function exitEditMode(save) {
    document.body.classList.remove('editing');
    if (save) {
      // Layout was already modified in place, just persist
      var layout = loadLayout();
      saveLayout(layout);
    } else {
      // Restore snapshot
      if (_snapshot) saveLayout(_snapshot);
    }
    _snapshot = null;
  }

  /**
   * Check if currently in edit mode.
   */
  function isEditing() {
    return document.body.classList.contains('editing');
  }

  // Export
  window.WKO5Layout = {
    PRESETS: PRESETS,
    LAYOUT_VERSION: LAYOUT_VERSION,
    getUser: getUser,
    loadLayout: loadLayout,
    saveLayout: saveLayout,
    resetLayout: resetLayout,
    enterEditMode: enterEditMode,
    exitEditMode: exitEditMode,
    isEditing: isEditing,
  };
})();
