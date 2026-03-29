/**
 * WKO5 Dashboard — Performance Management Chart (PMC)
 *
 * D3 v7 line/area chart: CTL (fitness), ATL (fatigue), TSB (form).
 * Renders into a .chart-content container. Exports as window.PMCChart.
 */

class PMCChart {
  /**
   * @param {string} container - CSS selector for the chart-content div
   */
  constructor(container) {
    this.container = container;
    this.el = document.querySelector(container);
    this.svg = null;
    this.data = [];
    this.margin = { top: 20, right: 50, bottom: 30, left: 50 };
    this.width = 0;
    this.height = 0;

    /* Scales */
    this.xScale = null;
    this.yScaleLeft = null;
    this.yScaleRight = null;

    /* Zoom state */
    this.zoom = null;
    this.currentTransform = d3.zoomIdentity;

    /* Groups */
    this.g = null;
    this.clipId = 'pmc-clip-' + Math.random().toString(36).slice(2, 8);

    /* ResizeObserver */
    this._ro = null;

    /* Tooltip elements */
    this.tooltip = null;
    this.crosshair = null;
  }

  /**
   * Initial render with data.
   * @param {{ pmc: Array<{date: string, ctl: number, atl: number, tsb: number, tss: number}> }} data
   */
  render(data) {
    this.data = (data && data.pmc) || [];
    this._parse();
    this._setup();
    this._draw();
    this._attachResize();
  }

  /**
   * Update with new data (re-draws in place).
   * @param {{ pmc: Array }} data
   */
  update(data) {
    this.data = (data && data.pmc) || [];
    this._parse();
    this._draw();
  }

  /** Clean up DOM and observers. */
  destroy() {
    if (this._ro) this._ro.disconnect();
    if (this.svg) this.svg.remove();
    if (this.tooltip) this.tooltip.remove();
    this.svg = null;
  }

  /* ------------------------------------------------------------------
   *  Internal
   * ----------------------------------------------------------------*/

  /** Parse date strings into Date objects. */
  _parse() {
    var parseDate = d3.timeParse('%Y-%m-%d');
    this.data.forEach(function (d) {
      if (typeof d.date === 'string') d.date = parseDate(d.date);
      /* Normalize uppercase API keys to lowercase for chart internals */
      if (d.CTL != null && d.ctl == null) d.ctl = d.CTL;
      if (d.ATL != null && d.atl == null) d.atl = d.ATL;
      if (d.TSB != null && d.tsb == null) d.tsb = d.TSB;
      if (d.TSS != null && d.tss == null) d.tss = d.TSS;
    });
    this.data.sort(function (a, b) { return a.date - b.date; });
  }

  /** Create SVG, scales, axes, groups. */
  _setup() {
    /* Clear previous */
    if (this.svg) this.svg.remove();
    if (this.tooltip) this.tooltip.remove();

    var rect = this.el.getBoundingClientRect();
    this.width = rect.width - this.margin.left - this.margin.right;
    this.height = 280; /* Fixed chart height — never read from container */
    var totalH = this.height + this.margin.top + this.margin.bottom;

    /* SVG */
    this.svg = d3.select(this.el)
      .append('svg')
      .attr('width', rect.width)
      .attr('height', totalH);

    /* Clip path */
    this.svg.append('defs')
      .append('clipPath')
      .attr('id', this.clipId)
      .append('rect')
      .attr('width', this.width)
      .attr('height', this.height);

    this.g = this.svg.append('g')
      .attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');

    /* Scales */
    this._buildScales();

    /* Zoom */
    var self = this;
    this.zoom = d3.zoom()
      .scaleExtent([1, 20])
      .translateExtent([[0, 0], [this.width, this.height]])
      .extent([[0, 0], [this.width, this.height]])
      .on('zoom', function (event) {
        self.currentTransform = event.transform;
        self._onZoom();
      });

    this.svg.call(this.zoom);

    /* Tooltip */
    this.tooltip = d3.select(this.el)
      .append('div')
      .attr('class', 'pmc-tooltip')
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

  /** Compute x/y scales from current data. */
  _buildScales() {
    if (!this.data.length) {
      this.xScale = d3.scaleTime().range([0, this.width]);
      this.yScaleLeft = d3.scaleLinear().range([this.height, 0]);
      this.yScaleRight = d3.scaleLinear().range([this.height, 0]);
      return;
    }

    this.xScale = d3.scaleTime()
      .domain(d3.extent(this.data, function (d) { return d.date; }))
      .range([0, this.width]);

    var maxLeft = d3.max(this.data, function (d) {
      return Math.max(d.ctl || 0, d.atl || 0, d.tss || 0);
    }) || 100;

    this.yScaleLeft = d3.scaleLinear()
      .domain([0, maxLeft * 1.1])
      .range([this.height, 0]);

    var tsbExtent = d3.extent(this.data, function (d) { return d.tsb; });
    var tsbPad = Math.max(Math.abs(tsbExtent[0] || 0), Math.abs(tsbExtent[1] || 0)) * 1.2 || 30;
    this.yScaleRight = d3.scaleLinear()
      .domain([-tsbPad, tsbPad])
      .range([this.height, 0]);
  }

  /** Draw all chart elements. */
  _draw() {
    this.g.selectAll('*').remove();

    if (!this.data.length) return;

    var xS = this.currentTransform.rescaleX(this.xScale);
    var yL = this.yScaleLeft;
    var yR = this.yScaleRight;

    /* Clipped content group */
    var content = this.g.append('g')
      .attr('clip-path', 'url(#' + this.clipId + ')');

    /* Grid lines */
    this.g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yL)
        .tickSize(-this.width)
        .tickFormat('')
      )
      .selectAll('line')
      .style('stroke', 'var(--chart-grid)')
      .style('stroke-opacity', 0.5);

