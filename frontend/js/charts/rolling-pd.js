(function () {
  'use strict';
  if (!window.WKO5Registry) return;

  WKO5Registry.registerFactory('rolling-pd', function (container, api) {
    function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

    var visible = { mFTP: true, Pmax: false, FRC: false, TTE: false };
    var colors = { mFTP: '#58a6ff', Pmax: '#f778ba', FRC: '#d29922', TTE: '#3fb950' };

    function render(data) {
      // API returns {data: [...]} or {snapshots: [...]} or just [...]
      var snapshots = data && (data.snapshots || data.data);
      if (Array.isArray(data)) snapshots = data;
      if (!snapshots || !snapshots.length) {
        container.innerHTML = '<div class="panel-error">No rolling PD data</div>'; return;
      }
      container.innerHTML = '';

      // Legend toggles
      var legendHtml = '<div style="display:flex;gap:8px;margin-bottom:8px;font-size:0.75rem;">';
      ['mFTP', 'Pmax', 'FRC', 'TTE'].forEach(function (key) {
        var active = visible[key];
        legendHtml += '<button class="pd-legend-btn" data-key="' + key + '" style="padding:3px 8px;border:1px solid ' + (active ? colors[key] : 'var(--border)') + ';border-radius:4px;background:' + (active ? colors[key] + '22' : 'transparent') + ';color:' + (active ? colors[key] : 'var(--text-muted)') + ';cursor:pointer;font-size:inherit;">' + key + '</button>';
      });
      legendHtml += '</div>';
      container.insertAdjacentHTML('beforeend', legendHtml);

      // Chart — use normalized snapshots
      var width = container.getBoundingClientRect().width || 500;
      var height = 200;
      var margin = { top: 10, right: 20, bottom: 30, left: 50 };
      var iw = width - margin.left - margin.right;
      var ih = height - margin.top - margin.bottom;

      var parseDate = function (s) { return new Date(s); };
      var dates = snapshots.map(function (s) { return parseDate(s.date); });
      var x = d3.scaleTime().domain(d3.extent(dates)).range([0, iw]);

      var svg = d3.select(container).append('svg').attr('width', width).attr('height', height);
      var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

      // Draw each visible series with its own y-scale
      var activeKeys = Object.keys(visible).filter(function (k) { return visible[k]; });
      if (activeKeys.length === 0) activeKeys = ['mFTP'];

      // Use the first active key for the y-axis
      var allVals = [];
      activeKeys.forEach(function (key) {
        snapshots.forEach(function (s) { if (s[key] != null) allVals.push(s[key]); });
      });
      var y = d3.scaleLinear().domain([d3.min(allVals) * 0.95, d3.max(allVals) * 1.05]).range([ih, 0]);

      activeKeys.forEach(function (key) {
        var lineData = snapshots.filter(function (s) { return s[key] != null; });
        var line = d3.line()
          .x(function (d) { return x(parseDate(d.date)); })
          .y(function (d) { return y(d[key]); })
          .curve(d3.curveMonotoneX);
        g.append('path').datum(lineData).attr('d', line)
          .attr('fill', 'none').attr('stroke', colors[key]).attr('stroke-width', 2);
      });

      g.append('g').attr('transform', 'translate(0,' + ih + ')').call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %y')))
        .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
      g.append('g').call(d3.axisLeft(y).ticks(5))
        .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
      g.selectAll('.domain, .tick line').attr('stroke', 'var(--chart-grid)');

      // Legend click handlers
      container.querySelectorAll('.pd-legend-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var key = this.getAttribute('data-key');
          visible[key] = !visible[key];
          render(data);
        });
      });
    }

    api.getRollingPDProfile().then(render).catch(function (err) {
      container.innerHTML = '<div class="panel-error">' + escapeHtml(err.message) + '</div>';
    });
    return { destroy: function () { container.innerHTML = ''; }, refresh: function (a) { (a || api).getRollingPDProfile().then(render); } };
  });

  /* ── Short Power Consistency panel ────────────────────────────────── */

  WKO5Registry.registerFactory('short-power', function (container, api) {
    function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }
    function fmtNum(v, dec) { return v != null && !isNaN(v) ? Number(v).toFixed(dec || 0) : '--'; }

    function render(data) {
      if (!data) { container.innerHTML = '<div class="panel-error">No short power data</div>'; return; }
      var ratio = data.ratio || (data.peak_1min && data.median_1min ? data.peak_1min / data.median_1min : null);
      var ratingColor = (data.consistency_rating === 'consistent' || data.consistency_rating === 'good') ? '#3fb950' : (data.consistency_rating === 'poor' || ratio > 2) ? '#f85149' : '#d29922';

      container.innerHTML = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;text-align:center;padding:12px 0;">' +
        '<div><div class="mono" style="font-size:1.4rem;font-weight:600;color:var(--accent);">' + fmtNum(data.peak_1min) + 'W</div><div style="color:var(--text-secondary);font-size:0.8rem;">Peak 1min</div></div>' +
        '<div><div class="mono" style="font-size:1.4rem;font-weight:600;">' + fmtNum(data.median_1min) + 'W</div><div style="color:var(--text-secondary);font-size:0.8rem;">Median 1min</div></div>' +
        '<div><div class="mono" style="font-size:1.4rem;font-weight:600;color:' + ratingColor + ';">' + fmtNum(ratio, 2) + 'x</div><div style="color:var(--text-secondary);font-size:0.8rem;">' + escapeHtml(data.consistency_rating || 'Ratio') + '</div></div>' +
      '</div>';
    }

    api.getShortPowerConsistency().then(render).catch(function (err) {
      container.innerHTML = '<div class="panel-error">' + escapeHtml(err.message) + '</div>';
    });
    return { destroy: function () { container.innerHTML = ''; }, refresh: function (a) { (a || api).getShortPowerConsistency().then(render); } };
  });
})();
