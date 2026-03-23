/**
 * Zone Distribution Chart — D3.js
 *
 * Stacked horizontal bar showing time in each power zone.
 * Supports single-ride and multi-period (weekly/monthly comparison) modes.
 *
 * CSS classes needed (add to styles.css):
 *   .zone-1 { fill: #6b7280; }  -- gray (Active Recovery)
 *   .zone-2 { fill: #3b82f6; }  -- blue (Endurance)
 *   .zone-3 { fill: #22c55e; }  -- green (Tempo)
 *   .zone-4 { fill: #eab308; }  -- yellow (Threshold)
 *   .zone-5 { fill: #f97316; }  -- orange (VO2max)
 *   .zone-6 { fill: #ef4444; }  -- red (Anaerobic)
 *   .zone-7 { fill: #a855f7; }  -- purple (Neuromuscular)
 */

;(function () {
  'use strict';

  /* ------------------------------------------------------------------ */
  /*  Helpers                                                            */
  /* ------------------------------------------------------------------ */

  var ZONE_COLORS = {
    z1: '#6b7280', z2: '#3b82f6', z3: '#22c55e', z4: '#eab308',
    z5: '#f97316', z6: '#ef4444', z7: '#a855f7'
  };

  function zoneColor(zone) {
    return ZONE_COLORS['z' + zone] || '#888';
  }

  function fmtDuration(sec) {
    if (sec == null) return '0:00';
    var h = Math.floor(sec / 3600);
    var m = Math.floor((sec % 3600) / 60);
    var s = Math.floor(sec % 60);
    if (h > 0) return h + ':' + (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
    return m + ':' + (s < 10 ? '0' : '') + s;
  }

  function pct(val, total) {
    if (!total) return '0%';
    return (val / total * 100).toFixed(1) + '%';
  }

  function css(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  /* ------------------------------------------------------------------ */
  /*  ZonesChart                                                         */
  /* ------------------------------------------------------------------ */

  function ZonesChart(container) {
    this.container = typeof container === 'string'
      ? document.querySelector(container) : container;
    this._data = null;
    this._svg = null;
    this._resizeObs = null;
    this._destroyed = false;
    this._tooltip = null;
    this._mode = 'single'; // 'single' or 'multi'
  }

  /* -- public API ---------------------------------------------------- */

  ZonesChart.prototype.render = function (data) {
    this._data = data;
    this._detectMode();
    this._build();
    return this;
  };

  ZonesChart.prototype.update = function (data) {
    this._data = data;
    this._detectMode();
    this._build();
    return this;
  };

  ZonesChart.prototype.destroy = function () {
    this._destroyed = true;
    if (this._resizeObs) this._resizeObs.disconnect();
    if (this.container) this.container.innerHTML = '';
  };

  /* -- internal ------------------------------------------------------ */

  ZonesChart.prototype._detectMode = function () {
    if (!this._data) { this._mode = 'single'; return; }
    // Multi-period: data is { periods: [ { label, zones, total_seconds }, ... ] }
    this._mode = Array.isArray(this._data.periods) ? 'multi' : 'single';
  };

  ZonesChart.prototype._build = function () {
    var self = this;
    if (this._destroyed) return;
    this.container.innerHTML = '';

    if (!this._data) {
      this.container.innerHTML = '<div class="empty-state">No zone data</div>';
      return;
    }

    /* ---- Tooltip ---- */
    var tooltip = document.createElement('div');
    tooltip.style.cssText =
      'position:absolute;pointer-events:none;opacity:0;transition:opacity .1s;' +
      'background:' + (css('--bg-secondary') || '#161b22') + ';' +
      'border:1px solid ' + (css('--border') || '#30363d') + ';' +
      'border-radius:6px;padding:8px 10px;font-size:0.75rem;z-index:10;' +
      'color:' + (css('--text-primary') || '#e6edf3') + ';white-space:nowrap;';
    this._tooltip = tooltip;

    var wrapper = document.createElement('div');
    wrapper.style.cssText = 'position:relative;width:100%;';
    wrapper.appendChild(tooltip);
    this.container.appendChild(wrapper);
    this._wrapper = wrapper;

    if (this._mode === 'multi') {
      this._buildMulti(wrapper);
    } else {
      this._buildSingle(wrapper);
    }

    /* Legend */
    this._buildLegend();

    /* Resize observer */
    var lastW = 0;
    this._resizeObs = new ResizeObserver(function () {
      var w = Math.floor(self.container.getBoundingClientRect().width);
      if (w === lastW || self._destroyed) return;
      lastW = w;
      self._build();
    });
    this._resizeObs.observe(this.container);
  };

  /* ---- Single bar mode ---- */

  ZonesChart.prototype._buildSingle = function (wrapper) {
    var self = this;
    var zones = this._data.zones || [];
    var total = this._data.total_seconds || zones.reduce(function (s, z) { return s + z.seconds; }, 0);

    var margin = { top: 12, right: 16, bottom: 24, left: 16 };
    var barH = 36;
    var totalH = margin.top + barH + margin.bottom + 4;
    var rect = wrapper.getBoundingClientRect();
    var totalW = Math.max(rect.width, 200);
    var w = totalW - margin.left - margin.right;

    var svg = d3.select(wrapper).append('svg')
      .attr('width', totalW).attr('height', totalH)
      .style('display', 'block');
    this._svg = svg;

    var xScale = d3.scaleLinear().domain([0, total]).range([0, w]);

    // Build cumulative offsets
    var cumX = 0;
    var segments = zones.map(function (z) {
      var seg = { zone: z, x: cumX, w: xScale(z.seconds) };
      cumX += seg.w;
      return seg;
    });

    var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    // Bar segments
    g.selectAll('.zone-seg')
      .data(segments).enter()
      .append('rect')
      .attr('x', function (d) { return d.x; })
      .attr('y', 0)
      .attr('width', function (d) { return Math.max(d.w, 0); })
      .attr('height', barH)
      .attr('rx', function (d, i) {
        // Round corners on first/last
        return (i === 0 || i === segments.length - 1) ? 4 : 0;
      })
      .attr('fill', function (d) { return zoneColor(d.zone.zone); })
      .attr('class', function (d) { return 'zone-' + d.zone.zone; })
      .style('cursor', 'default')
      .on('mouseenter', function (event, d) {
        self._showTooltip(event, d.zone, total);
      })
      .on('mousemove', function (event) {
        self._moveTooltip(event);
      })
      .on('mouseleave', function () {
        self._tooltip.style.opacity = '0';
      });

    // Labels inside segments
    g.selectAll('.zone-label')
      .data(segments).enter()
      .append('text')
      .attr('x', function (d) { return d.x + d.w / 2; })
      .attr('y', barH / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .style('font-size', '0.65rem')
      .style('font-weight', '600')
      .style('pointer-events', 'none')
      .text(function (d) {
        if (d.w < 50) return '';  // too narrow for text
        if (d.w < 90) return 'Z' + d.zone.zone;
        return d.zone.name + ' ' + fmtDuration(d.zone.seconds);
      });

    // Total label
    svg.append('text')
      .attr('x', totalW / 2)
      .attr('y', totalH - 4)
      .attr('text-anchor', 'middle')
      .attr('fill', css('--text-secondary') || '#8b949e')
      .style('font-size', '0.7rem')
      .text('Total: ' + fmtDuration(total));
  };

  /* ---- Multi-period mode ---- */

  ZonesChart.prototype._buildMulti = function (wrapper) {
    var self = this;
    var periods = this._data.periods;
    if (!periods || !periods.length) return;

    var margin = { top: 8, right: 16, bottom: 8, left: 80 };
    var barH = 28;
    var barGap = 6;
    var totalH = margin.top + periods.length * (barH + barGap) + margin.bottom;
    var rect = wrapper.getBoundingClientRect();
    var totalW = Math.max(rect.width, 200);
    var w = totalW - margin.left - margin.right;

    // Find max total for consistent scale
    var maxTotal = d3.max(periods, function (p) { return p.total_seconds; }) || 1;
    var xScale = d3.scaleLinear().domain([0, maxTotal]).range([0, w]);

    var svg = d3.select(wrapper).append('svg')
      .attr('width', totalW).attr('height', totalH)
      .style('display', 'block');
    this._svg = svg;

    periods.forEach(function (period, pi) {
      var yOff = margin.top + pi * (barH + barGap);
      var zones = period.zones || [];
      var total = period.total_seconds || 0;

      // Period label
      svg.append('text')
        .attr('x', margin.left - 8)
        .attr('y', yOff + barH / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', 'end')
        .attr('fill', css('--text-secondary') || '#8b949e')
        .style('font-size', '0.7rem')
        .text(period.label || 'Period ' + (pi + 1));

      // Segments
      var cumX = 0;
      zones.forEach(function (z) {
        var segW = xScale(z.seconds);
        svg.append('rect')
          .attr('x', margin.left + cumX)
          .attr('y', yOff)
          .attr('width', Math.max(segW, 0))
          .attr('height', barH)
          .attr('fill', zoneColor(z.zone))
          .attr('class', 'zone-' + z.zone)
          .style('cursor', 'default')
          .on('mouseenter', function (event) {
            self._showTooltip(event, z, total);
          })
          .on('mousemove', function (event) {
            self._moveTooltip(event);
          })
          .on('mouseleave', function () {
            self._tooltip.style.opacity = '0';
          });

        // inline label if wide enough
        if (segW > 40) {
          svg.append('text')
            .attr('x', margin.left + cumX + segW / 2)
            .attr('y', yOff + barH / 2)
            .attr('dy', '0.35em')
            .attr('text-anchor', 'middle')
            .attr('fill', '#fff')
            .style('font-size', '0.6rem')
            .style('font-weight', '600')
            .style('pointer-events', 'none')
            .text('Z' + z.zone);
        }

        cumX += segW;
      });
    });
  };

  /* ---- Legend ---- */

  ZonesChart.prototype._buildLegend = function () {
    var zones = this._mode === 'single'
      ? (this._data.zones || [])
      : (this._data.periods && this._data.periods[0] ? this._data.periods[0].zones || [] : []);

    var legend = document.createElement('div');
    legend.style.cssText =
      'display:flex;flex-wrap:wrap;gap:10px;margin-top:8px;padding:0 4px;';

    zones.forEach(function (z) {
      var item = document.createElement('div');
      item.style.cssText = 'display:flex;align-items:center;gap:4px;';

      var swatch = document.createElement('span');
      swatch.style.cssText =
        'width:10px;height:10px;border-radius:2px;flex-shrink:0;background:' +
        zoneColor(z.zone) + ';';

      var label = document.createElement('span');
      label.style.cssText =
        'font-size:0.7rem;color:' + (css('--text-secondary') || '#8b949e') + ';';
      label.textContent = z.name || ('Zone ' + z.zone);

      item.appendChild(swatch);
      item.appendChild(label);
      legend.appendChild(item);
    });

    this.container.appendChild(legend);
  };

  /* ---- Tooltip helpers ---- */

  ZonesChart.prototype._showTooltip = function (event, zone, total) {
    this._tooltip.innerHTML =
      '<b style="color:' + zoneColor(zone.zone) + '">' + (zone.name || 'Zone ' + zone.zone) + '</b><br>' +
      'Time: ' + fmtDuration(zone.seconds) + '<br>' +
      'Percentage: ' + pct(zone.seconds, total);
    this._tooltip.style.opacity = '1';
    this._moveTooltip(event);
  };

  ZonesChart.prototype._moveTooltip = function (event) {
    var wrapRect = this._wrapper.getBoundingClientRect();
    var x = event.clientX - wrapRect.left + 12;
    var y = event.clientY - wrapRect.top - 10;
    var tipW = this._tooltip.offsetWidth;
    if (x + tipW > wrapRect.width) x = x - tipW - 24;
    this._tooltip.style.left = x + 'px';
    this._tooltip.style.top = y + 'px';
  };

  /* ---- Expose ---- */
  window.ZonesChart = ZonesChart;
})();

if (window.WKO5Registry) {
  WKO5Registry.registerFactory('intensity-dist', function (container) {
    var chart = new ZonesChart(container);
    container.innerHTML = '<div class="panel-placeholder">Select a ride to view intensity distribution.</div>';
    return {
      destroy: function () { chart.destroy(); },
      refresh: function () { /* no-op: requires activity-specific data from external caller */ },
      setData: function (data) { chart.render(data); },
    };
  });
}
