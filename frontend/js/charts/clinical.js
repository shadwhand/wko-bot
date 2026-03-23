/**
 * Clinical Dashboard — Traffic-light indicator grid
 *
 * Data-driven DOM component using D3 data joins to display
 * health/safety flags with status indicators.
 */

class ClinicalDashboard {
  constructor(container) {
    this.container = typeof container === 'string'
      ? document.querySelector(container)
      : container;
    this.data = null;
    this.tooltip = null;
    this._resizeObserver = null;
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
    d3.select(this.container).selectAll('.cd-wrapper').remove();
  }

  _createTooltip() {
    if (this.tooltip) return;
    this.tooltip = d3.select(document.body)
      .append('div')
      .attr('class', 'cd-tooltip')
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
      .style('max-width', '260px')
      .style('line-height', '1.5');
  }

  _observe() {
    if (this._resizeObserver) this._resizeObserver.disconnect();
    this._resizeObserver = new ResizeObserver(() => {
      if (this.data) this._updateColumns();
    });
    this._resizeObserver.observe(this.container);
  }

  _updateColumns() {
    var grid = this.container.querySelector('.cd-grid');
    if (!grid) return;
    var w = this.container.getBoundingClientRect().width;
    if (w < 400) {
      grid.style.gridTemplateColumns = '1fr';
    } else if (w < 680) {
      grid.style.gridTemplateColumns = 'repeat(2, 1fr)';
    } else {
      grid.style.gridTemplateColumns = 'repeat(3, 1fr)';
    }
  }