    this.g.selectAll('.grid .domain').remove();

    /* TSB zero line */
    var zeroY = yR(0);
    if (zeroY >= 0 && zeroY <= this.height) {
      content.append('line')
        .attr('x1', 0)
        .attr('x2', this.width)
        .attr('y1', zeroY)
        .attr('y2', zeroY)
        .style('stroke', 'var(--text-muted)')
        .style('stroke-dasharray', '4,3')
        .style('stroke-width', 1);
    }

    /* TSB area — positive (above zero) */
    var areaPositive = d3.area()
      .x(function (d) { return xS(d.date); })
      .y0(function () { return yR(0); })
      .y1(function (d) { return yR(Math.max(0, d.tsb)); })
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(this.data)
      .attr('d', areaPositive)
      .style('fill', 'var(--chart-area-positive)');

    /* TSB area — negative (below zero) */
    var areaNegative = d3.area()
      .x(function (d) { return xS(d.date); })
      .y0(function () { return yR(0); })
      .y1(function (d) { return yR(Math.min(0, d.tsb)); })
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(this.data)
      .attr('d', areaNegative)
      .style('fill', 'var(--chart-area-negative)');

    /* CTL line */
    var ctlLine = d3.line()
      .x(function (d) { return xS(d.date); })
      .y(function (d) { return yL(d.ctl); })
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(this.data)
      .attr('d', ctlLine)
      .style('fill', 'none')
      .style('stroke', 'var(--chart-line-1)')
      .style('stroke-width', 2);

    /* ATL line */
    var atlLine = d3.line()
      .x(function (d) { return xS(d.date); })
      .y(function (d) { return yL(d.atl); })
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(this.data)
      .attr('d', atlLine)
      .style('fill', 'none')
      .style('stroke', 'var(--chart-line-2)')
      .style('stroke-width', 1.5);

    /* X axis */
    this.g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', 'translate(0,' + this.height + ')')
      .call(d3.axisBottom(xS).ticks(8))
      .selectAll('text')
      .style('fill', 'var(--text-secondary)')
      .style('font-size', '11px');

    this.g.selectAll('.x-axis .domain, .x-axis line')
      .style('stroke', 'var(--border)');

    /* Y axis left (CTL / ATL / TSS) */
    this.g.append('g')
      .attr('class', 'y-axis-left')
      .call(d3.axisLeft(yL).ticks(6))
      .selectAll('text')
      .style('fill', 'var(--text-secondary)')
      .style('font-size', '11px');

    this.g.selectAll('.y-axis-left .domain, .y-axis-left line')
      .style('stroke', 'var(--border)');

    /* Y axis right (TSB) */
    this.g.append('g')
      .attr('class', 'y-axis-right')
      .attr('transform', 'translate(' + this.width + ',0)')
      .call(d3.axisRight(yR).ticks(6))
      .selectAll('text')
      .style('fill', 'var(--text-secondary)')
      .style('font-size', '11px');

