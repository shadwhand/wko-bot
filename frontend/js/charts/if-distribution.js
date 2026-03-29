(function () {
  'use strict';
  if (!window.WKO5Registry) return;

  function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

  WKO5Registry.registerFactory('if-distribution', function (container, api) {
    function render(data) {
      if (!data) { container.innerHTML = '<div class="panel-error">No IF distribution data</div>'; return; }

      // API returns {histogram: {"0.40-0.45": 2, ...}, floor, ceiling, rides_analyzed}
      // Convert histogram object to bar data
      var histogram = data.histogram || data.bins || {};
      var barData = [];

      if (Array.isArray(histogram)) {
        // Already an array of {range, count}
        barData = histogram.map(function (b) {
          var lo = b.range ? b.range[0] : (b.if_low || b.low || 0);
          var hi = b.range ? b.range[1] : (b.if_high || b.high || lo + 0.05);
          return { lo: lo, hi: hi, count: b.count || 0 };
        });
      } else {
        // Object: {"0.40-0.45": 2, "0.50-0.55": 1, ...}
        for (var key in histogram) {
          if (!histogram.hasOwnProperty(key)) continue;
          var parts = key.split('-');
          if (parts.length === 2) {
            barData.push({ lo: parseFloat(parts[0]), hi: parseFloat(parts[1]), count: histogram[key] });
          }
        }
        barData.sort(function (a, b) { return a.lo - b.lo; });
      }

      if (!barData.length) { container.innerHTML = '<div class="panel-error">No IF distribution data</div>'; return; }

      container.innerHTML = '';
      var width = container.getBoundingClientRect().width || 500;
      var height = 220;
      var margin = { top: 20, right: 20, bottom: 35, left: 40 };
      var iw = width - margin.left - margin.right;
      var ih = height - margin.top - margin.bottom;

      var x = d3.scaleLinear()
        .domain([d3.min(barData, function (d) { return d.lo; }), d3.max(barData, function (d) { return d.hi; })])
        .range([0, iw]);
      var y = d3.scaleLinear()
        .domain([0, d3.max(barData, function (d) { return d.count; }) * 1.1])
        .range([ih, 0]);

      var svg = d3.select(container).append('svg').attr('width', width).attr('height', height);
      var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

      g.selectAll('rect.bar').data(barData).enter().append('rect')
        .attr('class', 'bar')
        .attr('x', function (d) { return x(d.lo); })
        .attr('width', function (d) { return Math.max(1, x(d.hi) - x(d.lo) - 1); })
        .attr('y', function (d) { return y(d.count); })
        .attr('height', function (d) { return ih - y(d.count); })
        .attr('fill', function (d) { return d.lo >= 0.70 ? '#f85149' : d.lo >= 0.55 ? '#d29922' : '#58a6ff'; })
        .attr('rx', 2);

      if (data.floor != null) {
        g.append('line').attr('x1', x(data.floor)).attr('x2', x(data.floor))
          .attr('y1', 0).attr('y2', ih)
          .attr('stroke', '#f85149').attr('stroke-width', 2).attr('stroke-dasharray', '4,3');
        g.append('text').attr('x', x(data.floor) + 4).attr('y', 12)
          .text('Floor ' + data.floor.toFixed(2))
          .attr('fill', '#f85149').attr('font-size', '10');
      }

      if (data.ceiling != null) {
        g.append('line').attr('x1', x(data.ceiling)).attr('x2', x(data.ceiling))
          .attr('y1', 0).attr('y2', ih)
          .attr('stroke', '#d29922').attr('stroke-width', 2).attr('stroke-dasharray', '4,3');
        g.append('text').attr('x', x(data.ceiling) + 4).attr('y', 12)
          .text('Ceiling ' + data.ceiling.toFixed(2))
          .attr('fill', '#d29922').attr('font-size', '10');
      }

      // Axes
      g.append('g').attr('transform', 'translate(0,' + ih + ')')
        .call(d3.axisBottom(x).ticks(8).tickFormat(function (d) { return d.toFixed(2); }))
        .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
      g.append('g').call(d3.axisLeft(y).ticks(5))
        .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
      g.selectAll('.domain, .tick line').attr('stroke', 'var(--chart-grid)');

      // Summary
      var summaryHtml = '<div style="display:flex;gap:16px;margin-top:8px;font-size:0.8rem;">';
      if (data.rides_analyzed != null) summaryHtml += '<span>Rides: <span class="mono">' + data.rides_analyzed + '</span></span>';
      if (data.spread != null) summaryHtml += '<span>Spread: <span class="mono">' + data.spread.toFixed(2) + '</span></span>';
      if (data.compressed != null) summaryHtml += '<span>' + (data.compressed ? '<span class="text-warning">Compressed</span>' : '<span class="text-success">Good spread</span>') + '</span>';
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
