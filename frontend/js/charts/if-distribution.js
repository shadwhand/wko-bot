(function () {
  'use strict';
  if (!window.WKO5Registry) return;

  function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

  WKO5Registry.registerFactory('if-distribution', function (container, api) {
    function render(data) {
      if (!data || !data.bins || !data.bins.length) {
        container.innerHTML = '<div class="panel-error">No IF distribution data</div>';
        return;
      }

      container.innerHTML = '';
      var width = container.getBoundingClientRect().width || 500;
      var height = 220;
      var margin = { top: 20, right: 20, bottom: 35, left: 40 };
      var iw = width - margin.left - margin.right;
      var ih = height - margin.top - margin.bottom;

      var bins = data.bins;
      var barData = bins.map(function (b) {
        var lo = b.range ? b.range[0] : (b.if_low || b.low || 0);
        var hi = b.range ? b.range[1] : (b.if_high || b.high || lo + 0.05);
        return { lo: lo, hi: hi, count: b.count || 0 };
      });

      var x = d3.scaleLinear()
        .domain([d3.min(barData, function (d) { return d.lo; }), d3.max(barData, function (d) { return d.hi; })])
        .range([0, iw]);
      var y = d3.scaleLinear()
        .domain([0, d3.max(barData, function (d) { return d.count; }) * 1.1])
        .range([ih, 0]);

      var svg = d3.select(container).append('svg').attr('width', width).attr('height', height);
      var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

      // Bars — color by intensity zone
      g.selectAll('rect.bar').data(barData).enter().append('rect')
        .attr('class', 'bar')
        .attr('x', function (d) { return x(d.lo); })
        .attr('width', function (d) { return Math.max(1, x(d.hi) - x(d.lo) - 1); })
        .attr('y', function (d) { return y(d.count); })
        .attr('height', function (d) { return ih - y(d.count); })
        .attr('fill', function (d) { return d.lo >= 0.70 ? '#f85149' : d.lo >= 0.55 ? '#d29922' : '#58a6ff'; })
        .attr('rx', 2);

      // Floor marker
      if (data.floor != null) {
        g.append('line').attr('x1', x(data.floor)).attr('x2', x(data.floor))
          .attr('y1', 0).attr('y2', ih)
          .attr('stroke', '#f85149').attr('stroke-width', 2).attr('stroke-dasharray', '4,3');
        g.append('text').attr('x', x(data.floor) + 4).attr('y', 12)
          .text('Floor ' + data.floor.toFixed(2))
          .attr('fill', '#f85149').attr('font-size', '10');
      }

      // Ceiling marker
      if (data.ceiling != null) {
        g.append('line').attr('x1', x(data.ceiling)).attr('x2', x(data.ceiling))
          .attr('y1', 0).attr('y2', ih)
          .attr('stroke', '#d29922').attr('stroke-width', 2).attr('stroke-dasharray', '4,3');
        g.append('text').attr('x', x(data.ceiling) + 4).attr('y', 12)
          .text('Ceiling ' + data.ceiling.toFixed(2))
          .attr('fill', '#d29922').attr('font-size', '10');
      }

      // Mean IF line
      if (data.mean_if != null) {
        g.append('line').attr('x1', x(data.mean_if)).attr('x2', x(data.mean_if))
          .attr('y1', 0).attr('y2', ih)
          .attr('stroke', 'var(--accent)').attr('stroke-width', 1.5).attr('stroke-dasharray', '2,2');
      }

      // Axes
      g.append('g').attr('transform', 'translate(0,' + ih + ')')
        .call(d3.axisBottom(x).ticks(8).tickFormat(function (d) { return d.toFixed(2); }))
        .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
      g.append('g').call(d3.axisLeft(y).ticks(5))
        .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
      g.selectAll('.domain, .tick line').attr('stroke', 'var(--chart-grid)');

      // Summary row below chart
      var summaryHtml = '<div style="display:flex;gap:16px;margin-top:8px;font-size:0.8rem;">';
      if (data.mean_if != null) summaryHtml += '<span>Mean IF: <span class="mono">' + data.mean_if.toFixed(2) + '</span></span>';
      if (data.total_rides != null) summaryHtml += '<span>Rides: <span class="mono">' + data.total_rides + '</span></span>';
      if (data.pct_above_floor != null) summaryHtml += '<span class="text-danger">' + (data.pct_above_floor * 100).toFixed(0) + '% above floor</span>';
      summaryHtml += '</div>';
      container.insertAdjacentHTML('beforeend', summaryHtml);
    }

    api.getIFDistribution().then(render).catch(function (err) {
      container.innerHTML = '<div class="panel-error">' + escapeHtml(err.message) + '</div>';
    });

    return {
      destroy: function () { container.innerHTML = ''; },
      refresh: function (a) { (a || api).getIFDistribution().then(render); }
    };
  });
})();