    this.g.selectAll('.y-axis-right .domain, .y-axis-right line')
      .style('stroke', 'var(--border)');

    /* Legend */
    var legend = this.g.append('g')
      .attr('transform', 'translate(0,-6)');

    var labels = [
      { text: 'CTL', color: 'var(--chart-line-1)' },
      { text: 'ATL', color: 'var(--chart-line-2)' },
      { text: 'TSB', color: 'var(--chart-line-3)' }
    ];

    var xOff = 0;
    labels.forEach(function (l) {
      legend.append('rect')
        .attr('x', xOff)
        .attr('y', -8)
        .attr('width', 12)
        .attr('height', 3)
        .style('fill', l.color);
      legend.append('text')
        .attr('x', xOff + 16)
        .attr('y', -3)
        .text(l.text)
        .style('fill', 'var(--text-secondary)')
        .style('font-size', '11px');
      xOff += 55;
    });

    /* Hover overlay */
    this._attachHover(content, xS, yL, yR);
  }

  /** Handle zoom/pan transforms. */
  _onZoom() {
    this._draw();
  }

  /** Attach mouse hover for crosshair + tooltip. */
  _attachHover(content, xS, yL, yR) {
    var self = this;
    var bisect = d3.bisector(function (d) { return d.date; }).left;

    /* Crosshair line */
    var crosshair = content.append('line')
      .attr('y1', 0)
      .attr('y2', this.height)
      .style('stroke', 'var(--text-muted)')
      .style('stroke-width', 1)
      .style('display', 'none');

    /* Invisible overlay for mouse events */
    content.append('rect')
      .attr('width', this.width)
      .attr('height', this.height)
      .style('fill', 'none')
      .style('pointer-events', 'all')
      .on('mousemove', function (event) {
        var coords = d3.pointer(event);
        var x0 = xS.invert(coords[0]);
        var i = bisect(self.data, x0, 1);
        var d0 = self.data[i - 1];
        var d1 = self.data[i];
        if (!d0) return;
        var d = (d1 && (x0 - d0.date > d1.date - x0)) ? d1 : d0;

        var cx = xS(d.date);
        crosshair
          .attr('x1', cx)
          .attr('x2', cx)
          .style('display', null);

        var fmt = d3.timeFormat('%Y-%m-%d');
        self.tooltip
          .style('display', 'block')
          .html(
            '<strong>' + fmt(d.date) + '</strong><br>' +
            '<span style="color:var(--chart-line-1)">CTL:</span> ' + d.ctl.toFixed(1) + '<br>' +
            '<span style="color:var(--chart-line-2)">ATL:</span> ' + d.atl.toFixed(1) + '<br>' +
            '<span style="color:var(--chart-line-3)">TSB:</span> ' + d.tsb.toFixed(1) + '<br>' +
            'TSS: ' + (d.tss != null ? d.tss : '—')
          );

        /* Position tooltip */
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
        self.tooltip.style('display', 'none');
      });
  }

  /** Set up ResizeObserver to redraw on container resize. */
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
      self.height = 280; /* Fixed chart height — never read from container */

      if (self.svg) {
        self.svg
          .attr('width', newWidth)
          .attr('height', self.height + self.margin.top + self.margin.bottom);

        self.svg.select('#' + self.clipId + ' rect')
          .attr('width', self.width)
          .attr('height', self.height);
      }

      self._buildScales();
      if (self.zoom) {
        self.zoom
          .translateExtent([[0, 0], [self.width, self.height]])
          .extent([[0, 0], [self.width, self.height]]);
      }
      self._draw();
    });

    this._ro.observe(this.el);
  }
}

/* Expose globally */
window.PMCChart = PMCChart;

if (window.WKO5Registry) {
  WKO5Registry.registerFactory('pmc', function (container, api) {
    if (!container.id) container.id = 'pmc-panel-' + Date.now();
    var chart = new PMCChart('#' + container.id);
    api.getFitness().then(function (data) {
      if (data) chart.render(data);
    }).catch(function (err) {
      container.innerHTML = '<div class="panel-error">Unable to load: ' + err.message + '</div>';
    });
    return {
      destroy: function () { chart.destroy(); },
      refresh: function () {
        api.getFitness().then(function (data) {
          if (data) chart.render(data);
        });
      },
    };
  });
}
