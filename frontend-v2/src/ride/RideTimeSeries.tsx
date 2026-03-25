// frontend-v2/src/ride/RideTimeSeries.tsx
import { useRef, useCallback, useState } from 'react';
import * as d3 from 'd3';
import { ChartContainer } from '../shared/ChartContainer';
import { COLORS } from '../shared/tokens';
import { styleAxis, fmtElapsed, rollingAvg, findNearest } from '../shared/chart-utils';
import { IntervalCards } from './IntervalCards';
import type { RideRecord, RideInterval } from '../api/types';
import styles from './RideTimeSeries.module.css';

const MARGIN = { top: 8, right: 55, bottom: 36, left: 55 };

interface Channel {
  key: string;
  label: string;
  color: string;
  dataKey: keyof RideRecord;
  defaultOn: boolean;
}

const CHANNELS: Channel[] = [
  { key: 'power', label: 'Power', color: '#58a6ff', dataKey: 'power', defaultOn: true },
  { key: 'hr', label: 'HR', color: '#f85149', dataKey: 'heart_rate', defaultOn: true },
  { key: 'cadence', label: 'Cadence', color: '#3fb950', dataKey: 'cadence', defaultOn: false },
  { key: 'speed', label: 'Speed', color: '#d29922', dataKey: 'speed', defaultOn: false },
];

interface Props {
  records: RideRecord[];
  intervals: RideInterval[];
}

