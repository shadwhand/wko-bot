/**
 * WKO5 Dashboard — MMP / Power-Duration Curve Chart
 *
 * D3 v7 log-scale chart: MMP envelope + PD model overlay.
 * Renders into a .chart-content container. Exports as window.MMPChart.
 */

class MMPChart {
  /**
   * @param {string} container - CSS selector for the chart-content div
   */
  constructor(container) {
    this.container = container;
    this.el = document.querySelector(container);
    this.svg = null;
    this.data = [];
    this.compData = [];
    this.pdModel = null;
    this.margin = { top: 20, right: 20, bottom: 30, left: 55 };
    this.width = 0;
    this.height = 0;

    /* Scales */
    this.xScale = null;
    this.yScale = null;

    /* Groups */
    this.g = null;
    this.clipId = 'mmp-clip-' + Math.random().toString(36).slice(2, 8);

    /* ResizeObserver */
    this._ro = null;

    /* Tooltip */
    this.tooltip = null;
  }

  /**
   * Initial render with data.
   * @param {{ mmp: number[][], pd_model: Object }} data
   * @param {{ mmp: number[][] }} [comparisonData] - Optional comparison period
   */
  render(data, comparisonData) {
    this._ingest(data, comparisonData);
    this._setup();
    this._draw();
    this._attachResize();
  }

  /**
   * Update with new data.
   * @param {{ mmp: number[][], pd_model: Object }} data
   * @param {{ mmp: number[][] }} [comparisonData]
   */
  update(data, comparisonData) {
    this._ingest(data, comparisonData);
    this._draw();
  }

  /** Clean up. */
  destroy() {
    if (this._ro) this._ro.disconnect();
    if (this.svg) this.svg.remove();
    if (this.tooltip) this.tooltip.remove();
    this.svg = null;
  }

  /* ------------------------------------------------------------------
   *  Internal
   * ----------------------------------------------------------------*/

  /** Store and normalise incoming data. */
  _ingest(data, comparisonData) {
    this.data = (data && data.mmp) || [];
    this.pdModel = (data && data.pd_model) || null;
    this.compData = (comparisonData && comparisonData.mmp) || [];
  }

  /** Create SVG scaffold. */
  _setup() {
    if (this.svg) this.svg.remove();
    if (this.tooltip) this.tooltip.remove();

    var rect = this.el.getBoundingClientRect();
    this.width = rect.width - this.margin.left - this.margin.right;
    this.height = rect.height - this.margin.top - this.margin.bottom;
    if (this.height < 60) this.height = 200;

    this.svg = d3.select(this.el)
      .append('svg')
      .attr('width', rect.width)
      .attr('height', rect.height);

    this.svg.append('defs')
      .append('clipPath')
      .attr('id', this.clipId)
      .append('rect')
      .attr('width', this.width)
      .attr('height', this.height);

    this.g = this.svg.append('g')
      .attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');

    /* Tooltip */
    this.tooltip = d3.select(this.el)
      .append('div')
      .attr('class', 'mmp-tooltip')
      .style('position', 'absolute')
      .style('pointer-events', 'none')
      .style('background', 'var(--bg-tertiary)')
      .style('border', '1px solid var(--border)')
      .style('border-radius', '4px')
      .style('padding', '6px 10px')
      .style('font-size', '12px')
      .style('color', 'var(--text-primary)')
      .style('display', 'none')
      .style('z-index', '10')
      .style('white-space', 'nowrap');
  }

  /** Build x (log) and y (linear) scales. */
  _buildScales() {
    if (!this.data.length) {
      this.xScale = d3.scaleLog().range([0, this.width]).domain([1, 3600]);
      this.yScale = d3.scaleLinear().range([this.height, 0]).domain([0, 1000]);
      return;
    }

    var maxDur = d3.max(this.data, function (d) { return d[0]; }) || 3600;
    this.xScale = d3.scaleLog()
      .domain([1, maxDur])
      .range([0, this.width])
      .clamp(true);

    var maxW = d3.max(this.data, function (d) { return d[1]; }) || 1000;
    if (this.compData.length) {
      var compMax = d3.max(this.compData, function (d) { return d[1]; }) || 0;
      maxW = Math.max(maxW, compMax);
    }
    this.yScale = d3.scaleLinear()
      .domain([0, maxW * 1.08])
      .range([this.height, 0]);
  }

