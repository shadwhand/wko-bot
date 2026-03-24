(function () {
  'use strict';
  if (!window.WKO5Registry) return;

  WKO5Registry.registerFactory('opportunity-cost', function (container, api) {
    function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

    function renderBars(data) {
      var chartArea = container.querySelector('.oc-chart') || container;
      chartArea.innerHTML = '';
      if (!data || !data.priorities || !data.priorities.length) {
        chartArea.innerHTML = '<div style="color:var(--text-secondary);text-align:center;padding:16px;">No opportunity cost data for this route</div>';
        return;
      }

      var priorities = data.priorities.sort(function (a, b) { return (b.impact || 0) - (a.impact || 0); });
      var width = chartArea.getBoundingClientRect().width || 400;
      var barH = 28;
      var height = priorities.length * barH + 40;
      var margin = { top: 10, right: 80, bottom: 10, left: 120 };
      var iw = width - margin.left - margin.right;

      var x = d3.scaleLinear().domain([0, d3.max(priorities, function (d) { return d.impact || 0; }) * 1.1 || 1]).range([0, iw]);
      var y = d3.scaleBand().domain(priorities.map(function (d) { return d.area || d.name; })).range([0, priorities.length * barH]).padding(0.2);

      var svg = d3.select(chartArea).append('svg').attr('width', width).attr('height', height);
      var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

      var colorScale = d3.scaleLinear().domain([0, d3.max(priorities, function (d) { return d.impact; })]).range(['#58a6ff', '#f85149']);

      g.selectAll('rect').data(priorities).enter().append('rect')
        .attr('y', function (d) { return y(d.area || d.name); })
        .attr('width', function (d) { return x(d.impact || 0); })
        .attr('height', y.bandwidth())
        .attr('fill', function (d) { return colorScale(d.impact || 0); })
        .attr('rx', 3);

      // Labels
      g.selectAll('text.label').data(priorities).enter().append('text')
        .attr('x', -4)
        .attr('y', function (d) { return y(d.area || d.name) + y.bandwidth() / 2; })
        .attr('text-anchor', 'end').attr('dominant-baseline', 'middle')
        .attr('fill', 'var(--text-secondary)').attr('font-size', '11')
        .text(function (d) { return d.area || d.name; });

      // Impact values
      g.selectAll('text.value').data(priorities).enter().append('text')
        .attr('x', function (d) { return x(d.impact || 0) + 4; })
        .attr('y', function (d) { return y(d.area || d.name) + y.bandwidth() / 2; })
        .attr('dominant-baseline', 'middle')
        .attr('fill', 'var(--text-muted)').attr('font-size', '10')
        .text(function (d) { return d.impact != null ? d.impact.toFixed(1) : ''; });
    }

    // Build route selector + chart area
    container.innerHTML = '<div style="margin-bottom:8px;display:flex;gap:8px;align-items:center;">' +
      '<label style="color:var(--text-secondary);font-size:0.8rem;">Route:</label>' +
      '<select class="oc-route-select" style="padding:4px 8px;background:var(--bg-primary);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;font-size:0.8rem;flex:1;max-width:300px;">' +
        '<option value="">Select route...</option>' +
      '</select></div><div class="oc-chart"></div>';

    var select = container.querySelector('.oc-route-select');

    api.getRoutes().then(function (routes) {
      var list = (routes && routes.routes) || routes || [];
      for (var i = 0; i < list.length; i++) {
        var r = list[i];
        var opt = document.createElement('option');
        opt.value = r.id || r.route_id;
        opt.textContent = (r.name || r.route_name || 'Route ' + opt.value) + (r.total_distance_m ? ' (' + (r.total_distance_m / 1000).toFixed(0) + ' km)' : '');
        select.appendChild(opt);
      }
    });

    select.addEventListener('change', function () {
      if (!this.value) return;
      api.getOpportunityCost(this.value).then(renderBars).catch(function (err) {
        var chart = container.querySelector('.oc-chart');
        if (chart) chart.innerHTML = '<div class="panel-error">' + escapeHtml(err.message) + '</div>';
      });
    });

    return { destroy: function () { container.innerHTML = ''; }, refresh: function () {} };
  });
})();
