(function () {
  'use strict';
  if (!window.WKO5Registry) return;

  function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

  WKO5Registry.registerFactory('if-floor', function (container, api) {
    function render(data) {
      if (!data) { container.innerHTML = '<div class="panel-error">No data</div>'; return; }
      var flags = data.flags || data.current_flags || [];
      var ifFlag = null;
      for (var i = 0; i < flags.length; i++) {
        if (flags[i].type === 'if_floor' || flags[i].type === 'intensity_floor' ||
            (flags[i].name || '').toLowerCase().indexOf('floor') !== -1) {
          ifFlag = flags[i]; break;
        }
      }

      if (!ifFlag || ifFlag.status === 'ok') {
        container.innerHTML = '<div style="text-align:center;padding:20px;border-left:4px solid #3fb950;border-radius:6px;background:rgba(63,185,80,0.06);">' +
          '<div style="font-weight:600;color:#3fb950;">IF Floor: OK</div>' +
          '<div style="color:var(--text-secondary);font-size:0.8rem;margin-top:4px;">Endurance rides are at appropriate intensity</div></div>';
        return;
      }

      var color = (ifFlag.status === 'alert' || ifFlag.status === 'critical' || ifFlag.severity === 'RED') ? '#f85149' : '#d29922';
      container.innerHTML = '<div style="padding:16px;border-left:4px solid ' + color + ';border-radius:6px;background:var(--bg-secondary);">' +
        '<div style="font-weight:600;color:' + color + ';">IF Floor Alert</div>' +
        '<div style="color:var(--text-secondary);font-size:0.85rem;margin-top:6px;">' + escapeHtml(ifFlag.detail || ifFlag.message || 'Endurance rides too intense') + '</div>' +
        (ifFlag.value && ifFlag.value !== '--' ? '<div class="mono" style="margin-top:6px;font-size:0.85rem;">Value: ' + escapeHtml(String(ifFlag.value)) + '</div>' : '') +
      '</div>';
    }

    api.getClinicalFlags().then(render).catch(function (err) {
      container.innerHTML = '<div class="panel-error">' + escapeHtml(err.message) + '</div>';
    });

    return {
      destroy: function () { container.innerHTML = ''; },
      refresh: function (a) { (a || api).getClinicalFlags().then(render); }
    };
  });
})();
