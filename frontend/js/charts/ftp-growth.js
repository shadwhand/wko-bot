(function () {
  'use strict';
  if (!window.WKO5Registry) return;

  WKO5Registry.registerFactory('ftp-growth', function (container, api) {
    function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }
    function fmtNum(v, dec) { return v != null && !isNaN(v) ? Number(v).toFixed(dec || 0) : '--'; }

    function render(data) {
      if (!data) { container.innerHTML = '<div class="panel-error">No FTP growth data</div>'; return; }
      container.innerHTML = '';

      // API returns: {slope, intercept, r_squared, improvement_rate_w_per_year, plateau_detected, growth_phase, training_age_weeks, data_points}
      // May also have: {history: [{date, ftp}], current_ftp, log_fit: {a, b}}
      var phase = data.growth_phase || (data.plateau_detected ? 'plateau' : '--');
      var phaseColor = phase === 'plateau' ? 'var(--warning)' : phase === 'rapid' ? 'var(--success)' : 'var(--accent)';
      var growthRate = data.improvement_rate_w_per_year || data.growth_rate;
      var rSquared = data.r_squared;
      var trainingAge = data.training_age_weeks;

      var cards = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:8px;margin-bottom:12px;font-size:0.8rem;">';
      if (data.current_ftp != null) {
        cards += '<div style="text-align:center;"><div class="mono" style="font-size:1.4rem;font-weight:600;color:var(--accent);">' + fmtNum(data.current_ftp) + '</div><div style="color:var(--text-secondary);">Current FTP</div></div>';
      }
      cards += '<div style="text-align:center;"><div class="mono" style="font-size:1.4rem;font-weight:600;">' + fmtNum(growthRate, 1) + '</div><div style="color:var(--text-secondary);">W/year</div></div>' +
        '<div style="text-align:center;"><div style="font-size:1.1rem;font-weight:600;color:' + phaseColor + ';">' + escapeHtml(phase) + '</div><div style="color:var(--text-secondary);">Phase</div></div>';
      if (trainingAge != null) {
        cards += '<div style="text-align:center;"><div class="mono" style="font-size:1.4rem;font-weight:600;">' + fmtNum(trainingAge / 52, 1) + '</div><div style="color:var(--text-secondary);">Training Years</div></div>';
      }
      if (rSquared != null) {
        cards += '<div style="text-align:center;"><div class="mono" style="font-size:1.4rem;font-weight:600;">' + fmtNum(rSquared, 2) + '</div><div style="color:var(--text-secondary);">R&sup2; (fit)</div></div>';
      }
      cards += '</div>';
      container.insertAdjacentHTML('beforeend', cards);

      // Chart — use rolling FTP data if available, or history from this endpoint
      var history = data.history || [];
      if (!history.length) {
        // No scatter data — try to use the rolling FTP endpoint as data source for the chart
        container.insertAdjacentHTML('beforeend', '<div style="color:var(--text-muted);font-size:0.8rem;text-align:center;">See Rolling FTP panel for trend chart</div>');
        return;
      }

      var width = container.getBoundingClientRect().width || 500;
      var height = 200;
      var margin = { top: 10, right: 20, bottom: 30, left: 45 };
      var iw = width - margin.left - margin.right;
      var ih = height - margin.top - margin.bottom;

      var parseDate = function (s) { return new Date(s); };
      var dates = history.map(function (h) { return parseDate(h.date); });
      var ftps = history.map(function (h) { return h.ftp || h.mFTP; });

      var x = d3.scaleTime().domain(d3.extent(dates)).range([0, iw]);
      var y = d3.scaleLinear().domain([d3.min(ftps) * 0.95, d3.max(ftps) * 1.05]).range([ih, 0]);

      var svg = d3.select(container).append('svg').attr('width', width).attr('height', height);
      var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

      g.selectAll('circle').data(history).enter().append('circle')
        .attr('cx', function (d) { return x(parseDate(d.date)); })
        .attr('cy', function (d) { return y(d.ftp || d.mFTP); })
        .attr('r', 4)
        .attr('fill', 'var(--accent)')
        .attr('opacity', 0.7);

      // Log fit curve using slope/intercept if available
      if (data.slope != null && data.intercept != null && dates.length > 1) {
        var slope = data.slope, intercept = data.intercept;
        var t0 = dates[0].getTime();
        var curvePoints = [];
        for (var i = 0; i <= 50; i++) {
          var t = dates[0].getTime() + (dates[dates.length - 1].getTime() - dates[0].getTime()) * i / 50;
          var weeks = (t - t0) / (7 * 24 * 3600 * 1000);
          if (weeks <= 0) weeks = 0.1;
          var predicted = slope * Math.log(weeks + 1) + intercept;
          curvePoints.push({ date: new Date(t), ftp: predicted });
        }
        var line = d3.line().x(function (d) { return x(d.date); }).y(function (d) { return y(d.ftp); }).curve(d3.curveMonotoneX);
        g.append('path').datum(curvePoints).attr('d', line)
          .attr('fill', 'none').attr('stroke', 'var(--accent)').attr('stroke-width', 2).attr('stroke-dasharray', '6,3').attr('opacity', 0.6);
      }

      g.append('g').attr('transform', 'translate(0,' + ih + ')').call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %y')))
        .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
      g.append('g').call(d3.axisLeft(y).ticks(5).tickFormat(function (d) { return d + 'W'; }))
        .selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', '10');
      g.selectAll('.domain, .tick line').attr('stroke', 'var(--chart-grid)');
    }

    api.getFTPGrowth().then(render).catch(function (err) {
      container.innerHTML = '<div class="panel-error">' + escapeHtml(err.message) + '</div>';
    });
    return { destroy: function () { container.innerHTML = ''; }, refresh: function (a) { (a || api).getFTPGrowth().then(render); } };
  });
})();
