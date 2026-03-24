(function () {
  'use strict';
  if (!window.WKO5Registry) return;

  function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

  WKO5Registry.registerFactory('panic-training', function (container, api) {
    function render(data) {
      if (!data) { container.innerHTML = '<div class="panel-error">No data</div>'; return; }
      var flags = data.flags || data.current_flags || [];
      var panicFlag = null;
      for (var i = 0; i < flags.length; i++) {
        if (flags[i].type === 'panic_training' ||
            (flags[i].name || '').toLowerCase().indexOf('panic') !== -1) {
          panicFlag = flags[i]; break;
        }
      }

      if (!panicFlag) {
        container.innerHTML = '<div style="text-align:center;padding:20px;border-left:4px solid #3fb950;border-radius:6px;background:rgba(63,185,80,0.06);">' +
          '<div style="font-weight:600;color:#3fb950;">No Panic Training</div>' +
          '<div style="color:var(--text-secondary);font-size:0.8rem;margin-top:4px;">Training load progression is smooth</div></div>';
        return;
      }

      var color = panicFlag.severity === 'RED' || panicFlag.severity === 'red' ? '#f85149' : '#d29922';
      container.innerHTML = '<div style="padding:16px;border-left:4px solid ' + color + ';border-radius:6px;background:var(--bg-secondary);">' +
        '<div style="font-weight:600;color:' + color + ';">Panic Training Detected</div>' +
        '<div style="color:var(--text-secondary);font-size:0.85rem;margin-top:6px;">' + escapeHtml(panicFlag.message || panicFlag.description || 'Sudden intensity spike after low-load period') + '</div>' +
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
