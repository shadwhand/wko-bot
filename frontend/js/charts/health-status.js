(function () {
  'use strict';
  if (!window.WKO5Registry) return;

  var COLORS = { RED: '#f85149', AMBER: '#d29922', GREEN: '#3fb950', red: '#f85149', amber: '#d29922', green: '#3fb950' };

  function severityColor(sev) {
    return COLORS[sev] || COLORS[(sev || '').toUpperCase()] || 'var(--text-muted)';
  }

  function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

  /* ── clinical-flags: detailed flag grid ────────────────────────────── */

  WKO5Registry.registerFactory('clinical-flags', function (container, api) {
    function render(data) {
      if (!data) { container.innerHTML = '<div class="panel-error">No clinical data</div>'; return; }
      var flags = data.flags || data.current_flags || [];
      var alertLevel = data.alert_level || 'GREEN';

      if (!flags.length || alertLevel === 'GREEN') {
        container.innerHTML = '<div style="text-align:center;padding:24px;border-left:4px solid #3fb950;background:rgba(63,185,80,0.06);border-radius:6px;">' +
          '<div style="font-size:1.2rem;font-weight:600;color:#3fb950;">All Clear</div>' +
          '<div style="color:var(--text-secondary);margin-top:4px;font-size:0.85rem;">No clinical flags detected</div></div>';
        return;
      }

      var html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;">';
      for (var i = 0; i < flags.length; i++) {
        var f = flags[i];
        var color = severityColor(f.severity || f.level || alertLevel);
        html += '<div style="border-left:4px solid ' + color + ';background:var(--bg-secondary);border-radius:6px;padding:12px;">' +
          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">' +
            '<span style="font-weight:600;font-size:0.85rem;">' + escapeHtml(f.type || f.name || 'Flag') + '</span>' +
            '<span style="font-size:0.7rem;padding:2px 6px;border-radius:3px;background:' + color + ';color:#fff;">' + escapeHtml((f.severity || f.level || '').toUpperCase()) + '</span>' +
          '</div>' +
          '<div style="color:var(--text-secondary);font-size:0.8rem;">' + escapeHtml(f.message || f.description || '') + '</div>' +
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
        if (flags[i].type === 'reds' || flags[i].type === 'red_s' ||
            (flags[i].name || '').toLowerCase().indexOf('red-s') !== -1 ||
            (flags[i].name || '').toLowerCase().indexOf('energy deficiency') !== -1) {
          redsFlag = flags[i]; break;
        }
      }
      if (!redsFlag) {
        container.innerHTML = '<div style="text-align:center;padding:20px;border-left:4px solid #3fb950;border-radius:6px;background:rgba(63,185,80,0.06);">' +
          '<div style="font-weight:600;color:#3fb950;">RED-S: Clear</div>' +
          '<div style="color:var(--text-secondary);font-size:0.8rem;margin-top:4px;">No energy deficiency indicators</div></div>';
        return;
      }
      var color = redsFlag.severity === 'RED' || redsFlag.severity === 'red' ? '#f85149' : '#d29922';
      container.innerHTML = '<div style="padding:16px;border-left:4px solid ' + color + ';border-radius:6px;background:var(--bg-secondary);">' +
        '<div style="font-weight:600;color:' + color + ';">RED-S Warning</div>' +
        '<div style="color:var(--text-secondary);font-size:0.85rem;margin-top:6px;">' + escapeHtml(redsFlag.message || 'Potential energy deficiency detected') + '</div></div>';
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
      if (!data || !data.durations) {
        container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-secondary);">No baseline data</div>';
        return;
      }
      var html = '<table class="data-table" style="font-size:0.8rem;"><thead><tr>' +
        '<th>Duration</th><th>Last Test</th><th>Days Ago</th><th>Status</th>' +
        '</tr></thead><tbody>';
      for (var i = 0; i < data.durations.length; i++) {
        var d = data.durations[i];
        var statusColor = d.stale ? '#f85149' : '#3fb950';
        var statusText = d.stale ? 'STALE' : 'Fresh';
        html += '<tr>' +
          '<td>' + escapeHtml(d.label || d.seconds + 's') + '</td>' +
          '<td>' + escapeHtml(d.last_date || '--') + '</td>' +
          '<td class="numeric">' + (d.days_since || '--') + '</td>' +
          '<td style="color:' + statusColor + ';">' + statusText + '</td>' +
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
