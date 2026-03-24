(function () {
  'use strict';
  if (!window.WKO5Registry) return;

  WKO5Registry.registerFactory('glycogen-budget', function (container, api) {
    function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

    var debounceTimer = null;
    var defaults = { ride_kj: 2000, duration_min: 180, carbs_g_hr: 60, weight_kg: 78 };

    container.innerHTML =
      '<div class="glyc-form" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:12px;font-size:0.8rem;">' +
        '<div><label style="color:var(--text-secondary);display:block;margin-bottom:2px;">Ride kJ</label><input type="number" name="ride_kj" value="' + defaults.ride_kj + '" style="width:100%;padding:4px 6px;background:var(--bg-primary);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;"></div>' +
        '<div><label style="color:var(--text-secondary);display:block;margin-bottom:2px;">Duration (min)</label><input type="number" name="duration_min" value="' + defaults.duration_min + '" style="width:100%;padding:4px 6px;background:var(--bg-primary);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;"></div>' +
        '<div><label style="color:var(--text-secondary);display:block;margin-bottom:2px;">Carbs (g/hr)</label><input type="number" name="carbs_g_hr" value="' + defaults.carbs_g_hr + '" style="width:100%;padding:4px 6px;background:var(--bg-primary);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;"></div>' +
        '<div><label style="color:var(--text-secondary);display:block;margin-bottom:2px;">Weight (kg)</label><input type="number" name="weight_kg" value="' + defaults.weight_kg + '" style="width:100%;padding:4px 6px;background:var(--bg-primary);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;"></div>' +
      '</div>' +
      '<div class="glyc-chart"></div>';

    function getFormValues() {
      var inputs = container.querySelectorAll('.glyc-form input');
      var vals = {};
      inputs.forEach(function (inp) { vals[inp.name] = parseFloat(inp.value) || 0; });
      return vals;
    }

    function renderChart(data) {
      var chartArea = container.querySelector('.glyc-chart');
      if (!chartArea) return;
      chartArea.innerHTML = '';

      if (!data || !data.timeline || !data.timeline.length) {
        chartArea.innerHTML = '<div style="color:var(--text-secondary);text-align:center;padding:16px;">Enter ride parameters above</div>';
        return;
      }

      var timeline = data.timeline;
      var width = chartArea.getBoundingClientRect().width || 500;
      var height = 180;
      var margin = { top: 10, right: 20, bottom: 30, left: 45 };
      var iw = width - margin.left - margin.right;
      var ih = height - margin.top - margin.bottom;

      var x = d3.scaleLinear().domain([0, d3.max(timeline, function (d) { return d.minute; })]).range([0, iw]);
      var y = d3.scaleLinear().domain([0, d3.max(timeline, function (d) { return d.glycogen_g; }) * 1.1]).range([ih, 0]);

      var svg = d3.select(chartArea).append('svg').attr('width', width).attr('height', height);
      var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

      // Bonk zone (below ~200g)
      var bonkThreshold = 200;
      if (y.domain()[1] > bonkThreshold) {
        g.append('rect').attr('x', 0).attr('y', y(bonkThreshold)).attr('width', iw).attr('height', ih - y(bonkThreshold))
          .attr('fill', 'rgba(248, 81, 73, 0.1)');
        g.append('text').attr('x', iw - 4).attr('y', y(bonkThreshold) + 14)
          .attr('text-anchor', 'end').attr('fill', '#f85149').attr('font-size', '9').text('Bonk Zone');
      }

      // Area + line
      var area = d3.area().x(function (d) { return x(d.minute); }).y0(ih).y1(function (d) { return y(d.glycogen_g); }).curve(d3.curveMonotoneX);
      var line = d3.line().x(function (d) { return x(d.minute); }).y(function (d) { return y(d.glycogen_g); }).curve(d3.curveMonotoneX);
      g.append('path').datum(timeline).attr('d', area).attr('fill', 'var(--accent)').attr('opacity', 0.15);
      g.append('path').datum(timeline).attr('d', line).attr('fill', 'none').attr('stroke', 'var(--accent)').attr('stroke-width', 2);

      // Bonk marker
      if (data.bonk_minute != null) {
        g.append('line').attr('x1', x(data.bonk_minute)).attr('x2', x(data.bonk_minute)).attr('y1', 0).attr('y2', ih)
          .attr('stroke', '#f85149').attr('stroke-width', 2).attr('stroke-dasharray', '4,3');
        g.append('text').attr('x', x(data.bonk_minute) + 4).attr('y', 14)
          .attr('fill', '#f85149').attr('font-size', '10').text('Bonk @ ' + data.bonk_minute + 'min');
      }

      // Feed markers
      if (data.feeds) {
        data.feeds.forEach(function (f) {
          g.append('circle').attr('cx', x(f.minute)).attr('cy', y(f.glycogen_g || 0) || ih / 2).attr('r', 4)
            .attr('fill', 'var(--success)').attr('stroke', '#fff').attr('stroke-width', 1);
        });
      }

      // Axes
      g.append('g').attr('transform', 'translate(0,' + ih + ')').call(d3.axisBottom(x).ticks(6).tickFormat(function (d) { return d + 'min'; }))
        .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
      g.append('g').call(d3.axisLeft(y).ticks(5).tickFormat(function (d) { return d + 'g'; }))
        .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
      g.selectAll('.domain, .tick line').attr('stroke', 'var(--chart-grid)');
    }

    function fetchAndRender() {
      var vals = getFormValues();
      api.postGlycogenBudget(vals).then(renderChart).catch(function (err) {
        var chart = container.querySelector('.glyc-chart');
        if (chart) chart.innerHTML = '<div class="panel-error">' + escapeHtml(err.message) + '</div>';
      });
    }

    // Debounced form input
    container.querySelectorAll('.glyc-form input').forEach(function (inp) {
      inp.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(fetchAndRender, 500);
      });
    });

    // Initial render
    fetchAndRender();

    return { destroy: function () { clearTimeout(debounceTimer); container.innerHTML = ''; }, refresh: function () { fetchAndRender(); } };
  });
})();