  _draw() {
    var data = this.data;
    if (!data || !data.flags || !data.flags.length) return;

    var flags = data.flags;
    var self = this;

    var wrapper = d3.select(this.container)
      .append('div')
      .attr('class', 'cd-wrapper');

    /* Summary header */
    var dangerCount = flags.filter(function (f) { return f.status === 'danger'; }).length;
    var warnCount = flags.filter(function (f) { return f.status === 'warning'; }).length;

    var summary = wrapper.append('div')
      .attr('class', 'cd-summary')
      .style('margin-bottom', '14px')
      .style('padding', '8px 14px')
      .style('border-radius', '6px')
      .style('font-size', '0.85rem')
      .style('font-weight', '600')
      .style('display', 'flex')
      .style('align-items', 'center')
      .style('gap', '8px');

    if (dangerCount === 0 && warnCount === 0) {
      summary
        .style('background', 'rgba(63,185,80,0.08)')
        .style('border', '1px solid rgba(63,185,80,0.2)')
        .style('color', 'var(--success)');
      summary.append('span')
        .style('width', '10px').style('height', '10px')
        .style('border-radius', '50%')
        .style('background', 'var(--success)')
        .style('display', 'inline-block')
        .style('flex-shrink', '0');
      summary.append('span').text('All Clear');
    } else {
      var parts = [];
      if (warnCount > 0) parts.push(warnCount + ' warning' + (warnCount > 1 ? 's' : ''));
      if (dangerCount > 0) parts.push(dangerCount + ' alert' + (dangerCount > 1 ? 's' : ''));
      var summaryColor = dangerCount > 0 ? 'var(--danger)' : 'var(--warning)';
      var summaryBg = dangerCount > 0
        ? 'rgba(248,81,73,0.08)'
        : 'rgba(210,153,34,0.08)';
      var summaryBorder = dangerCount > 0
        ? 'rgba(248,81,73,0.2)'
        : 'rgba(210,153,34,0.2)';

      summary
        .style('background', summaryBg)
        .style('border', '1px solid ' + summaryBorder)
        .style('color', summaryColor);
      summary.append('span')
        .style('width', '10px').style('height', '10px')
        .style('border-radius', '50%')
        .style('background', summaryColor)
        .style('display', 'inline-block')
        .style('flex-shrink', '0');
      summary.append('span').text(parts.join(', '));
    }

    /* Card grid */
    var grid = wrapper.append('div')
      .attr('class', 'cd-grid')
      .style('display', 'grid')
      .style('gap', '12px');

    var cards = grid.selectAll('.cd-card')
      .data(flags, function (d) { return d.name; })
      .join('div')
      .attr('class', function (d) { return 'cd-card cd-card--' + d.status; })
      .style('background', function (d) {
        if (d.status === 'danger') return 'rgba(248,81,73,0.06)';
        if (d.status === 'warning') return 'rgba(210,153,34,0.06)';
        return 'var(--bg-secondary)';
      })
      .style('border', function (d) {
        if (d.status === 'danger') return '1px solid rgba(248,81,73,0.3)';
        if (d.status === 'warning') return '1px solid rgba(210,153,34,0.2)';
        return '1px solid var(--border)';
      })
      .style('border-radius', '8px')
      .style('padding', '14px 16px')
      .style('cursor', 'default')
      .style('transition', 'border-color 0.2s ease, background 0.2s ease')
      .on('mouseenter', function (event, d) {
        self.tooltip
          .html('<strong>Threshold</strong><br>' + d.threshold)
          .style('opacity', 1)
          .style('left', (event.pageX + 14) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mousemove', function (event) {
        self.tooltip
          .style('left', (event.pageX + 14) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseleave', function () {
        self.tooltip.style('opacity', 0);
      });

    /* Card internals */
    var header = cards.append('div')
      .style('display', 'flex')
      .style('align-items', 'center')
      .style('gap', '10px')
      .style('margin-bottom', '6px');

    /* Status dot */
    header.append('span')
      .attr('class', function (d) { return 'cd-dot' + (d.status === 'danger' ? ' cd-dot--pulse' : ''); })
      .style('width', '12px')
      .style('height', '12px')
      .style('border-radius', '50%')
      .style('flex-shrink', '0')
      .style('display', 'inline-block')
      .style('background', function (d) { return _statusColor(d.status); });

    /* Flag name */
    header.append('span')
      .style('font-weight', '600')
      .style('font-size', '0.85rem')
      .style('color', 'var(--text-primary)')
      .text(function (d) { return d.name; });

    /* Value */
    cards.append('div')
      .style('font-family', "'SF Mono','Fira Code','Cascadia Code',Menlo,Consolas,monospace")
      .style('font-size', '0.9rem')
      .style('color', function (d) { return _statusColor(d.status); })
      .style('margin-bottom', '4px')
      .text(function (d) { return d.value; });

    /* Detail */
    cards.append('div')
      .style('font-size', '0.75rem')
      .style('color', 'var(--text-muted)')
      .style('line-height', '1.4')
      .text(function (d) { return d.detail; });

    /* Inject pulse animation if not already present */
    if (!document.getElementById('cd-pulse-style')) {
      var style = document.createElement('style');
      style.id = 'cd-pulse-style';
      style.textContent = [
        '@keyframes cd-pulse {',
        '  0%, 100% { box-shadow: 0 0 0 0 rgba(248,81,73,0.5); }',
        '  50% { box-shadow: 0 0 0 5px rgba(248,81,73,0); }',
        '}',
        '.cd-dot--pulse { animation: cd-pulse 2s ease-in-out infinite; }'
      ].join('\n');
      document.head.appendChild(style);
    }

    this._updateColumns();
  }
}

function _statusColor(status) {
  if (status === 'danger') return 'var(--danger)';
  if (status === 'warning') return 'var(--warning)';
  return 'var(--success)';
}

/* Export */
window.ClinicalDashboard = ClinicalDashboard;

if (window.WKO5Registry) {
  WKO5Registry.registerFactory('clinical-flags', function (container, api) {
    var chart = new ClinicalDashboard(container);
    api.getClinicalFlags().then(function (data) {
      if (data) chart.render(data);
    }).catch(function (err) {
      container.innerHTML = '<div class="panel-error">Unable to load: ' + err.message + '</div>';
    });
    return {
      destroy: function () { chart.destroy(); },
      refresh: function () {
        api.getClinicalFlags().then(function (data) {
          if (data) chart.render(data);
        });
      },
    };
  });
}
