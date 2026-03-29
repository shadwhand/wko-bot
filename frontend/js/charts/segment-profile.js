/**
 * Segment Profile / Altitude Chart
 *
 * Area chart showing altitude profile with colored segment overlays
 * indicating demand ratios. Uses D3 v7 (global `d3`).
 */

class SegmentProfileChart {
  constructor(container) {
    this.container = typeof container === 'string'
      ? document.querySelector(container)
      : container;
    this.svg = null;
    this.tooltip = null;
    this.data = null;
    this._resizeObserver = null;
    this._margin = { top: 32, right: 24, bottom: 64, left: 56 };
  }

  render(data) {
    this.data = data;
    this._clear();
    this._createTooltip();
    this._draw();
    this._observe();
  }

  update(data) {
    this.render(data);
  }

  destroy() {
    if (this._resizeObserver) this._resizeObserver.disconnect();
    this._clear();
    if (this.tooltip) { this.tooltip.remove(); this.tooltip = null; }
  }

  /* ------------------------------------------------------------------ */

  _clear() {
    if (this.svg) { this.svg.remove(); this.svg = null; }
    d3.select(this.container).selectAll('.sp-summary-bar').remove();
  }

  _createTooltip() {
    if (this.tooltip) return;
    this.tooltip = d3.select(document.body)
      .append('div')
      .attr('class', 'sp-tooltip')
      .style('position', 'absolute')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('background', 'var(--bg-secondary)')
      .style('border', '1px solid var(--border)')
      .style('border-radius', '6px')
      .style('padding', '10px 14px')
      .style('font-size', '0.8rem')
      .style('color', 'var(--text-primary)')
      .style('box-shadow', '0 4px 12px rgba(0,0,0,0.4)')
      .style('z-index', '1000')
      .style('max-width', '220px')
      .style('line-height', '1.5');
  }

  _observe() {
    if (this._resizeObserver) this._resizeObserver.disconnect();
    var lastW = 0;
    this._resizeObserver = new ResizeObserver(() => {
      var w = Math.floor(this.container.getBoundingClientRect().width);
      if (w === lastW || !this.data) return;
      lastW = w;
      this._draw();
    });
    this._resizeObserver.observe(this.container);
  }

  _draw() {
    var data = this.data;
    if (!data || !data.elevation_profile || !data.elevation_profile.length) return;

    /* Remove previous SVG (redraw) */
    d3.select(this.container).selectAll('svg').remove();
    d3.select(this.container).selectAll('.sp-summary-bar').remove();

    var m = this._margin;
    var rect = this.container.getBoundingClientRect();
    var width = rect.width;
    var height = Math.max(260, Math.min(rect.width * 0.45, 400));
    var innerW = width - m.left - m.right;
    var innerH = height - m.top - m.bottom;

    if (innerW < 40 || innerH < 40) return;

    /* Scales */
    var xExtent = [0, data.total_km || d3.max(data.elevation_profile, function (d) { return d.km; })];
    var altitudes = data.elevation_profile.map(function (d) { return d.altitude; });
    var yMin = d3.min(altitudes);
    var yMax = d3.max(altitudes);
    var yPad = (yMax - yMin) * 0.1 || 50;

    var x = d3.scaleLinear().domain(xExtent).range([0, innerW]);
    var y = d3.scaleLinear().domain([yMin - yPad, yMax + yPad]).range([innerH, 0]);

    /* SVG */
    this.svg = d3.select(this.container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('display', 'block');

    var g = this.svg.append('g')
      .attr('transform', 'translate(' + m.left + ',' + m.top + ')');

    /* Grid lines */
    g.append('g')
      .attr('class', 'sp-grid-y')
      .call(d3.axisLeft(y).ticks(5).tickSize(-innerW).tickFormat(''))
      .selectAll('line')
      .attr('stroke', 'var(--chart-grid)')
      .attr('stroke-dasharray', '2,3');
    g.selectAll('.sp-grid-y .domain').remove();

    /* Segment overlays (behind altitude) */
    var segments = data.segments || [];
    g.selectAll('.sp-segment-overlay')
      .data(segments)
      .join('rect')
      .attr('class', 'sp-segment-overlay')
      .attr('x', function (d) { return x(d.start_km); })
      .attr('y', 0)
      .attr('width', function (d) { return Math.max(0, x(d.end_km) - x(d.start_km)); })
      .attr('height', innerH)
      .attr('fill', function (d) { return _demandColor(d.demand_ratio); })
      .attr('opacity', function (d) { return _demandOpacity(d.demand_ratio); });

    /* Area */
    var area = d3.area()
      .x(function (d) { return x(d.km); })
      .y0(innerH)
      .y1(function (d) { return y(d.altitude); })
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(data.elevation_profile)
      .attr('d', area)
      .attr('fill', 'var(--text-muted)')
      .attr('fill-opacity', 0.15);

    /* Top line */
    var line = d3.line()
      .x(function (d) { return x(d.km); })
      .y(function (d) { return y(d.altitude); })
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(data.elevation_profile)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', 'var(--text-secondary)')
      .attr('stroke-width', 1.5);

    /* Segment type labels above profile */
    var MIN_LABEL_PX = 50;
    g.selectAll('.sp-seg-label')
      .data(segments.filter(function (d) {
        return (x(d.end_km) - x(d.start_km)) > MIN_LABEL_PX;
      }))
      .join('text')
      .attr('class', 'sp-seg-label')
      .attr('x', function (d) { return x((d.start_km + d.end_km) / 2); })
      .attr('y', -6)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--text-muted)')
      .attr('font-size', '0.7rem')
      .text(function (d) {
        if (d.type === 'climb') return 'Climb ' + d.avg_grade.toFixed(1) + '%';
        if (d.type === 'descent') return 'Descent';
        return 'Flat';
      });

    /* Axes */
    g.append('g')
      .attr('transform', 'translate(0,' + innerH + ')')
      .call(d3.axisBottom(x).ticks(Math.min(10, innerW / 60)).tickFormat(function (d) { return d + ' km'; }))
      .selectAll('text')
      .attr('fill', 'var(--text-muted)')
      .attr('font-size', '0.7rem');

    g.append('g')
      .call(d3.axisLeft(y).ticks(5).tickFormat(function (d) { return d + ' m'; }))
      .selectAll('text')
      .attr('fill', 'var(--text-muted)')
      .attr('font-size', '0.7rem');

    g.selectAll('.domain').attr('stroke', 'var(--border)');
    g.selectAll('.tick line').attr('stroke', 'var(--border)');

    /* Hover overlay */
    var self = this;
    var bisect = d3.bisector(function (d) { return d.km; }).left;

    var hoverLine = g.append('line')
      .attr('class', 'sp-hover-line')
      .attr('y1', 0).attr('y2', innerH)
      .attr('stroke', 'var(--accent)')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,3')
      .style('opacity', 0);

    var hoverDot = g.append('circle')
      .attr('r', 4)
      .attr('fill', 'var(--accent)')
      .style('opacity', 0);

    g.append('rect')
      .attr('width', innerW)
      .attr('height', innerH)
      .attr('fill', 'transparent')
      .on('mousemove', function (event) {
        var coords = d3.pointer(event);
        var km = x.invert(coords[0]);
        var i = bisect(data.elevation_profile, km, 1);
        var d0 = data.elevation_profile[i - 1];
        var d1 = data.elevation_profile[i] || d0;
        var d = (km - d0.km > d1.km - km) ? d1 : d0;

        hoverLine.attr('x1', x(d.km)).attr('x2', x(d.km)).style('opacity', 1);
        hoverDot.attr('cx', x(d.km)).attr('cy', y(d.altitude)).style('opacity', 1);

        /* Find matching segment */
        var seg = null;
        for (var s = 0; s < segments.length; s++) {
          if (km >= segments[s].start_km && km < segments[s].end_km) {
            seg = segments[s];
            break;
          }
        }

        var html = '<strong>' + d.km.toFixed(1) + ' km</strong> &mdash; ' + Math.round(d.altitude) + ' m';
        if (seg) {
          html += '<br><span style="color:var(--text-secondary)">' + _capitalize(seg.type) + ' ' + seg.avg_grade.toFixed(1) + '%</span>';
          html += '<br>Power: <span class="mono">' + seg.power_required + ' W</span>';
          html += '<br>Demand: <span style="color:' + _demandTextColor(seg.demand_ratio) + '">' + (seg.demand_ratio * 100).toFixed(0) + '%</span>';
        }

        self.tooltip
          .html(html)
          .style('opacity', 1)
          .style('left', (event.pageX + 14) + 'px')
          .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseleave', function () {
        hoverLine.style('opacity', 0);
        hoverDot.style('opacity', 0);
        self.tooltip.style('opacity', 0);
      });

    /* Summary bar */
    this._drawSummary(data, segments);
  }

