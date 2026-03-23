/**
 * Ride Time Series Chart — D3.js
 *
 * Multi-line chart: power, heart rate, cadence over elapsed time.
 * Supports zoom/pan, crosshair tooltip, interval shading, line toggling,
 * and configurable rolling average for power.
 *
 * CSS variables needed (add to styles.css):
 *   --chart-bg, --chart-grid, --text-primary, --text-secondary, --text-muted,
 *   --border, --accent, --danger, --success
 */

;(function () {
  'use strict';

  /* ------------------------------------------------------------------ */
  /*  Helpers                                                            */
  /* ------------------------------------------------------------------ */

  function fmtTime(seconds) {
    var h = Math.floor(seconds / 3600);
    var m = Math.floor((seconds % 3600) / 60);
    var s = Math.floor(seconds % 60);
    var mm = m < 10 ? '0' + m : '' + m;
    var ss = s < 10 ? '0' + s : '' + s;
    return h > 0 ? h + ':' + mm + ':' + ss : mm + ':' + ss;
  }

  function rollingAvg(data, key, window) {
    if (!window || window < 2) return data.map(function (d) { return d[key]; });
    var out = [];
    var sum = 0;
    var count = 0;
    for (var i = 0; i < data.length; i++) {
      var v = data[i][key];
      if (v != null) { sum += v; count++; }
      if (i >= window) {
        var old = data[i - window][key];
        if (old != null) { sum -= old; count--; }
      }
      out.push(count > 0 ? sum / count : null);
    }
    return out;
  }

  function css(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  /* ------------------------------------------------------------------ */
  /*  RideTimeseriesChart                                                */
  /* ------------------------------------------------------------------ */

  function RideTimeseriesChart(container) {
    this.container = typeof container === 'string'
      ? document.querySelector(container) : container;
    this._data = null;
    this._lines = { power: true, hr: true, cadence: false };
    this._smoothWindow = 5;       // default 5s rolling avg for power
    this._show30sAvg = false;
    this._svg = null;
    this._zoom = null;
    this._resizeObs = null;
    this._destroyed = false;
    this._dims = { w: 0, h: 0 };
    this._margin = { top: 8, right: 55, bottom: 36, left: 55 };
  }

  /* -- public API ---------------------------------------------------- */

  RideTimeseriesChart.prototype.render = function (data) {
    this._data = data;
    this._build();
    return this;
  };

  RideTimeseriesChart.prototype.update = function (data) {
    this._data = data;
    this._build();
    return this;
  };

  RideTimeseriesChart.prototype.destroy = function () {
    this._destroyed = true;
    if (this._resizeObs) this._resizeObs.disconnect();
    if (this.container) this.container.innerHTML = '';
  };

  /* -- internal ------------------------------------------------------ */

  RideTimeseriesChart.prototype._build = function () {
    var self = this;
    if (this._destroyed) return;

    /* clear previous */
    this.container.innerHTML = '';

    var data = this._data;
    if (!data || !data.records || !data.records.length) {
      this.container.innerHTML = '<div class="empty-state">No ride data</div>';
      return;
    }

    var records = data.records;
    var intervals = data.intervals || [];

    /* ---- Controls ---- */
    var controls = document.createElement('div');
    controls.style.cssText = 'display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap;align-items:center;';
    var toggles = [
      { key: 'power', label: 'Power', color: css('--accent') || '#58a6ff' },
      { key: 'hr', label: 'HR', color: css('--danger') || '#f85149' },
      { key: 'cadence', label: 'Cadence', color: css('--success') || '#3fb950' }
    ];

    toggles.forEach(function (t) {
      var btn = document.createElement('button');
      btn.textContent = t.label;
      btn.style.cssText =
        'padding:3px 10px;font-size:0.75rem;border-radius:4px;cursor:pointer;' +
        'font-family:inherit;transition:all .15s;border:1px solid ' + t.color + ';';
      function applyStyle() {
        if (self._lines[t.key]) {
          btn.style.background = t.color;
          btn.style.color = '#000';
        } else {
          btn.style.background = 'transparent';
          btn.style.color = t.color;
        }
      }
      applyStyle();
      btn.addEventListener('click', function () {
        if (t.key === 'power') return; // power always on
        self._lines[t.key] = !self._lines[t.key];
        applyStyle();
        self._draw();
      });
      if (t.key === 'power') btn.style.cursor = 'default';
      controls.appendChild(btn);
    });

    /* 30s avg toggle */
    var avgBtn = document.createElement('button');
    avgBtn.textContent = '30s Avg';
    avgBtn.style.cssText =
      'padding:3px 10px;font-size:0.75rem;border-radius:4px;cursor:pointer;' +
      'font-family:inherit;transition:all .15s;border:1px solid ' +
      (css('--text-muted') || '#484f58') + ';margin-left:auto;';
    function applyAvgStyle() {
      if (self._show30sAvg) {
        avgBtn.style.background = css('--text-muted') || '#484f58';
        avgBtn.style.color = css('--text-primary') || '#e6edf3';
      } else {
        avgBtn.style.background = 'transparent';
        avgBtn.style.color = css('--text-muted') || '#484f58';
      }
    }
    applyAvgStyle();
    avgBtn.addEventListener('click', function () {
      self._show30sAvg = !self._show30sAvg;
      applyAvgStyle();
      self._draw();
    });
    controls.appendChild(avgBtn);

    this.container.appendChild(controls);

    /* ---- SVG wrapper ---- */
    var wrapper = document.createElement('div');
    wrapper.style.cssText = 'position:relative;width:100%;';
    this.container.appendChild(wrapper);
    this._wrapper = wrapper;

    /* ---- Tooltip ---- */
    var tooltip = document.createElement('div');
    tooltip.style.cssText =
      'position:absolute;pointer-events:none;opacity:0;transition:opacity .1s;' +
      'background:' + (css('--bg-secondary') || '#161b22') + ';' +
      'border:1px solid ' + (css('--border') || '#30363d') + ';' +
      'border-radius:6px;padding:8px 10px;font-size:0.75rem;z-index:10;' +
      'color:' + (css('--text-primary') || '#e6edf3') + ';white-space:nowrap;';
    wrapper.appendChild(tooltip);
    this._tooltip = tooltip;

    /* ---- Create SVG ---- */
    this._svg = d3.select(wrapper).append('svg')
      .style('display', 'block')
      .style('width', '100%');

    /* groups */
    this._defs = this._svg.append('defs');
    this._gIntervals = this._svg.append('g').attr('class', 'intervals');
    this._gGrid = this._svg.append('g').attr('class', 'grid');
    this._gLines = this._svg.append('g').attr('class', 'lines');
    this._gAxes = this._svg.append('g').attr('class', 'axes');
    this._gCrosshair = this._svg.append('g').attr('class', 'crosshair')
      .style('display', 'none');

    /* clip path */
    this._clipId = 'ride-clip-' + Math.random().toString(36).slice(2, 8);
    this._defs.append('clipPath').attr('id', this._clipId)
      .append('rect');

    this._gIntervals.attr('clip-path', 'url(#' + this._clipId + ')');
    this._gLines.attr('clip-path', 'url(#' + this._clipId + ')');
    this._gCrosshair.attr('clip-path', 'url(#' + this._clipId + ')');

    /* crosshair line */
    this._crosshairLine = this._gCrosshair.append('line')
      .attr('stroke', css('--text-muted') || '#484f58')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '3,3');

    /* ---- Zoom ---- */
    this._currentTransform = d3.zoomIdentity;
    this._zoom = d3.zoom()
      .scaleExtent([1, 50])
      .on('zoom', function (event) {
        self._currentTransform = event.transform;
        self._draw();
      });

    /* ---- Interaction overlay ---- */
    this._overlay = this._svg.append('rect')
      .attr('class', 'overlay')
      .attr('fill', 'none')
      .style('pointer-events', 'all')
      .call(this._zoom);

    this._overlay.on('mousemove', function (event) {
      self._onMouseMove(event);
    }).on('mouseleave', function () {
      self._gCrosshair.style('display', 'none');
      self._tooltip.style.opacity = '0';
    });

    /* ---- Resize ---- */
    var lastW = 0;
    this._resizeObs = new ResizeObserver(function () {
      var w = Math.floor(wrapper.getBoundingClientRect().width);
      if (w === lastW || self._destroyed) return;
      lastW = w;
      self._draw();
    });
    this._resizeObs.observe(wrapper);

    this._draw();
  };

  RideTimeseriesChart.prototype._draw = function () {
    if (this._destroyed || !this._data) return;

    var records = this._data.records;
    var intervals = this._data.intervals || [];
    var m = this._margin;

    var rect = this._wrapper.getBoundingClientRect();
    var totalW = Math.max(rect.width, 300);
    var totalH = Math.max(Math.min(totalW * 0.4, 400), 220);
    var w = totalW - m.left - m.right;
    var h = totalH - m.top - m.bottom;
    this._dims = { w: w, h: h };

    this._svg
      .attr('viewBox', '0 0 ' + totalW + ' ' + totalH)
      .attr('height', totalH);

    /* Update clip rect */
    this._svg.select('#' + this._clipId + ' rect')
      .attr('x', m.left).attr('y', m.top)
      .attr('width', w).attr('height', h);

    this._overlay
      .attr('x', m.left).attr('y', m.top)
      .attr('width', w).attr('height', h);

    /* ---- Scales ---- */
    var xExtent = d3.extent(records, function (d) { return d.elapsed_seconds; });
    var xScale = d3.scaleLinear().domain(xExtent).range([m.left, m.left + w]);
    var xScaleZ = this._currentTransform.rescaleX(xScale);
    this._xScale = xScale;
    this._xScaleZ = xScaleZ;

    // Power scale (left)
    var pMax = d3.max(records, function (d) { return d.power; }) || 400;
    var yPower = d3.scaleLinear().domain([0, pMax * 1.1]).range([m.top + h, m.top]).nice();
    this._yPower = yPower;

    // HR scale (right)
    var hrExtent = d3.extent(records, function (d) { return d.heart_rate; });
    var hrMin = (hrExtent[0] || 80) - 10;
    var hrMax = (hrExtent[1] || 190) + 10;
    var yHR = d3.scaleLinear().domain([hrMin, hrMax]).range([m.top + h, m.top]).nice();
    this._yHR = yHR;

    // Cadence shares HR axis range roughly 0-140
    var cadMax = d3.max(records, function (d) { return d.cadence; }) || 120;
    var yCad = d3.scaleLinear().domain([0, cadMax * 1.2]).range([m.top + h, m.top]).nice();
    this._yCad = yCad;

    /* ---- Grid ---- */
    this._gGrid.selectAll('*').remove();
    var gridColor = css('--chart-grid') || '#21262d';

    // horizontal grid lines (power scale)
    var powerTicks = yPower.ticks(5);
    this._gGrid.selectAll('.hgrid')
      .data(powerTicks).enter()
      .append('line')
      .attr('x1', m.left).attr('x2', m.left + w)
      .attr('y1', function (d) { return yPower(d); })
      .attr('y2', function (d) { return yPower(d); })
      .attr('stroke', gridColor).attr('stroke-width', 0.5);

    /* ---- Axes ---- */
    this._gAxes.selectAll('*').remove();

    // X axis
    var xAxis = d3.axisBottom(xScaleZ)
      .ticks(Math.max(w / 100, 3))
      .tickFormat(fmtTime);
    this._gAxes.append('g')
      .attr('transform', 'translate(0,' + (m.top + h) + ')')
      .call(xAxis)
      .call(function (g) {
        g.select('.domain').attr('stroke', gridColor);
        g.selectAll('.tick line').attr('stroke', gridColor);
        g.selectAll('.tick text')
          .attr('fill', css('--text-secondary') || '#8b949e')
          .style('font-size', '0.7rem');
      });

    // Left axis (power)
    var leftAxis = d3.axisLeft(yPower).ticks(5);
    this._gAxes.append('g')
      .attr('transform', 'translate(' + m.left + ',0)')
      .call(leftAxis)
      .call(function (g) {
        g.select('.domain').attr('stroke', gridColor);
        g.selectAll('.tick line').attr('stroke', gridColor);
        g.selectAll('.tick text')
          .attr('fill', css('--accent') || '#58a6ff')
          .style('font-size', '0.7rem');
      });

    // Right axis (HR)
    var rightAxis = d3.axisRight(yHR).ticks(5);
    this._gAxes.append('g')
      .attr('transform', 'translate(' + (m.left + w) + ',0)')
      .call(rightAxis)
      .call(function (g) {
        g.select('.domain').attr('stroke', gridColor);
        g.selectAll('.tick line').attr('stroke', gridColor);
        g.selectAll('.tick text')
          .attr('fill', css('--danger') || '#f85149')
          .style('font-size', '0.7rem');
      });

    /* ---- Intervals ---- */
    this._gIntervals.selectAll('*').remove();
    if (intervals.length) {
      var intervalColor = css('--accent') || '#58a6ff';
      this._gIntervals.selectAll('.interval')
        .data(intervals).enter()
        .append('rect')
        .attr('x', function (d) { return xScaleZ(d.start_s); })
        .attr('width', function (d) {
          return Math.max(0, xScaleZ(d.end_s) - xScaleZ(d.start_s));
        })
        .attr('y', m.top)
        .attr('height', h)
        .attr('fill', function (d) {
          return d.type === 'hard' ? css('--danger') || '#f85149' : intervalColor;
        })
        .attr('opacity', 0.08);

      // Interval labels
      this._gIntervals.selectAll('.interval-label')
        .data(intervals).enter()
        .append('text')
        .attr('x', function (d) { return (xScaleZ(d.start_s) + xScaleZ(d.end_s)) / 2; })
        .attr('y', m.top + 14)
        .attr('text-anchor', 'middle')
        .attr('fill', css('--text-muted') || '#484f58')
        .style('font-size', '0.6rem')
        .text(function (d) {
          return d.avg_power ? d.avg_power + 'W' : '';
        });
    }

    /* ---- Lines ---- */
    this._gLines.selectAll('*').remove();

    var lineGen = function (yScale, key) {
      return d3.line()
        .defined(function (d) { return d[key] != null; })
        .x(function (d) { return xScaleZ(d.elapsed_seconds); })
        .y(function (d) { return yScale(d[key]); });
    };

    // Smoothed power data
    var smoothedPower = rollingAvg(records, 'power', this._smoothWindow);
    var smoothedRecords = records.map(function (d, i) {
      return { elapsed_seconds: d.elapsed_seconds, power: smoothedPower[i] };
    });

    // Power line (always on)
    if (this._lines.power) {
      this._gLines.append('path')
        .datum(smoothedRecords)
        .attr('fill', 'none')
        .attr('stroke', css('--accent') || '#58a6ff')
        .attr('stroke-width', 1.5)
        .attr('stroke-linejoin', 'round')
        .attr('d', lineGen(yPower, 'power'));

      // 30s rolling average overlay
      if (this._show30sAvg) {
        var avg30 = rollingAvg(records, 'power', 30);
        var avg30Records = records.map(function (d, i) {
          return { elapsed_seconds: d.elapsed_seconds, power: avg30[i] };
        });
        this._gLines.append('path')
          .datum(avg30Records)
          .attr('fill', 'none')
          .attr('stroke', css('--warning') || '#d29922')
          .attr('stroke-width', 2)
          .attr('stroke-linejoin', 'round')
          .attr('opacity', 0.85)
          .attr('d', lineGen(yPower, 'power'));
      }
    }

    // HR line
    if (this._lines.hr) {
      this._gLines.append('path')
        .datum(records)
        .attr('fill', 'none')
        .attr('stroke', css('--danger') || '#f85149')
        .attr('stroke-width', 1)
        .attr('stroke-linejoin', 'round')
        .attr('d', lineGen(yHR, 'heart_rate'));
    }

    // Cadence line
    if (this._lines.cadence) {
      this._gLines.append('path')
        .datum(records)
        .attr('fill', 'none')
        .attr('stroke', css('--success') || '#3fb950')
        .attr('stroke-width', 1)
        .attr('stroke-linejoin', 'round')
        .attr('d', lineGen(yCad, 'cadence'));
    }
  };

  RideTimeseriesChart.prototype._onMouseMove = function (event) {
    if (!this._xScaleZ || !this._data) return;

    var m = this._margin;
    var coords = d3.pointer(event, this._svg.node());
    var x = coords[0];
    var elapsed = this._xScaleZ.invert(x);
    var records = this._data.records;

    // Bisect to find nearest record
    var bisect = d3.bisector(function (d) { return d.elapsed_seconds; }).left;
    var idx = bisect(records, elapsed);
    idx = Math.max(0, Math.min(idx, records.length - 1));
    // pick closer of idx-1 and idx
    if (idx > 0) {
      var d0 = records[idx - 1];
      var d1 = records[idx];
      if (elapsed - d0.elapsed_seconds < d1.elapsed_seconds - elapsed) idx = idx - 1;
    }
    var d = records[idx];
    if (!d) return;

    var cx = this._xScaleZ(d.elapsed_seconds);

    // Crosshair
    this._gCrosshair.style('display', null);
    this._crosshairLine
      .attr('x1', cx).attr('x2', cx)
      .attr('y1', m.top).attr('y2', m.top + this._dims.h);

    // Tooltip
    var lines = ['<b>' + fmtTime(d.elapsed_seconds) + '</b>'];
    if (d.power != null) lines.push('<span style="color:' + (css('--accent') || '#58a6ff') + '">Power: ' + d.power + ' W</span>');
    if (d.heart_rate != null) lines.push('<span style="color:' + (css('--danger') || '#f85149') + '">HR: ' + d.heart_rate + ' bpm</span>');
    if (d.cadence != null) lines.push('<span style="color:' + (css('--success') || '#3fb950') + '">Cadence: ' + d.cadence + ' rpm</span>');
    if (d.speed != null) lines.push('Speed: ' + (d.speed * 3.6).toFixed(1) + ' km/h');

    this._tooltip.innerHTML = lines.join('<br>');
    this._tooltip.style.opacity = '1';

    // Position tooltip
    var wrapRect = this._wrapper.getBoundingClientRect();
    var svgRect = this._svg.node().getBoundingClientRect();
    var tipW = this._tooltip.offsetWidth;
    var scaleX = svgRect.width / (this._dims.w + m.left + m.right);
    var pixelX = cx * scaleX + svgRect.left - wrapRect.left;

    var left = pixelX + 12;
    if (left + tipW > wrapRect.width) left = pixelX - tipW - 12;
    this._tooltip.style.left = left + 'px';
    this._tooltip.style.top = '10px';
  };

  /* ---- Expose ---- */
  window.RideTimeseriesChart = RideTimeseriesChart;
})();
