/**
 * WKO5 Dashboard — Wiring Layer
 *
 * Initializes charts, fetches data per tab, renders helper cards,
 * and wires up MMP recency toggle + post-ride new-activity card.
 *
 * Now layout-driven: reads tab/panel config from WKO5Layout, generates
 * the tab bar + panel containers dynamically, and uses WKO5Registry
 * factories to instantiate panels. Falls back to the original hardcoded
 * loaders when layout or registry are unavailable.
 *
 * Loads AFTER app.js. Uses window.app global.
 */

(function () {
  'use strict';

  /* ================================================================
   *  Formatting helpers
   * ================================================================ */

  function fmtDuration(seconds) {
    if (seconds == null || isNaN(seconds)) return '--';
    var s = Math.round(Number(seconds));
    var h = Math.floor(s / 3600);
    var m = Math.floor((s % 3600) / 60);
    var sec = s % 60;
    return h + ':' + (m < 10 ? '0' : '') + m + ':' + (sec < 10 ? '0' : '') + sec;
  }

  function fmtDistance(meters) {
    if (meters == null || isNaN(meters)) return '--';
    return (Number(meters) / 1000).toFixed(1) + ' km';
  }

  function fmtPower(watts) {
    if (watts == null || isNaN(watts)) return '--';
    return Math.round(Number(watts)) + ' W';
  }

  function fmtNumber(val, decimals) {
    if (val == null || isNaN(val)) return '--';
    return Number(val).toFixed(decimals != null ? decimals : 0);
  }

  function fmtDate(iso) {
    if (!iso) return '--';
    try {
      var d = new Date(iso);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    } catch (_) { return iso; }
  }

  function fmtIF(val) {
    if (val == null || isNaN(val)) return '--';
    return Number(val).toFixed(2);
  }

  /* ================================================================
   *  TSB color / trend helpers
   * ================================================================ */

  function tsbColorClass(tsb) {
    if (tsb == null) return '';
    if (tsb > 15) return 'text-success';
    if (tsb > -10) return 'text-warning';
    return 'text-danger';
  }

  function tsbTrend(current, previous) {
    if (current == null || previous == null) return '';
    if (current > previous) return ' &#9650;';
    if (current < previous) return ' &#9660;';
    return ' &#9654;';
  }

  /* ================================================================
   *  DOM helpers
   * ================================================================ */

  function qs(sel) { return document.querySelector(sel); }

  function setLoading(chartAttr, on) {
    var panel = qs('[data-chart="' + chartAttr + '"]');
    if (!panel) return;
    if (on) panel.classList.add('loading');
    else panel.classList.remove('loading');
  }

  function showError(container, msg) {
    if (!container) return;
    container.innerHTML = '<div class="empty-state">' + escapeHtml(msg) + '</div>';
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /* ================================================================
   *  Render helpers — simple HTML cards
   * ================================================================ */

  function renderTSBStatus(container, fitness) {
    if (!container) return;
    var latest = null;
    var prev = null;

    if (Array.isArray(fitness)) {
      if (fitness.length > 0) latest = fitness[fitness.length - 1];
      if (fitness.length > 1) prev = fitness[fitness.length - 2];
    } else if (fitness && fitness.data && Array.isArray(fitness.data)) {
      var d = fitness.data;
      if (d.length > 0) latest = d[d.length - 1];
      if (d.length > 1) prev = d[d.length - 2];
    } else if (fitness && fitness.tsb != null) {
      latest = fitness;
    }

    if (!latest) {
      showError(container, 'No fitness data available');
      return;
    }

    var tsb = latest.tsb != null ? latest.tsb : latest.TSB;
    var ctl = latest.ctl != null ? latest.ctl : latest.CTL;
    var atl = latest.atl != null ? latest.atl : latest.ATL;
    var prevTsb = prev ? (prev.tsb != null ? prev.tsb : prev.TSB) : null;

    var colorClass = tsbColorClass(tsb);
    var trend = tsbTrend(tsb, prevTsb);

    container.innerHTML =
      '<div style="text-align:center;padding:16px 0;">' +
        '<div class="mono ' + colorClass + '" style="font-size:2.5rem;font-weight:700;">' +
          escapeHtml(fmtNumber(tsb, 1)) + trend +
        '</div>' +
        '<div style="margin-top:8px;color:var(--text-secondary);font-size:0.85rem;">Training Stress Balance</div>' +
        '<div style="margin-top:12px;display:flex;justify-content:center;gap:24px;font-size:0.85rem;">' +
          '<span>CTL <span class="mono">' + escapeHtml(fmtNumber(ctl, 1)) + '</span></span>' +
          '<span>ATL <span class="mono">' + escapeHtml(fmtNumber(atl, 1)) + '</span></span>' +
        '</div>' +
      '</div>';
  }

  /** Derive a human-readable name from activity fields */
  function activityName(a) {
    if (a.name) return a.name;
    if (a.title) return a.title;
    var sport = a.sub_sport && a.sub_sport !== 'generic' ? a.sub_sport : (a.sport || 'Ride');
    var date = fmtDate(a.start_time);
    return sport.charAt(0).toUpperCase() + sport.slice(1) + ' — ' + date;
  }

  function renderRecentRides(container, activities) {
    if (!container) return;
    if (!activities || !activities.length) {
      showError(container, 'No recent rides');
      return;
    }

    var rows = '';
    var list = activities.slice(0, 5);
    for (var i = 0; i < list.length; i++) {
      var a = list[i];
      rows +=
        '<tr>' +
          '<td>' + escapeHtml(fmtDate(a.start_time)) + '</td>' +
          '<td>' + escapeHtml(activityName(a)) + '</td>' +
          '<td class="numeric">' + escapeHtml(fmtDuration(a.total_elapsed_time || a.total_timer_time)) + '</td>' +
          '<td class="numeric">' + escapeHtml(fmtNumber(a.training_stress_score)) + '</td>' +
          '<td class="numeric">' + escapeHtml(fmtPower(a.normalized_power)) + '</td>' +
          '<td class="numeric">' + escapeHtml(fmtIF(a.intensity_factor)) + '</td>' +
        '</tr>';
    }

    container.innerHTML =
      '<table class="data-table">' +
        '<thead><tr>' +
          '<th>Date</th><th>Name</th><th>Duration</th><th>TSS</th><th>NP</th><th>IF</th>' +
        '</tr></thead>' +
        '<tbody>' + rows + '</tbody>' +
      '</table>';
  }

  function renderRollingFtp(container, data) {
    if (!container) return;
    if (!data) { showError(container, 'No FTP data'); return; }

    var ftp = data.current_ftp || data.ftp || data.value;
    container.innerHTML =
      '<div style="text-align:center;padding:16px 0;">' +
        '<div class="mono text-accent" style="font-size:2.5rem;font-weight:700;">' +
          escapeHtml(fmtNumber(ftp)) +
        '</div>' +
        '<div style="margin-top:8px;color:var(--text-secondary);font-size:0.85rem;">Rolling FTP (watts)</div>' +
      '</div>';
  }

  function renderPowerProfile(container, profileData) {
    if (!container) return;
    if (!profileData) { showError(container, 'No profile data'); return; }

    /* API: {profile: {watts: {5: 1104, 60: 427, ...}, wkg: {5: 14.16, ...}}, ranking: {...}} */
    var watts = (profileData.profile && profileData.profile.watts) || {};
    var wkg = (profileData.profile && profileData.profile.wkg) || {};
    var ranking = profileData.ranking || {};

    var durations = [
      { label: '5s', key: '5' },
      { label: '1min', key: '60' },
      { label: '5min', key: '300' },
      { label: '20min', key: '1200' },
      { label: '60min', key: '3600' }
    ];

    var html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:12px;padding:8px 0;">';
    for (var i = 0; i < durations.length; i++) {
      var d = durations[i];
      var w = watts[d.key];
      var wk = wkg[d.key];
      var cat = ranking[d.key] || '';
      html +=
        '<div style="text-align:center;">' +
          '<div class="mono" style="font-size:1.4rem;font-weight:600;">' + escapeHtml(wk != null ? fmtNumber(wk, 2) : '--') + '</div>' +
          '<div style="color:var(--text-secondary);font-size:0.75rem;">W/kg @ ' + escapeHtml(d.label) + '</div>' +
          '<div class="mono text-muted" style="font-size:0.75rem;">' + escapeHtml(fmtPower(w)) + '</div>' +
          (cat ? '<div style="font-size:0.7rem;margin-top:2px;" class="text-muted">' + escapeHtml(cat) + '</div>' : '') +
        '</div>';
    }
    html += '</div>';
    container.innerHTML = html;
  }

  var RIDES_PER_PAGE = 20;

  function renderRidesTable(container, activities) {
    if (!container) return;
    if (!activities || !activities.length) {
      showError(container, 'No ride history');
      return;
    }

    var sortKey = 'date';
    var sortDir = -1;
    var page = 0;
    var filterText = '';

    function getFiltered() {
      if (!filterText) return activities;
      var q = filterText.toLowerCase();
      return activities.filter(function (a) {
        var name = (a.name || a.title || '').toLowerCase();
        var date = fmtDate(a.date || a.start_time).toLowerCase();
        return name.indexOf(q) !== -1 || date.indexOf(q) !== -1;
      });
    }

    function buildTable() {
      var filtered = getFiltered();
      var sorted = filtered.slice().sort(function (a, b) {
        var va = a[sortKey], vb = b[sortKey];
        if (sortKey === 'date' || sortKey === 'start_time') {
          va = va ? new Date(va).getTime() : 0;
          vb = vb ? new Date(vb).getTime() : 0;
        }
        va = va || 0; vb = vb || 0;
        return sortDir * (va > vb ? 1 : va < vb ? -1 : 0);
      });

      var totalPages = Math.ceil(sorted.length / RIDES_PER_PAGE);
      if (page >= totalPages) page = Math.max(0, totalPages - 1);
      var start = page * RIDES_PER_PAGE;
      var pageItems = sorted.slice(start, start + RIDES_PER_PAGE);

      var rows = '';
      for (var i = 0; i < pageItems.length; i++) {
        var a = pageItems[i];
        var id = a.id || a.activity_id || i;
        rows +=
          '<tr data-ride-id="' + escapeHtml(String(id)) + '" style="cursor:pointer;">' +
            '<td>' + escapeHtml(fmtDate(a.start_time)) + '</td>' +
            '<td>' + escapeHtml(activityName(a)) + '</td>' +
            '<td class="numeric">' + escapeHtml(fmtDuration(a.total_elapsed_time || a.total_timer_time)) + '</td>' +
            '<td class="numeric">' + escapeHtml(fmtDistance(a.total_distance)) + '</td>' +
            '<td class="numeric">' + escapeHtml(fmtNumber(a.training_stress_score)) + '</td>' +
            '<td class="numeric">' + escapeHtml(fmtPower(a.normalized_power)) + '</td>' +
            '<td class="numeric">' + escapeHtml(fmtIF(a.intensity_factor)) + '</td>' +
          '</tr>';
      }

      var cols = [
        { key: 'date', label: 'Date' },
        { key: 'name', label: 'Name' },
        { key: 'duration', label: 'Duration' },
        { key: 'distance', label: 'Distance' },
        { key: 'tss', label: 'TSS' },
        { key: 'np', label: 'NP' },
        { key: 'intensity_factor', label: 'IF' }
      ];

      var thead = '<tr>';
      for (var c = 0; c < cols.length; c++) {
        var arrow = cols[c].key === sortKey ? (sortDir === 1 ? ' &#9650;' : ' &#9660;') : '';
        thead += '<th data-sort="' + cols[c].key + '" style="cursor:pointer;">' + cols[c].label + arrow + '</th>';
      }
      thead += '</tr>';

      /* Search + pagination controls */
      var controls =
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;gap:8px;">' +
          '<input type="text" class="rides-search" placeholder="Search rides..." value="' + escapeHtml(filterText) + '" ' +
            'style="padding:4px 8px;background:var(--bg-primary);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;font-size:0.85rem;flex:1;max-width:250px;">' +
          '<span class="text-muted" style="font-size:0.8rem;">' + (start + 1) + '–' + Math.min(start + RIDES_PER_PAGE, sorted.length) + ' of ' + sorted.length + '</span>' +
          '<div style="display:flex;gap:4px;">' +
            '<button class="rides-prev" style="padding:2px 8px;background:var(--bg-secondary);color:var(--text-secondary);border:1px solid var(--border);border-radius:4px;cursor:pointer;"' + (page === 0 ? ' disabled' : '') + '>&laquo; Prev</button>' +
            '<button class="rides-next" style="padding:2px 8px;background:var(--bg-secondary);color:var(--text-secondary);border:1px solid var(--border);border-radius:4px;cursor:pointer;"' + (page >= totalPages - 1 ? ' disabled' : '') + '>Next &raquo;</button>' +
          '</div>' +
        '</div>';

      container.innerHTML = controls +
        '<table class="data-table rides-table">' +
          '<thead>' + thead + '</thead>' +
          '<tbody>' + rows + '</tbody>' +
        '</table>';

      /* Event handlers */
      var searchInput = container.querySelector('.rides-search');
      if (searchInput) {
        searchInput.addEventListener('input', function () {
          filterText = this.value;
          page = 0;
          buildTable();
        });
        /* Restore focus after rebuild */
        searchInput.focus();
        searchInput.setSelectionRange(filterText.length, filterText.length);
      }

      var prevBtn = container.querySelector('.rides-prev');
      if (prevBtn) prevBtn.addEventListener('click', function () { if (page > 0) { page--; buildTable(); } });
      var nextBtn = container.querySelector('.rides-next');
      if (nextBtn) nextBtn.addEventListener('click', function () { if (page < totalPages - 1) { page++; buildTable(); } });

      var ths = container.querySelectorAll('th[data-sort]');
      for (var t = 0; t < ths.length; t++) {
        ths[t].addEventListener('click', function () {
          var newKey = this.getAttribute('data-sort');
          if (newKey === sortKey) sortDir = -sortDir;
          else { sortKey = newKey; sortDir = -1; }
          page = 0;
          buildTable();
        });
      }

      var trs = container.querySelectorAll('tr[data-ride-id]');
      for (var r = 0; r < trs.length; r++) {
        trs[r].addEventListener('click', function () {
          var rideId = this.getAttribute('data-ride-id');
          window.app.emit('ride-selected', { id: rideId });
        });
      }
    }

    buildTable();
  }

  function renderTrainingBlocks(container, blocks) {
    if (!container) return;
    if (!blocks) { showError(container, 'No training block data'); return; }

    /* API returns a single block object, not an array */
    var b = Array.isArray(blocks) ? blocks[0] : blocks;
    if (!b) { showError(container, 'No training block data'); return; }

    var vol = b.volume || {};
    var intensity = b.intensity || {};
    var power = b.power || {};
    var tp = b.tp || {};

    var html =
      '<div style="padding:10px;border:1px solid var(--border);border-radius:6px;">' +
        '<div style="font-weight:600;margin-bottom:8px;">' + escapeHtml(fmtDate(b.start)) + ' — ' + escapeHtml(fmtDate(b.end)) + '</div>' +
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;">' +
          '<div><span class="text-muted">Rides</span> <span class="mono">' + escapeHtml(fmtNumber(vol.ride_count)) + '</span></div>' +
          '<div><span class="text-muted">Hours</span> <span class="mono">' + escapeHtml(fmtNumber(vol.hours, 1)) + '</span></div>' +
          '<div><span class="text-muted">Distance</span> <span class="mono">' + escapeHtml(fmtNumber(vol.km, 0)) + ' km</span></div>' +
          '<div><span class="text-muted">Elevation</span> <span class="mono">' + escapeHtml(fmtNumber(vol.elevation_m, 0)) + ' m</span></div>' +
          '<div><span class="text-muted">Weekly TSS</span> <span class="mono">' + escapeHtml(fmtNumber(power.weekly_tss, 0)) + '</span></div>' +
          '<div><span class="text-muted">Avg IF</span> <span class="mono">' + escapeHtml(fmtNumber(intensity.avg_if, 3)) + '</span></div>' +
          '<div><span class="text-muted">Z1/Z2/Z3</span> <span class="mono">' + escapeHtml(fmtNumber(intensity.seiler_zone1_pct, 0)) + '/' + escapeHtml(fmtNumber(intensity.seiler_zone2_pct, 0)) + '/' + escapeHtml(fmtNumber(intensity.seiler_zone3_pct, 0)) + '%</span></div>' +
          (tp.compliance_rate != null ? '<div><span class="text-muted">TP Compliance</span> <span class="mono">' + escapeHtml(fmtNumber(tp.compliance_rate * 100, 0)) + '%</span></div>' : '') +
        '</div>' +
      '</div>';
    container.innerHTML = html;
  }

  function renderPhaseTimeline(container, phase) {
    if (!container) return;
    if (!phase) { showError(container, 'No phase data'); return; }

    var name = phase.phase || phase.name || phase.current_phase || '--';
    var confidence = phase.confidence;

    container.innerHTML =
      '<div style="text-align:center;padding:16px 0;">' +
        '<div style="font-size:1.2rem;font-weight:600;color:var(--accent);">' + escapeHtml(name) + '</div>' +
        '<div style="margin-top:8px;color:var(--text-secondary);font-size:0.85rem;">Current Phase</div>' +
        (confidence != null ? '<div class="mono" style="margin-top:4px;font-size:0.8rem;">Confidence: ' + escapeHtml(fmtNumber(confidence * 100, 0)) + '%</div>' : '') +
      '</div>';
  }

  function renderCogganRanking(container, profileData) {
    if (!container) return;
    if (!profileData) { showError(container, 'No profile data'); return; }

    /* API returns {profile: {watts, wkg}, ranking: {5: "Fair", ...}, strengths_limiters: {...}} */
    var ranking = profileData.ranking || {};
    var wkg = (profileData.profile && profileData.profile.wkg) || {};
    var durationLabels = { '5': '5s', '60': '1min', '300': '5min', '1200': '20min', '3600': '60min' };

    var html = '<div style="display:grid;gap:6px;font-size:0.85rem;">';
    for (var dur in ranking) {
      if (!ranking.hasOwnProperty(dur)) continue;
      var cat = ranking[dur];
      var label = durationLabels[dur] || dur + 's';
      var wkgVal = wkg[dur] ? fmtNumber(wkg[dur], 2) + ' W/kg' : '';
      var colorClass = cat === 'Exceptional' || cat === 'World Class' ? 'text-success' : cat === 'Good' || cat === 'Very Good' ? 'text-accent' : cat === 'Moderate' ? 'text-warning' : '';
      html +=
        '<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border);">' +
          '<span class="text-muted">' + escapeHtml(label) + '</span>' +
          '<span><span class="mono" style="margin-right:8px;">' + escapeHtml(wkgVal) + '</span><span class="' + colorClass + '">' + escapeHtml(cat) + '</span></span>' +
        '</div>';
    }
    html += '</div>';
    container.innerHTML = html;
  }

  function renderPhenotype(container, profileData) {
    if (!container) return;
    if (!profileData) { showError(container, 'No profile data'); return; }

    var sl = profileData.strengths_limiters || {};
    var strength = sl.strength || {};
    var limiter = sl.limiter || {};

    container.innerHTML =
      '<div style="padding:8px 0;">' +
        '<div style="display:flex;justify-content:space-around;gap:16px;">' +
          '<div style="text-align:center;">' +
            '<div class="text-success" style="font-size:1.1rem;font-weight:600;">Strength</div>' +
            '<div style="margin-top:4px;">' + escapeHtml(strength.label || '--') + '</div>' +
            '<div class="text-muted" style="font-size:0.8rem;">' + escapeHtml(strength.category || '') + '</div>' +
          '</div>' +
          '<div style="text-align:center;">' +
            '<div class="text-danger" style="font-size:1.1rem;font-weight:600;">Limiter</div>' +
            '<div style="margin-top:4px;">' + escapeHtml(limiter.label || '--') + '</div>' +
            '<div class="text-muted" style="font-size:0.8rem;">' + escapeHtml(limiter.category || '') + '</div>' +
          '</div>' +
        '</div>' +
      '</div>';
  }

  function renderAthleteConfig(container, config) {
    if (!container) return;
    if (!config) { showError(container, 'No config data'); return; }

    var groups = [
      { label: 'Physical', keys: ['weight_kg', 'max_hr', 'lthr', 'ftp_manual', 'sex'] },
      { label: 'Equipment', keys: ['bike_weight_kg', 'cda', 'crr'] },
      { label: 'PMC', keys: ['ctl_time_constant', 'atl_time_constant'] },
      { label: 'Ultra/Pacing', keys: ['intensity_ceiling_if', 'fueling_rate_g_hr', 'energy_deficit_alert_kcal'] },
      { label: 'Clinical', keys: ['spike_threshold_watts', 'ctl_ramp_rate_yellow', 'ctl_ramp_rate_red', 'tsb_floor_alert'] }
    ];

    var labels = {
      weight_kg: 'Weight', max_hr: 'Max HR', lthr: 'LTHR', ftp_manual: 'FTP', sex: 'Sex',
      bike_weight_kg: 'Bike Weight', cda: 'CdA', crr: 'Crr',
      ctl_time_constant: 'CTL τ (days)', atl_time_constant: 'ATL τ (days)',
      intensity_ceiling_if: 'IF Ceiling', fueling_rate_g_hr: 'Fueling (g/hr)', energy_deficit_alert_kcal: 'Energy Alert (kcal)',
      spike_threshold_watts: 'Spike Threshold', ctl_ramp_rate_yellow: 'Ramp Rate ⚠', ctl_ramp_rate_red: 'Ramp Rate 🔴', tsb_floor_alert: 'TSB Floor Alert'
    };

    var units = { weight_kg: 'kg', max_hr: 'bpm', lthr: 'bpm', ftp_manual: 'W', bike_weight_kg: 'kg', spike_threshold_watts: 'W' };

    var html = '<div style="font-size:0.85rem;">';
    for (var g = 0; g < groups.length; g++) {
      var group = groups[g];
      html += '<div style="color:var(--accent);font-weight:600;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;margin:12px 0 6px 0;">' + escapeHtml(group.label) + '</div>';
      for (var i = 0; i < group.keys.length; i++) {
        var k = group.keys[i];
        var v = config[k];
        if (v == null) continue;
        var unit = units[k] ? ' ' + units[k] : '';
        html +=
          '<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border);">' +
            '<span style="color:var(--text-secondary);">' + escapeHtml(labels[k] || k) + '</span>' +
            '<span class="mono">' + escapeHtml(String(v)) + escapeHtml(unit) + '</span>' +
          '</div>';
      }
    }
    html += '</div>';
    container.innerHTML = html;
  }

  function renderPosteriorSummary(container, data) {
    if (!container) return;
    if (!data) { showError(container, 'No posterior data'); return; }

    var keys = Object.keys(data);
    var html = '<div style="font-size:0.85rem;">';
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      var v = data[k];
      if (v != null && typeof v !== 'object') {
        html +=
          '<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border);">' +
            '<span style="color:var(--text-secondary);">' + escapeHtml(k) + '</span>' +
            '<span class="mono">' + escapeHtml(typeof v === 'number' ? fmtNumber(v, 2) : String(v)) + '</span>' +
          '</div>';
      }
    }
    html += '</div>';
    container.innerHTML = html;
  }

  function renderNewActivityCard(container, ride, fitness) {
    if (!container) return;

    var tsb_before = null;
    var tsb_after = null;
    if (fitness) {
      var arr = Array.isArray(fitness) ? fitness : (fitness.data || []);
      if (arr.length >= 2) {
        tsb_before = arr[arr.length - 2].tsb != null ? arr[arr.length - 2].tsb : arr[arr.length - 2].TSB;
        tsb_after = arr[arr.length - 1].tsb != null ? arr[arr.length - 1].tsb : arr[arr.length - 1].TSB;
      }
    }

    var html =
      '<div class="new-activity-card" style="padding:8px 0;">' +
        '<div style="font-weight:600;font-size:1rem;">' + escapeHtml(ride.name || ride.title || 'New Ride') + '</div>' +
        '<div style="color:var(--text-secondary);font-size:0.8rem;margin-top:2px;">' + escapeHtml(fmtDate(ride.date || ride.start_time)) + '</div>' +
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px;">' +
          '<div><span class="text-muted" style="font-size:0.75rem;">Duration</span><div class="mono">' + escapeHtml(fmtDuration(ride.duration || ride.moving_time)) + '</div></div>' +
          '<div><span class="text-muted" style="font-size:0.75rem;">Distance</span><div class="mono">' + escapeHtml(fmtDistance(ride.distance)) + '</div></div>' +
          '<div><span class="text-muted" style="font-size:0.75rem;">NP</span><div class="mono">' + escapeHtml(fmtPower(ride.np || ride.normalized_power)) + '</div></div>' +
          '<div><span class="text-muted" style="font-size:0.75rem;">TSS</span><div class="mono">' + escapeHtml(fmtNumber(ride.tss)) + '</div></div>' +
          '<div><span class="text-muted" style="font-size:0.75rem;">IF</span><div class="mono">' + escapeHtml(fmtIF(ride.intensity_factor || ride.if_)) + '</div></div>' +
          '<div><span class="text-muted" style="font-size:0.75rem;">kJ</span><div class="mono">' + escapeHtml(fmtNumber(ride.kj || ride.work)) + '</div></div>' +
        '</div>';

    if (tsb_before != null && tsb_after != null) {
      html +=
        '<div style="margin-top:12px;font-size:0.85rem;">' +
          'TSB: <span class="mono ' + tsbColorClass(tsb_before) + '">' + escapeHtml(fmtNumber(tsb_before, 1)) + '</span>' +
          ' &#8594; <span class="mono ' + tsbColorClass(tsb_after) + '">' + escapeHtml(fmtNumber(tsb_after, 1)) + '</span>' +
        '</div>';
    }

    html +=
        '<button class="dismiss-new-activity" style="margin-top:12px;padding:6px 16px;border:1px solid var(--border);border-radius:4px;background:var(--bg-secondary);color:var(--text-primary);cursor:pointer;font-size:0.8rem;">Dismiss</button>' +
      '</div>';

    container.innerHTML = html;

    var btn = container.querySelector('.dismiss-new-activity');
    if (btn) {
      btn.addEventListener('click', function () {
        var panel = qs('[data-chart="new-activity"]');
        if (panel) panel.classList.add('hidden');
        try {
          localStorage.setItem('wko5_last_seen_activity', ride.date || ride.start_time || '');
        } catch (_) { /* */ }
      });
    }
  }

  /* ================================================================
   *  MMP Recency Toggle
   * ================================================================ */

  function initRecencyToggle(toggleContainer, onSelect) {
    if (!toggleContainer) return;

    toggleContainer.innerHTML =
      '<div class="recency-buttons" style="display:flex;gap:4px;margin-bottom:8px;">' +
        '<button data-days="30" class="recency-btn" style="padding:4px 10px;border:1px solid var(--border);border-radius:4px;background:var(--bg-secondary);color:var(--text-secondary);cursor:pointer;font-size:0.75rem;">30d</button>' +
        '<button data-days="60" class="recency-btn" style="padding:4px 10px;border:1px solid var(--border);border-radius:4px;background:var(--bg-secondary);color:var(--text-secondary);cursor:pointer;font-size:0.75rem;">60d</button>' +
        '<button data-days="90" class="recency-btn active" style="padding:4px 10px;border:1px solid var(--accent);border-radius:4px;background:var(--bg-secondary);color:var(--accent);cursor:pointer;font-size:0.75rem;font-weight:600;">90d</button>' +
        '<button data-days="365" class="recency-btn" style="padding:4px 10px;border:1px solid var(--border);border-radius:4px;background:var(--bg-secondary);color:var(--text-secondary);cursor:pointer;font-size:0.75rem;">1yr</button>' +
        '<button data-days="0" class="recency-btn" style="padding:4px 10px;border:1px solid var(--border);border-radius:4px;background:var(--bg-secondary);color:var(--text-secondary);cursor:pointer;font-size:0.75rem;">All</button>' +
      '</div>';

    toggleContainer.addEventListener('click', function (e) {
      var btn = e.target.closest('.recency-btn');
      if (!btn) return;

      var days = parseInt(btn.getAttribute('data-days'), 10);
      var all = toggleContainer.querySelectorAll('.recency-btn');
      for (var i = 0; i < all.length; i++) {
        all[i].classList.remove('active');
        all[i].style.borderColor = 'var(--border)';
        all[i].style.color = 'var(--text-secondary)';
        all[i].style.fontWeight = 'normal';
      }
      btn.classList.add('active');
      btn.style.borderColor = 'var(--accent)';
      btn.style.color = 'var(--accent)';
      btn.style.fontWeight = '600';

      if (onSelect) onSelect(days);
    });
  }

  /* ================================================================
   *  Register inline render functions as panel factories (Step 1)
   * ================================================================ */

  function registerInlineFactories() {
    if (!window.WKO5Registry) return;

    WKO5Registry.registerFactory('tsb-status', function (container, api) {
      api.getFitness().then(function (fitness) {
        renderTSBStatus(container, fitness);
      }).catch(function (err) {
        showError(container, 'TSB: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getFitness().then(function (fitness) {
            renderTSBStatus(container, fitness);
          }).catch(function (err) {
            showError(container, 'TSB: ' + err.message);
          });
        }
      };
    });

    WKO5Registry.registerFactory('recent-rides', function (container, api) {
      api.getActivities({ limit: 5 }).then(function (result) {
        var activities = result && result.activities ? result.activities : (Array.isArray(result) ? result.slice(0, 5) : null);
        renderRecentRides(container, activities);
      }).catch(function (err) {
        showError(container, 'Recent rides: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getActivities({ limit: 5 }).then(function (result) {
            var activities = result && result.activities ? result.activities : (Array.isArray(result) ? result.slice(0, 5) : null);
            renderRecentRides(container, activities);
          }).catch(function (err) {
            showError(container, 'Recent rides: ' + err.message);
          });
        }
      };
    });

    WKO5Registry.registerFactory('clinical-alert', function (container, api) {
      api.getClinicalFlags().then(function (flags) {
        if (flags && typeof ClinicalDashboard !== 'undefined') {
          try {
            var cd = new ClinicalDashboard(container);
            cd.render(flags);
          } catch (_) {
            container.innerHTML = '<div class="empty-state">' + (flags ? 'Clinical flags loaded' : 'No clinical flags') + '</div>';
          }
        } else {
          container.innerHTML = '<div class="empty-state">' + (flags === null ? 'Clinical flags unavailable' : 'No clinical flags') + '</div>';
        }
      }).catch(function (err) {
        showError(container, 'Clinical: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getClinicalFlags().then(function (flags) {
            if (flags && typeof ClinicalDashboard !== 'undefined') {
              try {
                var cd = new ClinicalDashboard(container);
                cd.render(flags);
              } catch (_) {
                container.innerHTML = '<div class="empty-state">Clinical flags loaded</div>';
              }
            } else {
              container.innerHTML = '<div class="empty-state">' + (flags === null ? 'Clinical flags unavailable' : 'No clinical flags') + '</div>';
            }
          }).catch(function (err) {
            showError(container, 'Clinical: ' + err.message);
          });
        }
      };
    });

    WKO5Registry.registerFactory('rolling-ftp', function (container, api) {
      api.getRollingFtp().then(function (data) {
        renderRollingFtp(container, data);
      }).catch(function (err) {
        showError(container, 'Rolling FTP: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getRollingFtp().then(function (data) {
            renderRollingFtp(container, data);
          }).catch(function (err) {
            showError(container, 'Rolling FTP: ' + err.message);
          });
        }
      };
    });

    WKO5Registry.registerFactory('power-profile', function (container, api) {
      api.getProfile().then(function (data) {
        renderPowerProfile(container, data);
      }).catch(function (err) {
        showError(container, 'Power profile: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getProfile().then(function (data) {
            renderPowerProfile(container, data);
          }).catch(function (err) {
            showError(container, 'Power profile: ' + err.message);
          });
        }
      };
    });

    WKO5Registry.registerFactory('rides-table', function (container, api) {
      api.getActivities({ limit: 200 }).then(function (result) {
        var activities = result && result.activities ? result.activities : (Array.isArray(result) ? result : null);
        renderRidesTable(container, activities);
      }).catch(function (err) {
        showError(container, 'Rides: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getActivities({ limit: 200 }).then(function (result) {
            var activities = result && result.activities ? result.activities : (Array.isArray(result) ? result : null);
            renderRidesTable(container, activities);
          }).catch(function (err) {
            showError(container, 'Rides: ' + err.message);
          });
        }
      };
    });

    WKO5Registry.registerFactory('training-blocks', function (container, api) {
      api.getTrainingBlocks().then(function (blocks) {
        renderTrainingBlocks(container, blocks);
      }).catch(function (err) {
        showError(container, 'Training blocks: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getTrainingBlocks().then(function (blocks) {
            renderTrainingBlocks(container, blocks);
          }).catch(function (err) {
            showError(container, 'Training blocks: ' + err.message);
          });
        }
      };
    });

    WKO5Registry.registerFactory('phase-timeline', function (container, api) {
      api.getDetectPhase().then(function (phase) {
        renderPhaseTimeline(container, phase);
      }).catch(function (err) {
        showError(container, 'Phase timeline: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getDetectPhase().then(function (phase) {
            renderPhaseTimeline(container, phase);
          }).catch(function (err) {
            showError(container, 'Phase timeline: ' + err.message);
          });
        }
      };
    });

    WKO5Registry.registerFactory('coggan-ranking', function (container, api) {
      api.getProfile().then(function (data) {
        renderCogganRanking(container, data);
      }).catch(function (err) {
        showError(container, 'Coggan ranking: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getProfile().then(function (data) {
            renderCogganRanking(container, data);
          }).catch(function (err) {
            showError(container, 'Coggan ranking: ' + err.message);
          });
        }
      };
    });

    WKO5Registry.registerFactory('phenotype', function (container, api) {
      api.getProfile().then(function (data) {
        renderPhenotype(container, data);
      }).catch(function (err) {
        showError(container, 'Phenotype: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getProfile().then(function (data) {
            renderPhenotype(container, data);
          }).catch(function (err) {
            showError(container, 'Phenotype: ' + err.message);
          });
        }
      };
    });

    WKO5Registry.registerFactory('athlete-config', function (container, api) {
      api.getConfig().then(function (config) {
        renderAthleteConfig(container, config);
      }).catch(function (err) {
        showError(container, 'Config: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getConfig().then(function (config) {
            renderAthleteConfig(container, config);
          }).catch(function (err) {
            showError(container, 'Config: ' + err.message);
          });
        }
      };
    });

    WKO5Registry.registerFactory('posterior-summary', function (container, api) {
      api.getPosteriorSummary().then(function (data) {
        renderPosteriorSummary(container, data);
      }).catch(function (err) {
        showError(container, 'Posterior summary: ' + err.message);
      });
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () {
          api.getPosteriorSummary().then(function (data) {
            renderPosteriorSummary(container, data);
          }).catch(function (err) {
            showError(container, 'Posterior summary: ' + err.message);
          });
        }
      };
    });

    // Event-prep route-dependent placeholders
    WKO5Registry.registerFactory('demand-heatmap', function (container) {
      container.innerHTML = '<div class="empty-state">Select a route from the Event Prep tab</div>';
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () { /* no-op: route-dependent */ }
      };
    });

    WKO5Registry.registerFactory('pacing', function (container) {
      container.innerHTML = '<div class="empty-state">Select a route from the Event Prep tab</div>';
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () { /* no-op: route-dependent */ }
      };
    });

    WKO5Registry.registerFactory('gap-analysis', function (container) {
      container.innerHTML = '<div class="empty-state">Select a route from the Event Prep tab</div>';
      return {
        destroy: function () { container.innerHTML = ''; },
        refresh: function () { /* no-op: route-dependent */ }
      };
    });
  }

  /* ================================================================
   *  Layout-driven panel loading (Step 2)
   * ================================================================ */

  /** Active panel handles keyed by tab ID -> array of {destroy, refresh} */
  var _panelHandles = {};

  /**
   * Load a single tab's panels using layout config + registry factories.
   * @param {Object} tabConfig - {id, label, panels: [panelId, ...]}
   * @param {Object} api - WKO5API instance
   */
  function loadTabFromLayout(tabConfig, api) {
    var tabId = tabConfig.id;

    // Get or create the tab panel section
    var section = document.getElementById('panel-' + tabId);
    if (!section) return;

    // Get or create a .panel-container div inside the section
    var panelContainer = section.querySelector('.panel-container');
    if (!panelContainer) {
      panelContainer = document.createElement('div');
      panelContainer.className = 'panel-container';
      section.appendChild(panelContainer);
    }

    // Destroy any previously created panel handles for this tab
    if (_panelHandles[tabId]) {
      _panelHandles[tabId].forEach(function (handle) {
        if (handle && typeof handle.destroy === 'function') {
          try { handle.destroy(); } catch (_) { /* */ }
        }
      });
    }
    _panelHandles[tabId] = [];
    panelContainer.innerHTML = '';

    // Special case: event-prep tab with route selector
    // The event-prep tab uses a unified route-selector UX that doesn't
    // decompose into individual panels. Keep the legacy loader.
    if (tabId === 'event-prep') {
      var epPanel = document.createElement('div');
      epPanel.className = 'chart-panel wide';
      epPanel.setAttribute('data-chart', 'event-prep-unified');
      epPanel.innerHTML = '<h3>Event Prep</h3><div class="chart-content"></div>';
      panelContainer.appendChild(epPanel);
      loadEventPrep(api);
      return;
    }

    // Empty tab state
    if (!tabConfig.panels || tabConfig.panels.length === 0) {
      panelContainer.innerHTML = '<div class="empty-state" style="grid-column:1/-1;padding:40px 0;">This tab has no panels. Click + to add some.</div>';
      return;
    }

    // For each panel ID in the layout config, create DOM + instantiate factory
    for (var i = 0; i < tabConfig.panels.length; i++) {
      var panelId = tabConfig.panels[i];
      var meta = window.WKO5Registry ? WKO5Registry.getPanel(panelId) : null;
      var label = meta ? meta.label : panelId;

      // Create panel wrapper DOM
      var panelDiv = document.createElement('div');
      panelDiv.className = 'chart-panel';
      panelDiv.setAttribute('data-chart', panelId);

      var heading = document.createElement('h3');
      heading.textContent = label;
      panelDiv.appendChild(heading);

      // MMP gets a special recency-toggle div
      if (panelId === 'mmp') {
        var toggleDiv = document.createElement('div');
        toggleDiv.className = 'recency-toggle';
        panelDiv.appendChild(toggleDiv);
      }

      var contentDiv = document.createElement('div');
      contentDiv.className = 'chart-content';
      panelDiv.appendChild(contentDiv);

      panelContainer.appendChild(panelDiv);

      // Look up factory and instantiate
      var factory = meta ? meta.factory : null;
      if (factory) {
        try {
          var handle = factory(contentDiv, api);
          _panelHandles[tabId].push(handle);
        } catch (err) {
          console.warn('[Dashboard] Factory error for', panelId, err);
          contentDiv.innerHTML = '<div class="empty-state">Panel error: ' + escapeHtml(err.message) + '</div>';
        }
      } else {
        contentDiv.innerHTML = '<div class="empty-state">Panel not available</div>';
      }

      // Wire up MMP recency toggle after the panel is created
      if (panelId === 'mmp') {
        (function (td) {
          initRecencyToggle(td, function (days) {
            _mmpDays = days;
            if (!api) return;
            setLoading('mmp', true);
            api.getModel({ days: days || undefined }).then(function (model) {
              setLoading('mmp', false);
              if (window.app && window.app.charts.mmp && model) {
                window.app.charts.mmp.render(model);
              }
            }).catch(function (err) {
              setLoading('mmp', false);
              showError(qs('[data-chart="mmp"] .chart-content'), 'Failed to load model: ' + err.message);
            });
          });
        })(toggleDiv);
      }
    }
  }

  /* ================================================================
   *  Event Prep — route analysis helpers (preserved)
   * ================================================================ */

  function demandColor(dr) {
    if (dr > 1.0) return 'var(--danger)';
    if (dr > 0.95) return '#e05555';
    if (dr > 0.85) return 'var(--warning)';
    return 'var(--success)';
  }

  /** Render SVG route map with segments colored by demand ratio */
  function renderDemandMap(container, points, demandSegments) {
    if (!container || !points || points.length < 2) {
      if (container) container.innerHTML = '<div class="empty-state">No route track</div>';
      return;
    }
    var w = container.getBoundingClientRect().width || 600;
    var h = Math.min(300, w * 0.5);
    var lats = points.map(function (p) { return p.lat; });
    var lons = points.map(function (p) { return p.lon; });
    var pad = 0.01;
    var xScale = d3.scaleLinear().domain([d3.min(lons) - pad, d3.max(lons) + pad]).range([15, w - 15]);
    var yScale = d3.scaleLinear().domain([d3.min(lats) - pad, d3.max(lats) + pad]).range([h - 15, 15]);

    var svg = d3.select(container).html('').append('svg').attr('width', w).attr('height', h)
      .style('background', 'var(--bg-primary)').style('border-radius', '6px');

    /* If we have demand segments, color the track by segment */
    if (demandSegments && demandSegments.length) {
      for (var si = 0; si < demandSegments.length; si++) {
        var seg = demandSegments[si];
        var startKm = seg.start_km || 0;
        var endKm = seg.end_km || seg.start_km + (seg.distance || 0) / 1000;
        var segPoints = points.filter(function (p) { return p.km >= startKm && p.km <= endKm; });
        if (segPoints.length < 2) continue;
        var pathD = segPoints.map(function (p, i) {
          return (i === 0 ? 'M' : 'L') + xScale(p.lon).toFixed(1) + ',' + yScale(p.lat).toFixed(1);
        }).join(' ');
        svg.append('path').attr('d', pathD).attr('fill', 'none')
          .attr('stroke', demandColor(seg.demand_ratio || 0)).attr('stroke-width', 3)
          .attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round');
      }
    } else {
      /* No demand data — plain accent line */
      var pathData = points.map(function (p, i) {
        return (i === 0 ? 'M' : 'L') + xScale(p.lon).toFixed(1) + ',' + yScale(p.lat).toFixed(1);
      }).join(' ');
      svg.append('path').attr('d', pathData).attr('fill', 'none').attr('stroke', 'var(--accent)')
        .attr('stroke-width', 2.5).attr('stroke-linecap', 'round');
    }

    /* Start/end markers */
    var p0 = points[0], pN = points[points.length - 1];
    svg.append('circle').attr('cx', xScale(p0.lon)).attr('cy', yScale(p0.lat)).attr('r', 5).attr('fill', 'var(--success)');
    svg.append('circle').attr('cx', xScale(pN.lon)).attr('cy', yScale(pN.lat)).attr('r', 5).attr('fill', 'var(--danger)');

    /* Legend */
    var leg = svg.append('g').attr('transform', 'translate(15,' + (h - 12) + ')');
    var items = [['< 0.85', 'var(--success)'], ['0.85–0.95', 'var(--warning)'], ['> 0.95', 'var(--danger)']];
    items.forEach(function (item, i) {
      leg.append('rect').attr('x', i * 80).attr('y', -8).attr('width', 12).attr('height', 8).attr('fill', item[1]).attr('rx', 2);
      leg.append('text').attr('x', i * 80 + 16).attr('y', 0).text(item[0]).attr('fill', 'var(--text-muted)').attr('font-size', '9');
    });
  }

  /** Render elevation profile with demand-colored segments behind it */
  function renderDemandElevation(container, points, demandSegments) {
    if (!container || !points || points.length < 2) return;
    var hasElev = points.some(function (p) { return p.elevation != null; });
    if (!hasElev) { container.innerHTML = '<div class="empty-state">No elevation data</div>'; return; }

    var w = container.getBoundingClientRect().width || 600;
    var h = 180;
    var m = { top: 10, right: 10, bottom: 25, left: 45 };
    var iw = w - m.left - m.right, ih = h - m.top - m.bottom;

    var filtered = points.filter(function (p) { return p.elevation != null; });
    var xScale = d3.scaleLinear().domain([0, d3.max(filtered, function (p) { return p.km; }) || 1]).range([0, iw]);
    var yScale = d3.scaleLinear().domain([
      d3.min(filtered, function (p) { return p.elevation; }) - 20,
      d3.max(filtered, function (p) { return p.elevation; }) + 20
    ]).range([ih, 0]);

    d3.select(container).selectAll('svg').remove();
    var svg = d3.select(container).append('svg').attr('width', w).attr('height', h);
    var g = svg.append('g').attr('transform', 'translate(' + m.left + ',' + m.top + ')');

    /* Demand segment background rects */
    if (demandSegments) {
      for (var si = 0; si < demandSegments.length; si++) {
        var seg = demandSegments[si];
        var x1 = xScale(seg.start_km || 0);
        var x2 = xScale(seg.end_km || seg.start_km + (seg.distance || 0) / 1000);
        g.append('rect').attr('x', x1).attr('y', 0).attr('width', Math.max(1, x2 - x1)).attr('height', ih)
          .attr('fill', demandColor(seg.demand_ratio || 0)).attr('opacity', 0.12);
      }
    }

    /* Elevation area + line */
    var area = d3.area().x(function (p) { return xScale(p.km); }).y0(ih).y1(function (p) { return yScale(p.elevation); }).curve(d3.curveMonotoneX);
    var line = d3.line().x(function (p) { return xScale(p.km); }).y(function (p) { return yScale(p.elevation); }).curve(d3.curveMonotoneX);
    g.append('path').datum(filtered).attr('d', area).attr('fill', 'var(--text-muted)').attr('opacity', 0.08);
    g.append('path').datum(filtered).attr('d', line).attr('fill', 'none').attr('stroke', 'var(--text-secondary)').attr('stroke-width', 1.5);

    /* Axes */
    g.append('g').attr('transform', 'translate(0,' + ih + ')').call(d3.axisBottom(xScale).ticks(8).tickFormat(function (d) { return d + ' km'; }))
      .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
    g.append('g').call(d3.axisLeft(yScale).ticks(4).tickFormat(function (d) { return d + 'm'; }))
      .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
    g.selectAll('.domain, .tick line').attr('stroke', 'var(--chart-grid)');
  }

  /** Build the pacing / segment table */
  function renderSegmentTable(container, demandSegments, gap) {
    if (!container) return;
    if (!demandSegments || !demandSegments.length) {
      container.innerHTML = '<div class="empty-state">No segment data</div>';
      return;
    }

    /* Gap analysis summary */
    var summaryHtml = '';
    if (gap && !gap.error) {
      var feasible = gap.feasible !== false;
      var prob = gap.overall_probability != null ? fmtNumber(gap.overall_probability * 100, 0) + '%' : '';
      summaryHtml =
        '<div style="display:flex;gap:16px;align-items:center;margin-bottom:12px;padding:10px;border:1px solid var(--border);border-radius:6px;background:var(--bg-secondary);">' +
          '<div style="font-size:1.3rem;font-weight:700;" class="' + (feasible ? 'text-success' : 'text-danger') + '">' + (feasible ? 'FEASIBLE' : 'NOT FEASIBLE') + '</div>' +
          (prob ? '<div class="mono">' + prob + ' success probability</div>' : '') +
          (gap.bottleneck ? '<div class="text-warning">' + escapeHtml(gap.bottleneck) + '</div>' : '') +
        '</div>';
    }

    /* Segment table */
    var rows = '';
    for (var i = 0; i < demandSegments.length; i++) {
      var s = demandSegments[i];
      var dr = s.demand_ratio || 0;
      var drColor = dr > 1.0 ? 'text-danger' : dr > 0.95 ? 'text-danger' : dr > 0.85 ? 'text-warning' : 'text-success';
      rows +=
        '<tr>' +
          '<td>' + (i + 1) + '</td>' +
          '<td>' + escapeHtml(s.type || '--') + '</td>' +
          '<td class="numeric">' + fmtNumber(s.start_km, 1) + ' – ' + fmtNumber(s.end_km || (s.start_km + (s.distance || 0) / 1000), 1) + '</td>' +
          '<td class="numeric">' + fmtNumber(s.avg_grade, 1) + '%</td>' +
          '<td class="numeric">' + fmtNumber(s.elevation_gain, 0) + 'm</td>' +
          '<td class="numeric">' + fmtPower(s.power_required) + '</td>' +
          '<td class="numeric ' + drColor + '">' + fmtNumber(dr, 2) + '</td>' +
        '</tr>';
    }

    container.innerHTML = summaryHtml +
      '<table class="data-table" style="font-size:0.8rem;">' +
        '<thead><tr>' +
          '<th>#</th><th>Type</th><th>km</th><th>Grade</th><th>Gain</th><th>Power Req</th><th>Demand</th>' +
        '</tr></thead>' +
        '<tbody>' + rows + '</tbody>' +
      '</table>';
  }

  async function loadRouteAnalysis(api, routeId, body) {
    if (!body) return;
    body.innerHTML = '<div class="empty-state">Loading route analysis...</div>';

    try {
      var results = await Promise.allSettled([
        api.getRoute(routeId),
        api.getDemand(routeId),
        api.getGapAnalysis(routeId)
      ]);

      var routeDetail = results[0].status === 'fulfilled' ? results[0].value : null;
      var demand = results[1].status === 'fulfilled' ? results[1].value : null;
      var gap = results[2].status === 'fulfilled' ? results[2].value : null;
      var demandSegments = demand && demand.segments ? demand.segments : [];
      var points = routeDetail && routeDetail.points ? routeDetail.points : [];

      /* Route summary header */
      var routeName = (routeDetail && routeDetail.name) || 'Route';
      var totalKm = routeDetail && routeDetail.total_distance_m ? fmtNumber(routeDetail.total_distance_m / 1000, 1) + ' km' : '';
      var totalElev = routeDetail && routeDetail.total_elevation_m ? fmtNumber(routeDetail.total_elevation_m, 0) + 'm gain' : '';

      body.innerHTML =
        '<div style="margin-bottom:12px;font-size:0.9rem;">' +
          '<span style="font-weight:600;">' + escapeHtml(routeName) + '</span>' +
          (totalKm ? ' &mdash; <span class="mono">' + escapeHtml(totalKm) + '</span>' : '') +
          (totalElev ? ' &middot; <span class="mono">' + escapeHtml(totalElev) + '</span>' : '') +
        '</div>' +
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">' +
          '<div class="route-map-area" style="min-height:200px;"></div>' +
          '<div class="elev-area" style="min-height:200px;"></div>' +
        '</div>' +
        '<div class="segment-table-area" style="margin-top:12px;"></div>';

      renderDemandMap(body.querySelector('.route-map-area'), points, demandSegments);
      renderDemandElevation(body.querySelector('.elev-area'), points, demandSegments);
      renderSegmentTable(body.querySelector('.segment-table-area'), demandSegments, gap);

    } catch (err) {
      body.innerHTML = '<div class="empty-state">Analysis failed: ' + escapeHtml(err.message) + '</div>';
    }
  }

  /* ================================================================
   *  Tab data loaders (legacy fallbacks)
   * ================================================================ */

  var _loaded = {};
  var _mmpDays = 90;

  async function loadToday(api) {
    var panels = ['tsb-status', 'recent-rides', 'clinical-flags', 'new-activity'];
    panels.forEach(function (p) { setLoading(p, true); });

    try {
      var results = await Promise.allSettled([
        api.getFitness(),
        api.getActivities({ limit: 5 }),
        api.getClinicalFlags()
      ]);

      var fitness = results[0].status === 'fulfilled' ? results[0].value : null;
      var actResult = results[1].status === 'fulfilled' ? results[1].value : null;
      var flags = results[2].status === 'fulfilled' ? results[2].value : null;

      /* API returns {activities: [...], total, limit, offset} — already sorted desc */
      var activities = actResult && actResult.activities ? actResult.activities : (Array.isArray(actResult) ? actResult.slice(0, 5) : null);

      setLoading('tsb-status', false);
      renderTSBStatus(qs('[data-chart="tsb-status"] .chart-content'), fitness);

      setLoading('recent-rides', false);
      renderRecentRides(qs('[data-chart="recent-rides"] .chart-content'), activities);

      setLoading('clinical-flags', false);
      if (flags && window.app.charts.clinical) {
        window.app.charts.clinical.render(flags);
      } else {
        var cfContainer = qs('[data-chart="clinical-flags"] .chart-content');
        if (cfContainer) cfContainer.innerHTML = '<div class="empty-state">' + (flags === null ? 'Clinical flags unavailable' : 'No clinical flags') + '</div>';
      }

      // New activity detection
      setLoading('new-activity', false);
      if (activities && activities.length > 0) {
        var latest = activities[0];
        var latestDate = latest.date || latest.start_time || '';
        var lastSeen = '';
        try { lastSeen = localStorage.getItem('wko5_last_seen_activity') || ''; } catch (_) { /* */ }

        if (latestDate && latestDate !== lastSeen) {
          var panel = qs('[data-chart="new-activity"]');
          if (panel) panel.classList.remove('hidden');
          renderNewActivityCard(qs('[data-chart="new-activity"] .chart-content'), latest, fitness);
        }
      }
    } catch (err) {
      panels.forEach(function (p) { setLoading(p, false); });
      showError(qs('[data-chart="tsb-status"] .chart-content'), 'Failed to load: ' + err.message);
    }
  }

  async function loadFitness(api) {
    var panels = ['pmc', 'mmp', 'rolling-ftp', 'power-profile'];
    panels.forEach(function (p) { setLoading(p, true); });

    try {
      var results = await Promise.allSettled([
        api.getPmc(),
        api.getModel({ days: _mmpDays || undefined }),
        api.getRollingFtp(),
        api.getProfile()
      ]);

      var pmcData = results[0].status === 'fulfilled' ? results[0].value : null;
      var model = results[1].status === 'fulfilled' ? results[1].value : null;
      var ftp = results[2].status === 'fulfilled' ? results[2].value : null;
      var profile = results[3].status === 'fulfilled' ? results[3].value : null;

      setLoading('pmc', false);
      if (window.app.charts.pmc && pmcData && pmcData.length) {
        /* PMC chart expects {pmc: [...]} — wrap the array */
        window.app.charts.pmc.render({ pmc: pmcData });
      } else {
        var pmcContainer = qs('[data-chart="pmc"] .chart-content');
        if (pmcContainer) showError(pmcContainer, 'No PMC data');
      }

      setLoading('mmp', false);
      if (window.app.charts.mmp && model && model.mmp) {
        window.app.charts.mmp.render(model);
      } else if (model && model.error) {
        showError(qs('[data-chart="mmp"] .chart-content'), model.error);
      } else {
        showError(qs('[data-chart="mmp"] .chart-content'), 'No model data');
      }

      setLoading('rolling-ftp', false);
      renderRollingFtp(qs('[data-chart="rolling-ftp"] .chart-content'), ftp);

      setLoading('power-profile', false);
      renderPowerProfile(qs('[data-chart="power-profile"] .chart-content'), profile);
    } catch (err) {
      panels.forEach(function (p) { setLoading(p, false); });
      showError(qs('[data-chart="pmc"] .chart-content'), 'Failed to load: ' + err.message);
    }
  }

  async function loadEventPrep(api) {
    if (!api) return;
    var panel = qs('[data-chart="event-prep-unified"]');
    var container = panel ? panel.querySelector('.chart-content') : null;
    if (!container) return;

    try {
      var routes = await api.getRoutes();
      var routeList = (routes && routes.routes) || routes || [];

      if (!routeList.length) {
        container.innerHTML = '<div class="empty-state">No routes imported. Import a GPX file or sync from RWGPS first.</div>';
        return;
      }

      /* Route selector */
      var selectorHtml =
        '<div class="route-selector" style="margin-bottom:16px;display:flex;gap:8px;align-items:center;">' +
          '<label style="color:var(--text-secondary);font-size:0.85rem;font-weight:600;">Route:</label>' +
          '<select class="route-select" style="padding:6px 10px;background:var(--bg-primary);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;font-size:0.85rem;flex:1;max-width:400px;">' +
            '<option value="">-- Select a route --</option>';
      for (var i = 0; i < routeList.length; i++) {
        var r = routeList[i];
        var rName = r.name || r.route_name || ('Route ' + (r.id || r.route_id));
        var dist = r.total_distance_m ? ' (' + fmtNumber(r.total_distance_m / 1000, 0) + ' km)' : '';
        var rId = r.id || r.route_id;
        selectorHtml += '<option value="' + escapeHtml(String(rId)) + '">' + escapeHtml(rName + dist) + '</option>';
      }
      selectorHtml += '</select></div><div class="event-prep-body"><div class="empty-state">Select a route to analyze</div></div>';
      container.innerHTML = selectorHtml;

      container.querySelector('.route-select').addEventListener('change', function () {
        var routeId = this.value;
        if (routeId) loadRouteAnalysis(api, routeId, container.querySelector('.event-prep-body'));
      });
    } catch (err) {
      container.innerHTML = '<div class="empty-state">Could not load routes: ' + escapeHtml(err.message) + '</div>';
    }
  }

  async function loadHistory(api) {
    var panels = ['rides-table', 'training-blocks', 'phase-timeline', 'intensity-dist'];
    panels.forEach(function (p) { setLoading(p, true); });

    try {
      var results = await Promise.allSettled([
        api.getActivities({ limit: 200 }),
        api.getTrainingBlocks(),
        api.getDetectPhase()
      ]);

      var actResult = results[0].status === 'fulfilled' ? results[0].value : null;
      var activities = actResult && actResult.activities ? actResult.activities : (Array.isArray(actResult) ? actResult : null);
      var blocks = results[1].status === 'fulfilled' ? results[1].value : null;
      var phase = results[2].status === 'fulfilled' ? results[2].value : null;

      setLoading('rides-table', false);
      renderRidesTable(qs('[data-chart="rides-table"] .chart-content'), activities);

      setLoading('training-blocks', false);
      renderTrainingBlocks(qs('[data-chart="training-blocks"] .chart-content'), blocks);

      setLoading('phase-timeline', false);
      renderPhaseTimeline(qs('[data-chart="phase-timeline"] .chart-content'), phase);

      setLoading('intensity-dist', false);
      // Intensity distribution placeholder
      var idContainer = qs('[data-chart="intensity-dist"] .chart-content');
      if (idContainer) idContainer.innerHTML = '<div class="empty-state">Intensity distribution coming soon</div>';
    } catch (err) {
      panels.forEach(function (p) { setLoading(p, false); });
      showError(qs('[data-chart="rides-table"] .chart-content'), 'Failed to load: ' + err.message);
    }
  }

  async function loadProfile(api) {
    var panels = ['coggan-ranking', 'phenotype', 'athlete-config', 'posterior-summary'];
    panels.forEach(function (p) { setLoading(p, true); });

    try {
      var results = await Promise.allSettled([
        api.getProfile(),
        api.getConfig(),
        api.getPosteriorSummary()
      ]);

      var profile = results[0].status === 'fulfilled' ? results[0].value : null;
      var config = results[1].status === 'fulfilled' ? results[1].value : null;
      var posterior = results[2].status === 'fulfilled' ? results[2].value : null;

      setLoading('coggan-ranking', false);
      renderCogganRanking(qs('[data-chart="coggan-ranking"] .chart-content'), profile);

      setLoading('phenotype', false);
      renderPhenotype(qs('[data-chart="phenotype"] .chart-content'), profile);

      setLoading('athlete-config', false);
      renderAthleteConfig(qs('[data-chart="athlete-config"] .chart-content'), config);

      setLoading('posterior-summary', false);
      renderPosteriorSummary(qs('[data-chart="posterior-summary"] .chart-content'), posterior);
    } catch (err) {
      panels.forEach(function (p) { setLoading(p, false); });
      showError(qs('[data-chart="coggan-ranking"] .chart-content'), 'Failed to load: ' + err.message);
    }
  }

  /* ================================================================
   *  Tab dispatch (Step 3)
   * ================================================================ */

  function loadTab(tabName, api, force) {
    if (!api) return;
    if (!force && _loaded[tabName]) return;
    _loaded[tabName] = true;

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
      case 'today':     loadToday(api); break;
      case 'fitness':   loadFitness(api); break;
      case 'event-prep': loadEventPrep(api); break;
      case 'history':   loadHistory(api); break;
      case 'profile':   loadProfile(api); break;
    }
  }

  /* ================================================================
   *  Disconnection overlay
   * ================================================================ */

  function showDisconnected(show) {
    var existing = qs('.disconnected-overlay');
    if (show && !existing) {
      var overlay = document.createElement('div');
      overlay.className = 'disconnected-overlay';
      overlay.style.cssText = 'position:fixed;top:var(--header-height,48px);left:0;right:0;bottom:var(--footer-height,28px);display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.5);z-index:50;';
      overlay.innerHTML = '<div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:24px;text-align:center;max-width:320px;">' +
        '<div style="font-size:1.1rem;font-weight:600;margin-bottom:8px;">Disconnected</div>' +
        '<div style="color:var(--text-secondary);font-size:0.85rem;">Waiting for API connection...</div>' +
      '</div>';
      document.body.appendChild(overlay);
    } else if (!show && existing) {
      existing.remove();
    }
  }

  /* ================================================================
   *  Dynamic tab bar + panel generation (Step 4)
   * ================================================================ */

  /**
   * Generate tab bar buttons and panel sections from layout config.
   * @param {Object} layout - from WKO5Layout.loadLayout()
   * @param {string} activeTab - the tab to mark as active
   */
  function generateTabsFromLayout(layout, activeTab) {
    var tabBar = qs('.tab-bar');
    var tabPanels = qs('.tab-panels');
    if (!tabBar || !tabPanels) return;

    tabBar.innerHTML = '';
    tabPanels.innerHTML = '';

    var firstTab = layout.tabs.length > 0 ? layout.tabs[0].id : 'today';
    if (!activeTab) activeTab = firstTab;

    for (var i = 0; i < layout.tabs.length; i++) {
      var tab = layout.tabs[i];
      var isActive = tab.id === activeTab;

      // Create tab button
      var btn = document.createElement('button');
      btn.className = 'tab' + (isActive ? ' active' : '');
      btn.setAttribute('role', 'tab');
      btn.setAttribute('data-tab', tab.id);
      btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
      btn.setAttribute('aria-controls', 'panel-' + tab.id);
      btn.textContent = tab.label;
      tabBar.appendChild(btn);

      // Create tab panel section
      var section = document.createElement('section');
      section.className = 'tab-panel' + (isActive ? ' active' : '');
      section.setAttribute('data-panel', tab.id);
      section.id = 'panel-' + tab.id;
      section.setAttribute('role', 'tabpanel');
      if (!isActive) section.style.display = 'none';
      tabPanels.appendChild(section);
    }
  }

  /* ================================================================
   *  Edit Mode — drag/drop, add/remove panels
   * ================================================================ */

  var _sortableInstances = [];

  function initEditMode() {
    // Add X buttons to each panel
    var panels = document.querySelectorAll('.chart-panel');
    panels.forEach(function (panel) {
      var removeBtn = document.createElement('button');
      removeBtn.className = 'panel-remove-btn';
      removeBtn.innerHTML = '&times;';
      removeBtn.style.cssText = 'position:absolute;top:4px;right:4px;width:24px;height:24px;border-radius:50%;border:1px solid var(--border);background:var(--bg-secondary);color:var(--text-secondary);cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;z-index:5;';
      panel.style.position = 'relative';
      panel.appendChild(removeBtn);

      removeBtn.addEventListener('click', function () {
        var chartId = panel.getAttribute('data-chart');
        removePanel(chartId);
        panel.remove();
      });
    });

    // Add "+" button at bottom of panel container
    var activePanel = document.querySelector('.tab-panel.active .panel-container');
    if (activePanel) {
      var addBtn = document.createElement('button');
      addBtn.className = 'panel-add-btn';
      addBtn.innerHTML = '+ Add Panel';
      addBtn.style.cssText = 'width:100%;padding:16px;border:2px dashed var(--border);border-radius:8px;background:transparent;color:var(--text-muted);cursor:pointer;font-size:0.85rem;margin-top:8px;';
      addBtn.addEventListener('click', showAddPanelModal);
      activePanel.appendChild(addBtn);

      // Initialize SortableJS on panel container
      if (window.Sortable) {
        var sortable = Sortable.create(activePanel, {
          animation: 150,
          handle: 'h3',
          ghostClass: 'sortable-ghost',
          filter: '.panel-add-btn',
          onEnd: function () { syncPanelOrder(); }
        });
        _sortableInstances.push(sortable);
      }
    }
  }

  function cleanupEditMode() {
    // Remove edit UI elements
    document.querySelectorAll('.panel-remove-btn').forEach(function (btn) { btn.remove(); });
    document.querySelectorAll('.panel-add-btn').forEach(function (btn) { btn.remove(); });
    // Destroy sortable instances
    _sortableInstances.forEach(function (s) { s.destroy(); });
    _sortableInstances = [];
    // Remove modal if open
    var modal = document.querySelector('.add-panel-modal');
    if (modal) modal.remove();
  }

  function removePanel(panelId) {
    var layout = WKO5Layout.loadLayout();
    var activeTabId = window.app.activeTab;
    var tab = layout.tabs.find(function (t) { return t.id === activeTabId; });
    if (tab) {
      tab.panels = tab.panels.filter(function (p) { return p !== panelId; });
      WKO5Layout.saveLayout(layout);
    }
  }

  function syncPanelOrder() {
    var container = document.querySelector('.tab-panel.active .panel-container');
    if (!container) return;
    var panelIds = [];
    container.querySelectorAll('.chart-panel[data-chart]').forEach(function (el) {
      panelIds.push(el.getAttribute('data-chart'));
    });
    var layout = WKO5Layout.loadLayout();
    var activeTabId = window.app.activeTab;
    var tab = layout.tabs.find(function (t) { return t.id === activeTabId; });
    if (tab) {
      tab.panels = panelIds;
      WKO5Layout.saveLayout(layout);
    }
  }

  function addPanel(panelId) {
    var layout = WKO5Layout.loadLayout();
    var activeTabId = window.app.activeTab;
    var tab = layout.tabs.find(function (t) { return t.id === activeTabId; });
    if (tab) {
      if (tab.panels.indexOf(panelId) === -1) {
        tab.panels.push(panelId);
        WKO5Layout.saveLayout(layout);
      }
    }
    // Close modal and reload
    var modal = document.querySelector('.add-panel-modal');
    if (modal) modal.remove();
    // Re-render current tab panels
    _loaded[activeTabId] = false;
    loadTab(activeTabId, window.app.api, true);
    // Re-init edit mode UI
    setTimeout(initEditMode, 100);
  }

  function showAddPanelModal() {
    var existing = document.querySelector('.add-panel-modal');
    if (existing) { existing.remove(); return; }

    var catalog = WKO5Registry.getCatalog();
    var layout = WKO5Layout.loadLayout();
    var activeTabId = window.app.activeTab;
    var tab = layout.tabs.find(function (t) { return t.id === activeTabId; });
    var currentPanels = tab ? tab.panels : [];

    var modal = document.createElement('div');
    modal.className = 'add-panel-modal';
    modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);z-index:200;display:flex;align-items:center;justify-content:center;';

    var content = '<div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:20px;max-width:500px;width:90%;max-height:80vh;overflow-y:auto;">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><h3 style="margin:0;">Add Panel</h3><button class="modal-close" style="background:none;border:none;color:var(--text-secondary);cursor:pointer;font-size:1.2rem;">&times;</button></div>';

    catalog.forEach(function (cat) {
      content += '<div style="margin-bottom:12px;"><div style="color:var(--accent);font-size:0.75rem;font-weight:600;text-transform:uppercase;margin-bottom:6px;">' + cat.label + '</div>';
      cat.panels.forEach(function (p) {
        var alreadyAdded = currentPanels.indexOf(p.id) !== -1;
        content += '<div class="add-panel-item" data-panel-id="' + p.id + '" style="padding:8px;border:1px solid var(--border);border-radius:4px;margin-bottom:4px;cursor:' + (alreadyAdded ? 'default' : 'pointer') + ';opacity:' + (alreadyAdded ? '0.4' : '1') + ';">' +
          '<div style="font-weight:500;font-size:0.85rem;">' + p.label + '</div>' +
          '<div style="font-size:0.75rem;color:var(--text-muted);">' + p.description + '</div>' +
          (alreadyAdded ? '<div style="font-size:0.7rem;color:var(--text-muted);margin-top:2px;">Already added</div>' : '') +
        '</div>';
      });
      content += '</div>';
    });
    content += '</div>';
    modal.innerHTML = content;

    document.body.appendChild(modal);

    // Close handlers
    modal.querySelector('.modal-close').addEventListener('click', function () { modal.remove(); });
    modal.addEventListener('click', function (e) { if (e.target === modal) modal.remove(); });

    // Panel selection
    modal.querySelectorAll('.add-panel-item').forEach(function (item) {
      item.addEventListener('click', function () {
        var panelId = this.getAttribute('data-panel-id');
        if (currentPanels.indexOf(panelId) === -1) {
          addPanel(panelId);
        }
      });
    });
  }

  function showToast(message) {
    var toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;bottom:40px;left:50%;transform:translateX(-50%);padding:8px 20px;background:var(--bg-secondary);color:var(--text-primary);border:1px solid var(--border);border-radius:6px;font-size:0.85rem;z-index:300;opacity:0;transition:opacity 0.3s ease;';
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(function () { toast.style.opacity = '1'; });
    setTimeout(function () {
      toast.style.opacity = '0';
      setTimeout(function () { toast.remove(); }, 300);
    }, 2000);
  }

  function reloadCurrentTab() {
    var activeTabId = window.app.activeTab;
    _loaded[activeTabId] = false;
    loadTab(activeTabId, window.app.api, true);
  }

  function rebuildTabBar() {
    if (!window.WKO5Layout) return;
    var layout = WKO5Layout.loadLayout();
    var activeTab = window.app.activeTab;
    // Check if activeTab still exists in the new layout
    var tabExists = layout.tabs.some(function (t) { return t.id === activeTab; });
    if (!tabExists) activeTab = layout.tabs.length > 0 ? layout.tabs[0].id : 'today';
    generateTabsFromLayout(layout, activeTab);
    window.app._showTab(activeTab);
  }

  /* ================================================================
   *  Bootstrap
   * ================================================================ */

  function boot() {
    var app = window.app;
    if (!app) {
      console.error('[Dashboard] window.app not found — is app.js loaded?');
      return;
    }

    // Step 1: Register inline render functions as factories
    registerInlineFactories();

    // Step 4: Generate tab bar + panel sections from layout
    var restoredTab = null;
    try { restoredTab = localStorage.getItem('wko5_active_tab'); } catch (_) { /* */ }

    if (window.WKO5Layout) {
      var layout = WKO5Layout.loadLayout();
      var activeTab = restoredTab || (layout.tabs.length > 0 ? layout.tabs[0].id : 'today');
      generateTabsFromLayout(layout, activeTab);

      // Re-run _showTab on app so it sees the new DOM
      app._showTab(activeTab);
    }

    // ── Edit mode UI ────────────────────────────────────────────
    var header = document.querySelector('.app-header');
    if (header) {
      // Gear icon button
      var editBtn = document.createElement('button');
      editBtn.className = 'edit-mode-btn';
      editBtn.setAttribute('aria-label', 'Edit layout');
      editBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492ZM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0ZM9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319Z" fill="currentColor"/></svg>';
      editBtn.style.cssText = 'margin-left:auto;padding:6px;background:transparent;border:none;color:var(--text-secondary);cursor:pointer;display:flex;align-items:center;';
      header.appendChild(editBtn);

      // Done / Cancel / Reset controls
      var editControls = document.createElement('div');
      editControls.className = 'edit-controls hidden';
      editControls.style.cssText = 'margin-left:auto;display:flex;gap:6px;';
      editControls.innerHTML =
        '<button class="edit-done" style="padding:4px 12px;background:var(--success);color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:0.8rem;">Done</button>' +
        '<button class="edit-cancel" style="padding:4px 12px;background:var(--bg-secondary);color:var(--text-secondary);border:1px solid var(--border);border-radius:4px;cursor:pointer;font-size:0.8rem;">Cancel</button>' +
        '<button class="edit-reset" style="padding:4px 12px;background:transparent;color:var(--text-muted);border:1px solid var(--border);border-radius:4px;cursor:pointer;font-size:0.75rem;">Reset</button>';
      header.appendChild(editControls);

      // Click handlers
      editBtn.addEventListener('click', function () {
        WKO5Layout.enterEditMode();
        editBtn.classList.add('hidden');
        editControls.classList.remove('hidden');
        initEditMode();
      });

      editControls.querySelector('.edit-done').addEventListener('click', function () {
        WKO5Layout.exitEditMode(true);
        editControls.classList.add('hidden');
        editBtn.classList.remove('hidden');
        cleanupEditMode();
        reloadCurrentTab();
        showToast('Layout saved');
      });

      editControls.querySelector('.edit-cancel').addEventListener('click', function () {
        WKO5Layout.exitEditMode(false);
        editControls.classList.add('hidden');
        editBtn.classList.remove('hidden');
        cleanupEditMode();
        reloadCurrentTab();
        showToast('Changes discarded');
      });

      editControls.querySelector('.edit-reset').addEventListener('click', function () {
        if (confirm('Reset layout to default?')) {
          WKO5Layout.resetLayout();
          WKO5Layout.exitEditMode(false);
          editControls.classList.add('hidden');
          editBtn.classList.remove('hidden');
          cleanupEditMode();
          rebuildTabBar();
          reloadCurrentTab();
          showToast('Layout reset to default');
        }
      });
    }

    // Initialize D3 chart components (backward compatibility)
    // These create chart instances used by the factory wrappers in chart files
    var charts = {};
    try { charts.pmc = new PMCChart('[data-chart="pmc"] .chart-content'); } catch (_) { console.warn('[Dashboard] PMCChart not available'); }
    try { charts.mmp = new MMPChart('[data-chart="mmp"] .chart-content'); } catch (_) { console.warn('[Dashboard] MMPChart not available'); }
    try { charts.clinical = new ClinicalDashboard('[data-chart="clinical-flags"] .chart-content'); } catch (_) { console.warn('[Dashboard] ClinicalDashboard not available'); }
    try { charts.segmentProfile = new SegmentProfileChart('[data-chart="segment-profile"] .chart-content'); } catch (_) { console.warn('[Dashboard] SegmentProfileChart not available'); }

    // Register with app
    Object.keys(charts).forEach(function (name) {
      app.registerChart(name, charts[name]);
    });

    // Init MMP recency toggle (for legacy path; layout path sets this up in loadTabFromLayout)
    initRecencyToggle(qs('[data-chart="mmp"] .recency-toggle'), function (days) {
      _mmpDays = days;
      if (!app.api) return;
      setLoading('mmp', true);
      app.api.getModel({ days: days || undefined }).then(function (model) {
        setLoading('mmp', false);
        if (app.charts.mmp && model) {
          app.charts.mmp.render(model);
        }
      }).catch(function (err) {
        setLoading('mmp', false);
        showError(qs('[data-chart="mmp"] .chart-content'), 'Failed to load model: ' + err.message);
      });
    });

    // Listen for ride selection — show ride detail in a modal or expand panel
    app.on('ride-selected', function (e) {
      var rideId = e.detail && e.detail.id;
      if (!rideId || !app.api) return;

      /* Create or show ride detail overlay */
      var overlay = qs('.ride-detail-overlay');
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'ride-detail-overlay';
        overlay.style.cssText = 'position:fixed;top:var(--header-height,48px);left:0;right:0;bottom:var(--footer-height,28px);background:var(--bg-primary);z-index:80;overflow-y:auto;padding:16px;';
        overlay.innerHTML =
          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">' +
            '<h2 style="margin:0;color:var(--text-primary);">Ride Detail</h2>' +
            '<button class="ride-detail-close" style="padding:4px 12px;background:var(--bg-secondary);color:var(--text-secondary);border:1px solid var(--border);border-radius:4px;cursor:pointer;">Close</button>' +
          '</div>' +
          '<div class="ride-detail-summary" style="margin-bottom:16px;"></div>' +
          '<div class="ride-detail-chart" style="min-height:300px;"></div>' +
          '<div class="ride-detail-zones" style="margin-top:16px;min-height:80px;"></div>';
        document.body.appendChild(overlay);

        overlay.querySelector('.ride-detail-close').addEventListener('click', function () {
          overlay.style.display = 'none';
        });
      }

      overlay.style.display = 'block';
      var summaryEl = overlay.querySelector('.ride-detail-summary');
      var chartEl = overlay.querySelector('.ride-detail-chart');
      var zonesEl = overlay.querySelector('.ride-detail-zones');
      summaryEl.innerHTML = '<div class="empty-state">Loading...</div>';
      chartEl.innerHTML = '';
      zonesEl.innerHTML = '';

      app.api.getRide(rideId).then(function (data) {
        if (!data) { summaryEl.innerHTML = '<div class="empty-state">No data</div>'; return; }
        var s = data.summary || data;
        /* ride_summary() returns: date, duration_s, distance_km, avg_power, np, IF, TSS, kJ, avg_hr, max_hr, elevation_gain */
        summaryEl.innerHTML =
          '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;">' +
            '<div><div class="text-muted" style="font-size:0.75rem;">Date</div><div>' + escapeHtml(fmtDate(s.date || s.start_time)) + '</div></div>' +
            '<div><div class="text-muted" style="font-size:0.75rem;">Duration</div><div class="mono">' + escapeHtml(fmtDuration(s.duration_s || s.total_elapsed_time)) + '</div></div>' +
            '<div><div class="text-muted" style="font-size:0.75rem;">Distance</div><div class="mono">' + escapeHtml(s.distance_km != null ? fmtNumber(s.distance_km, 1) + ' km' : fmtDistance(s.total_distance)) + '</div></div>' +
            '<div><div class="text-muted" style="font-size:0.75rem;">Avg Power</div><div class="mono">' + escapeHtml(fmtPower(s.avg_power)) + '</div></div>' +
            '<div><div class="text-muted" style="font-size:0.75rem;">NP</div><div class="mono">' + escapeHtml(fmtPower(s.np || s.normalized_power)) + '</div></div>' +
            '<div><div class="text-muted" style="font-size:0.75rem;">TSS</div><div class="mono">' + escapeHtml(fmtNumber(s.TSS || s.training_stress_score)) + '</div></div>' +
            '<div><div class="text-muted" style="font-size:0.75rem;">IF</div><div class="mono">' + escapeHtml(fmtIF(s.IF || s.intensity_factor)) + '</div></div>' +
            '<div><div class="text-muted" style="font-size:0.75rem;">Avg HR</div><div class="mono">' + escapeHtml(fmtNumber(s.avg_hr || s.avg_heart_rate)) + '</div></div>' +
          '</div>';

        /* Render ride timeseries chart */
        if (typeof RideTimeseriesChart !== 'undefined' && data.records && data.records.length) {
          try {
            var rideChart = new RideTimeseriesChart(chartEl);
            rideChart.render(data);
          } catch (err) {
            chartEl.innerHTML = '<div class="empty-state">Chart error: ' + escapeHtml(err.message) + '</div>';
          }
        }
      }).catch(function (err) {
        summaryEl.innerHTML = '<div class="empty-state">Failed to load ride: ' + escapeHtml(err.message) + '</div>';
      });
    });

    // Listen for tab changes
    app.on('tab-changed', function (e) {
      var tab = e.detail && e.detail.tab;
      if (tab) loadTab(tab, app.api);
    });

    // Listen for reconnection — reload current tab
    app.on('status-changed', function (e) {
      var connected = e.detail && e.detail.connected;
      showDisconnected(!connected);
      if (connected) {
        _loaded[app.activeTab] = false;
        loadTab(app.activeTab, app.api);
      }
    });

    // Wait for cache warmup before loading tabs
    waitForWarmup(app);
  }

  /** Poll /warmup-status and show progress. Load tabs once warm. */
  function waitForWarmup(app) {
    if (!app.api) { loadTab(app.activeTab, app.api); return; }

    var statusEl = qs('.content');
    var warmupOverlay = document.createElement('div');
    warmupOverlay.className = 'warmup-overlay';
    warmupOverlay.style.cssText = 'position:fixed;top:var(--header-height,48px);left:0;right:0;bottom:var(--footer-height,28px);display:flex;align-items:center;justify-content:center;background:var(--bg-primary);z-index:60;';
    warmupOverlay.innerHTML =
      '<div style="text-align:center;max-width:400px;">' +
        '<div style="font-size:1.1rem;font-weight:600;color:var(--text-primary);margin-bottom:12px;">Warming up...</div>' +
        '<div class="warmup-details" style="font-size:0.8rem;color:var(--text-secondary);line-height:1.8;"></div>' +
      '</div>';
    document.body.appendChild(warmupOverlay);

    var detailsEl = warmupOverlay.querySelector('.warmup-details');

    function poll() {
      app.api.getWarmupStatus().then(function (status) {
        if (!status) { finish(); return; }

        /* Show progress */
        var lines = [];
        for (var k in status.results) {
          lines.push('<span class="text-success">\u2713</span> ' + escapeHtml(k) + ' <span class="text-muted">' + escapeHtml(status.results[k]) + '</span>');
        }
        for (var ek in status.errors) {
          lines.push('<span class="text-danger">\u2717</span> ' + escapeHtml(ek) + ' <span class="text-danger">' + escapeHtml(status.errors[ek]) + '</span>');
        }
        if (status.running) {
          lines.push('<span class="text-muted">computing...</span>');
        }
        detailsEl.innerHTML = lines.join('<br>');

        if (status.done) {
          finish();
        } else {
          setTimeout(poll, 1000);
        }
      }).catch(function () {
        /* API not ready yet */
        setTimeout(poll, 1000);
      });
    }

    function finish() {
      warmupOverlay.style.opacity = '0';
      warmupOverlay.style.transition = 'opacity 0.3s ease';
      setTimeout(function () {
        warmupOverlay.remove();
        loadTab(app.activeTab, app.api);
      }, 300);
    }

    poll();
  }

  // Boot after app.js has initialized
  if (window.app) {
    boot();
  } else {
    document.addEventListener('DOMContentLoaded', function () {
      // Small delay to ensure app.js DOMContentLoaded handler runs first
      setTimeout(boot, 0);
    });
  }
})();