  /** Draw all chart elements. */
  _draw() {
    this.g.selectAll('*').remove();
    this._buildScales();

    if (!this.data.length) return;

    var xS = this.xScale;
    var yS = this.yScale;

    var content = this.g.append('g')
      .attr('clip-path', 'url(#' + this.clipId + ')');

    /* Background power zones (very subtle) */
    this._drawZones(content, xS);

    /* Grid lines */
    this.g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yS)
        .tickSize(-this.width)
        .tickFormat('')
      )
      .selectAll('line')
      .style('stroke', 'var(--chart-grid)')
      .style('stroke-opacity', 0.4);

    this.g.selectAll('.grid .domain').remove();

    /* Comparison MMP (if present) — draw first, underneath */
    if (this.compData.length) {
      var compLine = d3.line()
        .x(function (d) { return xS(d[0]); })
        .y(function (d) { return yS(d[1]); })
        .curve(d3.curveMonotoneX);

      content.append('path')
        .datum(this.compData)
        .attr('d', compLine)
        .style('fill', 'none')
        .style('stroke', 'var(--text-muted)')
        .style('stroke-width', 1.5)
        .style('stroke-dasharray', '4,3');
    }

    /* MMP area fill */
    var area = d3.area()
      .x(function (d) { return xS(d[0]); })
      .y0(this.height)
      .y1(function (d) { return yS(d[1]); })
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(this.data)
      .attr('d', area)
      .style('fill', 'var(--accent)')
      .style('opacity', 0.12);

    /* MMP line */
    var line = d3.line()
      .x(function (d) { return xS(d[0]); })
      .y(function (d) { return yS(d[1]); })
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(this.data)
      .attr('d', line)
      .style('fill', 'none')
      .style('stroke', 'var(--accent)')
      .style('stroke-width', 2);

    /* PD model overlay */
    if (this.pdModel) {
      this._drawPDModel(content, xS, yS);
    }

    /* X axis — log scale with custom tick labels */
    var tickValues = [1, 5, 30, 60, 300, 1200, 3600];
    var maxDur = this.xScale.domain()[1];
    tickValues = tickValues.filter(function (t) { return t <= maxDur; });

    this.g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', 'translate(0,' + this.height + ')')
      .call(
        d3.axisBottom(xS)
          .tickValues(tickValues)
          .tickFormat(function (d) { return MMPChart._fmtDurShort(d); })
      )
      .selectAll('text')
      .style('fill', 'var(--text-secondary)')
      .style('font-size', '11px');

    this.g.selectAll('.x-axis .domain, .x-axis line')
      .style('stroke', 'var(--border)');

    /* Y axis */
    this.g.append('g')
      .attr('class', 'y-axis')
      .call(d3.axisLeft(yS).ticks(6))
      .selectAll('text')
      .style('fill', 'var(--text-secondary)')
      .style('font-size', '11px');

    this.g.selectAll('.y-axis .domain, .y-axis line')
      .style('stroke', 'var(--border)');

    /* Y axis label */
    this.g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -this.height / 2)
      .attr('y', -40)
      .attr('text-anchor', 'middle')
      .style('fill', 'var(--text-muted)')
      .style('font-size', '11px')
      .text('Watts');

    /* Hover */
    this._attachHover(content, xS, yS);
  }

  /** Draw subtle background zones (neuromuscular, anaerobic, VO2max, threshold, endurance). */
  _drawZones(content, xS) {
    var zones = [
      { label: 'NM',   from: 1,    to: 15,   color: 'var(--danger)' },
      { label: 'AN',   from: 15,   to: 120,  color: 'var(--warning)' },
      { label: 'VO2',  from: 120,  to: 480,  color: 'var(--accent)' },
      { label: 'TH',   from: 480,  to: 1200, color: 'var(--success)' },
      { label: 'END',  from: 1200, to: this.xScale.domain()[1], color: 'var(--text-muted)' }
    ];

    var height = this.height;

    zones.forEach(function (z) {
      var x1 = xS(Math.max(z.from, xS.domain()[0]));
      var x2 = xS(Math.min(z.to, xS.domain()[1]));
      if (x2 <= x1) return;

      content.append('rect')
        .attr('x', x1)
        .attr('y', 0)
        .attr('width', x2 - x1)
        .attr('height', height)
        .style('fill', z.color)
        .style('opacity', 0.04);

      content.append('text')
        .attr('x', (x1 + x2) / 2)
        .attr('y', 14)
        .attr('text-anchor', 'middle')
        .style('fill', 'var(--text-muted)')
        .style('font-size', '9px')
        .style('opacity', 0.6)
        .text(z.label);
    });
  }

  /** Draw PD model curve from parameters. */
  _drawPDModel(content, xS, yS) {
    var m = this.pdModel;
    var maxDur = xS.domain()[1];
    var points = [];

    /* Generate model curve points on log-spaced durations */
    for (var t = 1; t <= maxDur; t = Math.ceil(t * 1.05) || t + 1) {
      var watts;
      if (t <= m.tau) {
        watts = m.pmax;
      } else {
        watts = ((m.frc * 1000) / (t + m.t0)) + m.mftp;
      }
      if (watts > 0) points.push([t, watts]);
    }

    var modelLine = d3.line()
      .x(function (d) { return xS(d[0]); })
      .y(function (d) { return yS(d[1]); })
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(points)
      .attr('d', modelLine)
      .style('fill', 'none')
      .style('stroke', 'var(--warning)')
      .style('stroke-width', 1.5)
      .style('stroke-dasharray', '6,3')
      .style('opacity', 0.8);
  }

  /** Attach hover behaviour. */
  _attachHover(content, xS, yS) {
    var self = this;
    var bisect = d3.bisector(function (d) { return d[0]; }).left;

    var crosshair = content.append('line')
      .attr('y1', 0)
      .attr('y2', this.height)
      .style('stroke', 'var(--text-muted)')
      .style('stroke-width', 1)
      .style('display', 'none');

    var dot = content.append('circle')
      .attr('r', 4)
      .style('fill', 'var(--accent)')
      .style('display', 'none');

    content.append('rect')
      .attr('width', this.width)
      .attr('height', this.height)
      .style('fill', 'none')
      .style('pointer-events', 'all')
      .on('mousemove', function (event) {
        var coords = d3.pointer(event);
        var durAtMouse = xS.invert(coords[0]);
        var i = bisect(self.data, durAtMouse, 1);
        var d0 = self.data[i - 1];
        var d1 = self.data[i];
        if (!d0) return;
        var d = (d1 && (durAtMouse - d0[0] > d1[0] - durAtMouse)) ? d1 : d0;

        var cx = xS(d[0]);
        var cy = yS(d[1]);

        crosshair
          .attr('x1', cx)
          .attr('x2', cx)
          .style('display', null);

        dot
          .attr('cx', cx)
          .attr('cy', cy)
          .style('display', null);

        self.tooltip
          .style('display', 'block')
          .html(
            '<strong>' + MMPChart._fmtDuration(d[0]) + '</strong><br>' +
            d[1] + ' W'
          );

        var tipNode = self.tooltip.node();
        var tipW = tipNode.offsetWidth;
        var left = cx + self.margin.left + 12;
        if (left + tipW > self.el.getBoundingClientRect().width) {
          left = cx + self.margin.left - tipW - 12;
        }
        self.tooltip
          .style('left', left + 'px')
          .style('top', (self.margin.top + 10) + 'px');
      })
      .on('mouseleave', function () {
        crosshair.style('display', 'none');
        dot.style('display', 'none');
        self.tooltip.style('display', 'none');
      });
  }

  /** Set up ResizeObserver. */
  _attachResize() {
    var self = this;
    if (this._ro) this._ro.disconnect();
    var lastWidth = 0;

    this._ro = new ResizeObserver(function () {
      var rect = self.el.getBoundingClientRect();
      var newWidth = Math.floor(rect.width);
      /* Only react to width changes — prevents infinite height feedback loop */
      if (newWidth === lastWidth) return;
      lastWidth = newWidth;

      self.width = newWidth - self.margin.left - self.margin.right;
      self.height = 280; /* Fixed chart height */

      if (self.svg) {
        self.svg
          .attr('width', newWidth)
          .attr('height', self.height + self.margin.top + self.margin.bottom);

        self.svg.select('#' + self.clipId + ' rect')
          .attr('width', self.width)
          .attr('height', self.height);
      }

      self._draw();
    });

    this._ro.observe(this.el);
  }

  /* ------------------------------------------------------------------
   *  Static formatters
   * ----------------------------------------------------------------*/

  /**
   * Format duration in seconds to short axis label (1s, 5min, 60min).
   * @param {number} s
   * @returns {string}
   */
  static _fmtDurShort(s) {
    if (s < 60) return s + 's';
    return Math.round(s / 60) + 'min';
  }

  /**
   * Format duration in seconds to readable tooltip string (Xmin Ys).
   * @param {number} s
   * @returns {string}
   */
  static _fmtDuration(s) {
    if (s < 60) return s + 's';
    var min = Math.floor(s / 60);
    var sec = s % 60;
    if (sec === 0) return min + 'min';
    return min + 'min ' + sec + 's';
  }
}

/* Expose globally */
window.MMPChart = MMPChart;

if (window.WKO5Registry) {
  WKO5Registry.registerFactory('mmp', function (container, api) {
    var chart = new MMPChart(container);
    api.getModel().then(function (data) {
      if (data) chart.render(data);
    }).catch(function (err) {
      container.innerHTML = '<div class="panel-error">Unable to load: ' + err.message + '</div>';
    });
    return {
      destroy: function () { chart.destroy(); },
      refresh: function () {
        api.getModel().then(function (data) {
          if (data) chart.render(data);
        });
      },
    };
  });
}