  _drawSummary(data, segments) {
    var hardest = segments.reduce(function (best, s) {
      return (!best || s.demand_ratio > best.demand_ratio) ? s : best;
    }, null);

    var bar = d3.select(this.container)
      .append('div')
      .attr('class', 'sp-summary-bar')
      .style('display', 'flex')
      .style('gap', '24px')
      .style('padding', '10px 0 0')
      .style('font-size', '0.8rem')
      .style('color', 'var(--text-secondary)')
      .style('flex-wrap', 'wrap');

    bar.append('span').html('Distance: <strong style="color:var(--text-primary)">' + (data.total_km || 0) + ' km</strong>');
    bar.append('span').html('Elevation: <strong style="color:var(--text-primary)">' + (data.total_elevation || 0) + ' m</strong>');
    if (hardest) {
      var color = _demandTextColor(hardest.demand_ratio);
      bar.append('span').html(
        'Hardest: <strong style="color:' + color + '">' +
        _capitalize(hardest.type) + ' ' + hardest.avg_grade.toFixed(1) + '% @ ' +
        (hardest.demand_ratio * 100).toFixed(0) + '% demand</strong>'
      );
    }
  }
}

/* Helpers */
function _demandColor(ratio) {
  if (ratio > 1.0) return 'var(--danger)';
  if (ratio >= 0.95) return 'var(--danger)';
  if (ratio >= 0.85) return 'var(--warning)';
  return 'var(--success)';
}

function _demandOpacity(ratio) {
  if (ratio > 1.0) return 0.4;
  if (ratio >= 0.95) return 0.25;
  if (ratio >= 0.85) return 0.2;
  return 0.15;
}

function _demandTextColor(ratio) {
  if (ratio >= 0.95) return 'var(--danger)';
  if (ratio >= 0.85) return 'var(--warning)';
  return 'var(--success)';
}

function _capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
}

/* Export */
window.SegmentProfileChart = SegmentProfileChart;

if (window.WKO5Registry) {
  WKO5Registry.registerFactory('segment-profile', function (container) {
    if (!container.id) container.id = 'segment-panel-' + Date.now();
    var chart = new SegmentProfileChart('#' + container.id);
    container.innerHTML = '<div class="panel-placeholder">Select a ride to view segment profile.</div>';
    return {
      destroy: function () { chart.destroy(); },
      refresh: function () { /* no-op: requires activity_id from external caller */ },
      setData: function (data) { chart.render(data); },
    };
  });
}
