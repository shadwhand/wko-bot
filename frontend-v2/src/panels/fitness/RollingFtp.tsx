// frontend-v2/src/panels/fitness/RollingFtp.tsx
import { useRef, useCallback, useState } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { COLORS } from '../../shared/tokens';
import { styleAxis, drawGridY, tooltipLeft, findNearest } from '../../shared/chart-utils';
import { PanelSkeleton } from '../../shared/PanelSkeleton';
import { PanelError } from '../../shared/PanelError';
import { PanelEmpty } from '../../shared/PanelEmpty';
import { registerPanel } from '../../layout/PanelRegistry';
import type { RollingFtpRow } from '../../api/types';
import styles from './RollingFtp.module.css';

const CHART_HEIGHT = 180;
const MARGIN = { top: 10, right: 20, bottom: 30, left: 50 };

export function RollingFtp() {
  const rollingFtp = useDataStore(s => s.rollingFtp);
  const loading = useDataStore(s => s.loading.has('rollingFtp'));
  const error = useDataStore(s => s.errors['rollingFtp']);

  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!rollingFtp || !rollingFtp.length) return <PanelEmpty message="No rolling FTP data" />;

  const latest = rollingFtp[rollingFtp.length - 1];

  return (
    <div className={styles.wrapper}>
      <div className={styles.bigNumber}>
        <div className={styles.value}>{Math.round(latest.mFTP)} W</div>
        <div className={styles.label}>Current mFTP</div>
      </div>
      <RollingFtpInner data={rollingFtp} />
    </div>
  );
}

interface ParsedRow extends RollingFtpRow {
  _date: Date;
}

function RollingFtpInner({ data }: { data: RollingFtpRow[] }) {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltipContent, setTooltipContent] = useState('');
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ left: 0, top: 0 });

  const renderChart = useCallback((svgEl: SVGSVGElement, width: number) => {
    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = CHART_HEIGHT;
    const totalH = innerH + MARGIN.top + MARGIN.bottom;
    svg.attr('width', width).attr('height', totalH);

    const parsed: ParsedRow[] = data.map(d => ({
      ...d,
      _date: new Date(d.date),
    })).sort((a, b) => a._date.getTime() - b._date.getTime());

    if (!parsed.length) return;

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    // Scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(parsed, d => d._date) as [Date, Date])
      .range([0, innerW]);

    const yExtent = d3.extent(parsed, d => d.mFTP) as [number, number];
    const yPad = (yExtent[1] - yExtent[0]) * 0.15 || 10;
    const yScale = d3.scaleLinear()
      .domain([yExtent[0] - yPad, yExtent[1] + yPad])
      .range([innerH, 0]);

    // Grid
    drawGridY(g, yScale, innerW, 4);

    // Area fill
    const area = d3.area<ParsedRow>()
      .x(d => xScale(d._date))
      .y0(innerH)
      .y1(d => yScale(d.mFTP))
      .curve(d3.curveMonotoneX);

    g.append('path').datum(parsed).attr('d', area)
      .style('fill', COLORS.primary).style('opacity', 0.08);

    // Line
    const line = d3.line<ParsedRow>()
      .x(d => xScale(d._date))
      .y(d => yScale(d.mFTP))
      .curve(d3.curveMonotoneX);

    g.append('path').datum(parsed).attr('d', line)
      .style('fill', 'none')
      .style('stroke', COLORS.primary).style('stroke-width', 2);

    // Trend line (linear regression)
    if (parsed.length > 2) {
      const xs = parsed.map((_, i) => i);
      const ys = parsed.map(d => d.mFTP);
      const n = xs.length;
      const sumX = xs.reduce((a, b) => a + b, 0);
      const sumY = ys.reduce((a, b) => a + b, 0);
      const sumXY = xs.reduce((a, x, i) => a + x * ys[i], 0);
      const sumXX = xs.reduce((a, x) => a + x * x, 0);
      const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
      const intercept = (sumY - slope * sumX) / n;

      const trendLine = d3.line<ParsedRow>()
        .x(d => xScale(d._date))
        .y((_, i) => yScale(slope * i + intercept))
        .curve(d3.curveLinear);

      g.append('path').datum(parsed).attr('d', trendLine)
        .style('fill', 'none')
        .style('stroke', COLORS.muted)
        .style('stroke-width', 1)
        .style('stroke-dasharray', '4,3');
    }

    // Axes
    const xAxisG = g.append('g').attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(xScale).ticks(6).tickFormat(d3.timeFormat('%b %y') as unknown as (d: d3.NumberValue) => string));
    styleAxis(xAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    const yAxisG = g.append('g')
      .call(d3.axisLeft(yScale).ticks(4).tickFormat(d => `${d}W`));
    styleAxis(yAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    // Hover crosshair
    const crosshair = g.append('line')
      .attr('y1', 0).attr('y2', innerH)
      .style('stroke', COLORS.muted).style('stroke-width', 1)
      .style('display', 'none');

    g.append('rect')
      .attr('width', innerW).attr('height', innerH)
      .style('fill', 'none').style('pointer-events', 'all')
      .on('mousemove', (event: MouseEvent) => {
        const [mx] = d3.pointer(event);
        const x0 = xScale.invert(mx);
        const d = findNearest(parsed, p => p._date.getTime(), x0.getTime());
        if (!d) return;

        const cx = xScale(d._date);
        crosshair.attr('x1', cx).attr('x2', cx).style('display', null);
        setTooltipContent(`${d3.timeFormat('%Y-%m-%d')(d._date)}\nmFTP: ${Math.round(d.mFTP)} W`);
        setTooltipVisible(true);

        const tipW = tooltipRef.current?.offsetWidth ?? 100;
        const containerW = svgEl.parentElement?.getBoundingClientRect().width ?? 800;
        setTooltipPos({ left: tooltipLeft(cx, MARGIN.left, tipW, containerW), top: MARGIN.top + 10 });
      })
      .on('mouseleave', () => {
        crosshair.style('display', 'none');
        setTooltipVisible(false);
      });
  }, [data]);

  return (
    <>
      <ChartContainer renderChart={renderChart} minHeight={CHART_HEIGHT + MARGIN.top + MARGIN.bottom} />
      <div
        ref={tooltipRef}
        className={`${styles.tooltip} ${tooltipVisible ? styles.visible : ''}`}
        style={{ left: tooltipPos.left, top: tooltipPos.top }}
      >
        {tooltipContent.split('\n').map((line, i) => (
          <div key={i}>{line}</div>
        ))}
      </div>
    </>
  );
}

// -- Panel Registration --
registerPanel({
  id: 'rolling-ftp',
  label: 'Rolling FTP',
  category: 'fitness',
  description: 'mFTP time series with big number display + trend line',
  component: RollingFtp,
  dataKeys: ['rollingFtp'],
});
