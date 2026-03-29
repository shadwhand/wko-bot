(function () {
  'use strict';
  if (!window.WKO5Registry) return;

  function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

  // API returns {flags: [{name, status, value, detail}, ...]}
  // status is "ok", "warning", "alert", "critical"
  var STATUS_COLORS = {
    ok: '#3fb950', warning: '#d29922', alert: '#f85149', critical: '#f85149',
    GREEN: '#3fb950', AMBER: '#d29922', RED: '#f85149'
  };

  function statusColor(s) { return STATUS_COLORS[s] || STATUS_COLORS[(s || '').toLowerCase()] || 'var(--text-muted)'; }
  function statusLabel(s) { return (s || '').toUpperCase(); }

  /* ── clinical-flags: detailed flag grid ────────────────────────────── */

  WKO5Registry.registerFactory('clinical-flags', function (container, api) {
    function render(data) {
      if (!data) { container.innerHTML = '<div class="panel-error">No clinical data</div>'; return; }
      var flags = data.flags || data.current_flags || [];

      // Check if any non-ok flags exist
      var hasIssues = flags.some(function (f) {
        var s = f.status || f.severity || 'ok';
        return s !== 'ok' && s !== 'GREEN';
      });

      if (!flags.length || !hasIssues) {
        container.innerHTML = '<div style="text-align:center;padding:24px;border-left:4px solid #3fb950;background:rgba(63,185,80,0.06);border-radius:6px;">' +
          '<div style="font-size:1.2rem;font-weight:600;color:#3fb950;">All Clear</div>' +
          '<div style="color:var(--text-secondary);margin-top:4px;font-size:0.85rem;">No clinical flags detected</div></div>';
        return;
      }

      var html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;">';
      for (var i = 0; i < flags.length; i++) {
        var f = flags[i];
        var s = f.status || f.severity || f.level || 'ok';
        if (s === 'ok' || s === 'GREEN') continue; // only show issues
        var color = statusColor(s);
        var name = f.name || f.type || 'Flag';
        var detail = f.detail || f.message || f.description || '';
        var value = f.value || '';

        html += '<div style="border-left:4px solid ' + color + ';background:var(--bg-secondary);border-radius:6px;padding:12px;">' +
          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">' +
            '<span style="font-weight:600;font-size:0.85rem;">' + escapeHtml(name) + '</span>' +
            '<span style="font-size:0.7rem;padding:2px 6px;border-radius:3px;background:' + color + ';color:#fff;">' + escapeHtml(statusLabel(s)) + '</span>' +
          '</div>' +
          (detail ? '<div style="color:var(--text-secondary);font-size:0.8rem;">' + escapeHtml(detail) + '</div>' : '') +
          (value && value !== '--' ? '<div class="mono" style="font-size:0.8rem;margin-top:4px;">' + escapeHtml(String(value)) + '</div>' : '') +
        '</div>';
      }
      html += '</div>';
      container.innerHTML = html;
    }

    api.getClinicalFlags().then(render).catch(function (err) {
      container.innerHTML = '<div class="panel-error">Failed to load: ' + escapeHtml(err.message) + '</div>';
    });

    return {
      destroy: function () { container.innerHTML = ''; },
      refresh: function (a) { (a || api).getClinicalFlags().then(render); }
    };
  });

  /* ── reds-screen: RED-S energy deficiency screening ────────────────── */

  WKO5Registry.registerFactory('reds-screen', function (container, api) {
    function render(data) {
      if (!data) { container.innerHTML = '<div class="panel-error">No data</div>'; return; }
      var flags = data.flags || data.current_flags || [];
      var redsFlag = null;
      for (var i = 0; i < flags.length; i++) {
        var n = (flags[i].name || '').toLowerCase();
        if (n.indexOf('red-s') !== -1 || n.indexOf('reds') !== -1 || n.indexOf('energy deficiency') !== -1 ||
            n.indexOf('within-day') !== -1 || n.indexOf('deficit') !== -1) {
          redsFlag = flags[i]; break;
        }
      }
      if (!redsFlag || redsFlag.status === 'ok') {
        container.innerHTML = '<div style="text-align:center;padding:20px;border-left:4px solid #3fb950;border-radius:6px;background:rgba(63,185,80,0.06);">' +
          '<div style="font-weight:600;color:#3fb950;">RED-S: Clear</div>' +
          '<div style="color:var(--text-secondary);font-size:0.8rem;margin-top:4px;">No energy deficiency indicators</div></div>';
        return;
      }
      var color = statusColor(redsFlag.status || redsFlag.severity);
      container.innerHTML = '<div style="padding:16px;border-left:4px solid ' + color + ';border-radius:6px;background:var(--bg-secondary);">' +
        '<div style="font-weight:600;color:' + color + ';">RED-S Warning</div>' +
        '<div style="color:var(--text-secondary);font-size:0.85rem;margin-top:6px;">' + escapeHtml(redsFlag.detail || redsFlag.message || 'Potential energy deficiency detected') + '</div></div>';
    }

    api.getClinicalFlags().then(render).catch(function (err) {
      container.innerHTML = '<div class="panel-error">' + escapeHtml(err.message) + '</div>';
    });

    return {
      destroy: function () { container.innerHTML = ''; },
      refresh: function (a) { (a || api).getClinicalFlags().then(render); }
    };
  });

  /* ── fresh-baseline: staleness check for key durations ─────────────── */

  WKO5Registry.registerFactory('fresh-baseline', function (container, api) {
    function render(data) {
      if (!data) { container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-secondary);">No baseline data</div>'; return; }

      // API returns {"60": {exists, value, date, staleness_days}, "300": {...}, ...}
      // OR {durations: [{seconds, label, stale, last_date, days_since}]}
      var durations;
      if (data.durations) {
        durations = data.durations;
      } else {
        // Convert object format
        var labels = { '60': '1min', '300': '5min', '1200': '20min', '3600': '60min' };
        durations = [];
        for (var sec in data) {
          if (!data.hasOwnProperty(sec) || isNaN(parseInt(sec))) continue;
          var d = data[sec];
          durations.push({
            seconds: parseInt(sec),
            label: labels[sec] || sec + 's',
            last_date: d.date ? d.date.split(' ')[0] : '--',
            days_since: d.staleness_days,
            stale: d.staleness_days != null && d.staleness_days > 30,
            value: d.value,
            exists: d.exists
          });
        }
        durations.sort(function (a, b) { return a.seconds - b.seconds; });
      }

      if (!durations.length) {
        container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-secondary);">No baseline data</div>';
        return;
      }

      var html = '<table class="data-table" style="font-size:0.8rem;"><thead><tr>' +
        '<th>Duration</th><th>Best (W)</th><th>Last Date</th><th>Status</th>' +
        '</tr></thead><tbody>';
      for (var i = 0; i < durations.length; i++) {
        var dur = durations[i];
        var statusColor2 = dur.stale ? '#f85149' : '#3fb950';
        var statusText = dur.stale ? 'STALE' : (dur.exists === false ? 'No data' : 'Fresh');
        html += '<tr>' +
          '<td>' + escapeHtml(dur.label || dur.seconds + 's') + '</td>' +
          '<td class="numeric">' + (dur.value != null ? Math.round(dur.value) : '--') + '</td>' +
          '<td>' + escapeHtml(dur.last_date || '--') + '</td>' +
          '<td style="color:' + statusColor2 + ';">' + statusText + '</td>' +
        '</tr>';
      }
      html += '</tbody></table>';
      container.innerHTML = html;
    }

    api.getFreshBaseline().then(render).catch(function (err) {
      container.innerHTML = '<div class="panel-error">' + escapeHtml(err.message) + '</div>';
    });

    return {
      destroy: function () { container.innerHTML = ''; },
      refresh: function (a) { (a || api).getFreshBaseline().then(render); }
    };
  });
})();
