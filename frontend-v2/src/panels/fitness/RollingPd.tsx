// frontend-v2/src/panels/fitness/RollingPd.tsx
import { useCallback, useState } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { styleAxis, drawGridY } from '../../shared/chart-utils';
import { PanelSkeleton } from '../../shared/PanelSkeleton';
import { PanelError } from '../../shared/PanelError';
import { PanelEmpty } from '../../shared/PanelEmpty';
import { registerPanel } from '../../layout/PanelRegistry';
import type { RollingPdRow } from '../../api/types';
import styles from './RollingPd.module.css';

const CHART_HEIGHT = 200;
const MARGIN = { top: 10, right: 20, bottom: 30, left: 50 };

type SeriesKey = 'mFTP' | 'Pmax' | 'FRC' | 'TTE';

const SERIES: { key: SeriesKey; color: string; label: string }[] = [
  { key: 'mFTP', color: '#58a6ff', label: 'mFTP' },
  { key: 'Pmax', color: '#f778ba', label: 'Pmax' },
  { key: 'FRC', color: '#d29922', label: 'FRC' },
  { key: 'TTE', color: '#3fb950', label: 'TTE' },
];

export function RollingPd() {
  const rollingPd = useDataStore(s => s.rollingPd);
  const loading = useDataStore(s => s.loading.has('rollingPd'));
  const error = useDataStore(s => s.errors['rollingPd']);
  const [visible, setVisible] = useState<Record<string, boolean>>({
    mFTP: true, Pmax: false, FRC: false, TTE: false,
  });

  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!rollingPd || !rollingPd.length) return <PanelEmpty message="No rolling PD data" />;

  const toggleSeries = (key: string) => {
    setVisible(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.legend}>
        {SERIES.map(s => (
          <button
            key={s.key}
            className={styles.legendBtn}
            style={{
              border: `1px solid ${visible[s.key] ? s.color : 'var(--border, #30363d)'}`,
              background: visible[s.key] ? `${s.color}22` : 'transparent',
              color: visible[s.key] ? s.color : 'var(--text-muted, #484f58)',
            }}
            onClick={() => toggleSeries(s.key)}
          >
            {s.label}
          </button>
        ))}
      </div>
      <RollingPdInner data={rollingPd} visible={visible} />
    </div>
  );
}

interface ParsedPdRow extends RollingPdRow {
  _date: Date;
}

function RollingPdInner({ data, visible }: { data: RollingPdRow[]; visible: Record<string, boolean> }) {
  const renderChart = useCallback((svgEl: SVGSVGElement, width: number) => {
    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = CHART_HEIGHT;
    const totalH = innerH + MARGIN.top + MARGIN.bottom;
    svg.attr('width', width).attr('height', totalH);

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const parsed: ParsedPdRow[] = data.map(d => ({ ...d, _date: new Date(d.date) }))
      .sort((a, b) => a._date.getTime() - b._date.getTime());

    const x = d3.scaleTime()
      .domain(d3.extent(parsed, d => d._date) as [Date, Date])
      .range([0, innerW]);

    const activeKeys = SERIES.filter(s => visible[s.key]).map(s => s.key);
    if (!activeKeys.length) return;

    const allVals: number[] = [];
    activeKeys.forEach(key => {
      parsed.forEach(row => {
        const v = row[key];
        if (v != null) allVals.push(v);
      });
    });
    if (!allVals.length) return;

    const y = d3.scaleLinear()
      .domain([d3.min(allVals)! * 0.95, d3.max(allVals)! * 1.05])
      .range([innerH, 0]);

    drawGridY(g, y, innerW, 4);

    SERIES.forEach(s => {
      if (!visible[s.key]) return;
      const lineData = parsed.filter(d => d[s.key] != null);
      const line = d3.line<ParsedPdRow>()
        .x(d => x(d._date))
        .y(d => y(d[s.key]))
        .curve(d3.curveMonotoneX);

      g.append('path').datum(lineData).attr('d', line)
        .attr('fill', 'none').attr('stroke', s.color).attr('stroke-width', 2);
    });

    // Axes
    const xAxisG = g.append('g').attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %y') as unknown as (d: d3.NumberValue) => string));
    styleAxis(xAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    const yAxisG = g.append('g').call(d3.axisLeft(y).ticks(5));
    styleAxis(yAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);
  }, [data, visible]);

  return (
    <ChartContainer renderChart={renderChart} minHeight={CHART_HEIGHT + MARGIN.top + MARGIN.bottom} />
  );
}

// -- Panel Registration --
registerPanel({
  id: 'rolling-pd',
  label: 'Rolling PD Parameters',
  category: 'fitness',
  description: 'Multi-line time series of mFTP, Pmax, FRC, TTE with toggle legend',
  component: RollingPd,
  dataKeys: ['rollingPd'],
});