export function RideTimeSeries({ records, intervals }: Props) {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState<Record<string, boolean>>(
    Object.fromEntries(CHANNELS.map(c => [c.key, c.defaultOn]))
  );
  const [show30sAvg, setShow30sAvg] = useState(false);
  const [tooltipContent, setTooltipContent] = useState('');
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ left: 0, top: 0 });
  const [xScaleFn, setXScaleFn] = useState<((s: number) => number) | null>(null);

  const renderChart = useCallback(
    (svgEl: SVGSVGElement, width: number) => {
      const svg = d3.select(svgEl);
      svg.selectAll('*').remove();

      if (!records.length) return;

      const totalW = Math.max(width, 300);
      const totalH = Math.max(Math.min(totalW * 0.4, 400), 220);
      const w = totalW - MARGIN.left - MARGIN.right;
      const h = totalH - MARGIN.top - MARGIN.bottom;

      svg.attr('width', totalW).attr('height', totalH);

      // Clip path
      const clipId = 'ride-ts-clip';
      svg.append('defs').append('clipPath').attr('id', clipId)
        .append('rect')
        .attr('x', MARGIN.left).attr('y', MARGIN.top)
        .attr('width', w).attr('height', h);

      // X scale
      const xExtent = d3.extent(records, d => d.elapsed_seconds) as [number, number];
      const xScale = d3.scaleLinear().domain(xExtent).range([MARGIN.left, MARGIN.left + w]);
      setXScaleFn(() => (s: number) => xScale(s) - MARGIN.left);

      // Power Y scale (left)
      const pMax = d3.max(records, d => d.power) || 400;
      const yPower = d3.scaleLinear().domain([0, pMax * 1.1]).range([MARGIN.top + h, MARGIN.top]).nice();

      // HR Y scale (right)
      const hrExtent = d3.extent(records, d => d.heart_rate) as [number, number];
      const yHR = d3.scaleLinear()
        .domain([(hrExtent[0] || 80) - 10, (hrExtent[1] || 190) + 10])
        .range([MARGIN.top + h, MARGIN.top]).nice();

      // Cadence Y scale
      const cadMax = d3.max(records, d => d.cadence) || 120;
      const yCad = d3.scaleLinear().domain([0, cadMax * 1.2]).range([MARGIN.top + h, MARGIN.top]).nice();

      // Grid
      const gridColor = '#21262d';
      const powerTicks = yPower.ticks(5);
      powerTicks.forEach(tick => {
        svg.append('line')
          .attr('x1', MARGIN.left).attr('x2', MARGIN.left + w)
          .attr('y1', yPower(tick)).attr('y2', yPower(tick))
          .attr('stroke', gridColor).attr('stroke-width', 0.5);
      });

      // Interval shading
      const gIntervals = svg.append('g').attr('clip-path', `url(#${clipId})`);
      intervals.forEach(interval => {
        gIntervals.append('rect')
          .attr('x', xScale(interval.start))
          .attr('width', Math.max(0, xScale(interval.end) - xScale(interval.start)))
          .attr('y', MARGIN.top).attr('height', h)
          .attr('fill', COLORS.primary)
          .attr('opacity', 0.08);

        // Interval label
        const cx = (xScale(interval.start) + xScale(interval.end)) / 2;
        gIntervals.append('text')
          .attr('x', cx).attr('y', MARGIN.top + 14)
          .attr('text-anchor', 'middle')
          .attr('fill', COLORS.muted)
          .style('font-size', '0.6rem')
          .text(interval.avg_power ? `${interval.avg_power}W` : '');
      });

      // Lines
      const gLines = svg.append('g').attr('clip-path', `url(#${clipId})`);
      const lineGen = (yScale: d3.ScaleLinear<number, number>, key: keyof RideRecord) =>
        d3.line<RideRecord>()
          .defined(d => d[key] != null)
          .x(d => xScale(d.elapsed_seconds))
          .y(d => yScale(d[key] as number));

      // Power (with smoothing)
      if (visible.power) {
        const smoothed = rollingAvg(records.map(r => r.power), 5);
        const smoothedRecords = records.map((r, i) => ({ ...r, power: smoothed[i] }));

        gLines.append('path')
          .datum(smoothedRecords as RideRecord[])
          .attr('fill', 'none').attr('stroke', '#58a6ff')
          .attr('stroke-width', 1.5).attr('stroke-linejoin', 'round')
          .attr('d', lineGen(yPower, 'power') as unknown as string);

        if (show30sAvg) {
          const avg30 = rollingAvg(records.map(r => r.power), 30);
          const avg30Records = records.map((r, i) => ({ ...r, power: avg30[i] }));
          gLines.append('path')
            .datum(avg30Records as RideRecord[])
            .attr('fill', 'none').attr('stroke', COLORS.warning)
            .attr('stroke-width', 2).attr('stroke-linejoin', 'round')
            .attr('opacity', 0.85)
            .attr('d', lineGen(yPower, 'power') as unknown as string);
        }
      }

      // HR
      if (visible.hr) {
        gLines.append('path')
          .datum(records)
          .attr('fill', 'none').attr('stroke', '#f85149')
          .attr('stroke-width', 1).attr('stroke-linejoin', 'round')
          .attr('d', lineGen(yHR, 'heart_rate'));
      }

      // Cadence
      if (visible.cadence) {
        gLines.append('path')
          .datum(records)
          .attr('fill', 'none').attr('stroke', '#3fb950')
          .attr('stroke-width', 1).attr('stroke-linejoin', 'round')
          .attr('d', lineGen(yCad, 'cadence'));
      }

      // Speed (on its own scale, converted to km/h)
      if (visible.speed) {
        const speedMax = d3.max(records, d => d.speed ? d.speed * 3.6 : 0) || 60;
        const ySpeed = d3.scaleLinear().domain([0, speedMax * 1.1]).range([MARGIN.top + h, MARGIN.top]);
        const speedLine = d3.line<RideRecord>()
          .defined(d => d.speed != null)
          .x(d => xScale(d.elapsed_seconds))
          .y(d => ySpeed((d.speed || 0) * 3.6));
        gLines.append('path')
          .datum(records).attr('fill', 'none').attr('stroke', '#d29922')
          .attr('stroke-width', 1).attr('d', speedLine);
      }

      // Axes
      const xAxisG = svg.append('g')
        .attr('transform', `translate(0,${MARGIN.top + h})`)
        .call(d3.axisBottom(xScale).ticks(Math.max(w / 100, 3)).tickFormat(d => fmtElapsed(d as number)));
      styleAxis(xAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

      const yLeftG = svg.append('g')
        .attr('transform', `translate(${MARGIN.left},0)`)
        .call(d3.axisLeft(yPower).ticks(5));
      yLeftG.selectAll('text').style('fill', '#58a6ff').style('font-size', '0.7rem');
      yLeftG.selectAll('.domain, line').style('stroke', gridColor);

      const yRightG = svg.append('g')
        .attr('transform', `translate(${MARGIN.left + w},0)`)
        .call(d3.axisRight(yHR).ticks(5));
      yRightG.selectAll('text').style('fill', '#f85149').style('font-size', '0.7rem');
      yRightG.selectAll('.domain, line').style('stroke', gridColor);

      // Crosshair + hover
      const gCross = svg.append('g').attr('clip-path', `url(#${clipId})`).style('display', 'none');
      const crossLine = gCross.append('line')
        .attr('stroke', COLORS.muted).attr('stroke-width', 1).attr('stroke-dasharray', '3,3');

      svg.append('rect')
        .attr('x', MARGIN.left).attr('y', MARGIN.top)
        .attr('width', w).attr('height', h)
        .attr('fill', 'none').style('pointer-events', 'all')
        .on('mousemove', (event: MouseEvent) => {
          const [mx] = d3.pointer(event, svgEl);
          const elapsed = xScale.invert(mx);
          const d = findNearest(records, r => r.elapsed_seconds, elapsed);
          if (!d) return;

          const cx = xScale(d.elapsed_seconds);
          gCross.style('display', null);
          crossLine.attr('x1', cx).attr('x2', cx)
            .attr('y1', MARGIN.top).attr('y2', MARGIN.top + h);

          const lines = [fmtElapsed(d.elapsed_seconds)];
          if (d.power != null) lines.push(`Power: ${d.power} W`);
          if (d.heart_rate != null) lines.push(`HR: ${d.heart_rate} bpm`);
          if (d.cadence != null) lines.push(`Cadence: ${d.cadence} rpm`);
          if (d.speed != null) lines.push(`Speed: ${(d.speed * 3.6).toFixed(1)} km/h`);

          setTooltipContent(lines.join('\n'));
          setTooltipVisible(true);

          const containerW = svgEl.parentElement?.getBoundingClientRect().width ?? 800;
          let left = cx + 12;
          const tipW = tooltipRef.current?.offsetWidth ?? 120;
          if (left + tipW > containerW) left = cx - tipW - 12;
          setTooltipPos({ left, top: 10 });
        })
        .on('mouseleave', () => {
          gCross.style('display', 'none');
          setTooltipVisible(false);
        });
    },
    [records, intervals, visible, show30sAvg],
  );

  return (
    <div className={styles.wrapper}>
      <div className={styles.controls}>
        {CHANNELS.map(c => (
          <button
            key={c.key}
            className={styles.channelBtn}
            style={{
              border: `1px solid ${c.color}`,
              background: visible[c.key] ? c.color : 'transparent',
              color: visible[c.key] ? '#000' : c.color,
              cursor: c.key === 'power' ? 'default' : 'pointer',
            }}
            onClick={() => {
              if (c.key === 'power') return; // power always on
              setVisible(v => ({ ...v, [c.key]: !v[c.key] }));
            }}
          >
            {c.label}
          </button>
        ))}
        <button
          className={styles.channelBtn}
          style={{
            border: `1px solid ${COLORS.muted}`,
            background: show30sAvg ? COLORS.muted : 'transparent',
            color: show30sAvg ? 'var(--text-primary)' : COLORS.muted,
            marginLeft: 'auto',
          }}
          onClick={() => setShow30sAvg(v => !v)}
        >
          30s Avg
        </button>
      </div>

      {xScaleFn && intervals.length > 0 && (
        <IntervalCards intervals={intervals} xScale={xScaleFn} marginLeft={MARGIN.left} />
      )}

      <div style={{ position: 'relative' }}>
        <ChartContainer renderChart={renderChart} minHeight={220} aspectRatio={2.5} />
        <div
          ref={tooltipRef}
          className={`${styles.tooltip} ${tooltipVisible ? styles.visible : ''}`}
          style={{ left: tooltipPos.left, top: tooltipPos.top }}
        >
          {tooltipContent.split('\n').map((line, i) => <div key={i}>{line}</div>)}
        </div>
      </div>
    </div>
  );
}
