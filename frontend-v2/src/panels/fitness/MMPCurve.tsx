// frontend-v2/src/panels/fitness/MMPCurve.tsx
import { useRef, useCallback, useState } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { COLORS } from '../../shared/tokens';
import {
  styleAxis,
  drawGridY,
  tooltipLeft,
  fmtDurationShort,
  fmtDuration,
  findNearest,
} from '../../shared/chart-utils';
import { PanelSkeleton } from '../../shared/PanelSkeleton';
import { PanelError } from '../../shared/PanelError';
import { PanelEmpty } from '../../shared/PanelEmpty';
import { registerPanel } from '../../layout/PanelRegistry';
import type { ModelResult } from '../../api/types';
import styles from './MMPCurve.module.css';

const CHART_HEIGHT = 280;
const MARGIN = { top: 20, right: 20, bottom: 30, left: 55 };

const RECENCY_OPTIONS = [
  { label: '30d', days: 30 },
  { label: '60d', days: 60 },
  { label: '90d', days: 90 },
  { label: '1yr', days: 365 },
  { label: 'All', days: 0 },
] as const;

// MMP power zone boundaries (seconds)
const ZONES = [
  { label: 'NM', from: 1, to: 15, color: COLORS.danger },
  { label: 'AN', from: 15, to: 120, color: COLORS.warning },
  { label: 'VO2', from: 120, to: 480, color: COLORS.primary },
  { label: 'TH', from: 480, to: 1200, color: COLORS.success },
  { label: 'END', from: 1200, to: Infinity, color: COLORS.muted },
];

export function MMPCurve() {
  const model = useDataStore(s => s.model);
  const loading = useDataStore(s => s.loading.has('model'));
  const error = useDataStore(s => s.errors['model']);
  const [recency, setRecency] = useState(90);

  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!model || !model.mmp || !model.mmp.length) {
    return <PanelEmpty message="No MMP data available" />;
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.controls}>
        {RECENCY_OPTIONS.map(opt => (
          <button
            key={opt.label}
            className={`${styles.toggleBtn} ${recency === opt.days ? styles.active : ''}`}
            onClick={() => setRecency(opt.days)}
          >
            {opt.label}
          </button>
        ))}
      </div>
      <MMPCurveInner model={model} recencyDays={recency} />
    </div>
  );
}

interface MMPCurveInnerProps {
  model: ModelResult;
  recencyDays: number;
}

function MMPCurveInner({ model, recencyDays: _recencyDays }: MMPCurveInnerProps) {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltipContent, setTooltipContent] = useState('');
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ left: 0, top: 0 });

  const mmpData: [number, number][] = model.mmp || [];

  const renderChart = useCallback((svgEl: SVGSVGElement, width: number) => {
    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();

    if (!mmpData.length) return;

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = CHART_HEIGHT;
    const totalH = innerH + MARGIN.top + MARGIN.bottom;
    svg.attr('width', width).attr('height', totalH);

    const clipId = 'mmp-clip';
    svg.append('defs').append('clipPath').attr('id', clipId)
      .append('rect').attr('width', innerW).attr('height', innerH);

    const g = svg.append('g')
      .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);
    const content = g.append('g').attr('clip-path', `url(#${clipId})`);

    // Scales
    const maxDur = d3.max(mmpData, d => d[0]) || 3600;
    const xScale = d3.scaleLog()
      .domain([1, maxDur])
      .range([0, innerW])
      .clamp(true);

    const maxW = d3.max(mmpData, d => d[1]) || 1000;
    const yScale = d3.scaleLinear()
      .domain([0, maxW * 1.08])
      .range([innerH, 0]);

    // Zone backgrounds
    ZONES.forEach(z => {
      const zoneTo = Math.min(z.to, maxDur);
      const x1 = xScale(Math.max(z.from, 1));
      const x2 = xScale(zoneTo);
      if (x2 <= x1) return;

      content.append('rect')
        .attr('x', x1).attr('y', 0)
        .attr('width', x2 - x1).attr('height', innerH)
        .style('fill', z.color).style('opacity', 0.04);

      content.append('text')
        .attr('x', (x1 + x2) / 2).attr('y', 14)
        .attr('text-anchor', 'middle')
        .style('fill', COLORS.muted)
        .style('font-size', '9px').style('opacity', 0.6)
        .text(z.label);
    });

    // Grid
    drawGridY(g, yScale, innerW);

    // MMP area fill
    const area = d3.area<[number, number]>()
      .x(d => xScale(d[0]))
      .y0(innerH)
      .y1(d => yScale(d[1]))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(mmpData)
      .attr('d', area)
      .style('fill', COLORS.primary)
      .style('opacity', 0.12);

    // MMP line
    const line = d3.line<[number, number]>()
      .x(d => xScale(d[0]))
      .y(d => yScale(d[1]))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(mmpData)
      .attr('d', line)
      .style('fill', 'none')
      .style('stroke', COLORS.primary)
      .style('stroke-width', 2);

    // PD model overlay
    if (model.mFTP != null && model.FRC != null && model.Pmax != null) {
      const tau = model.tau ?? 0;
      const t0 = model.t0 ?? 0;
      const frc = model.FRC;
      const mftp = model.mFTP;
      const pmax = model.Pmax;

      const points: [number, number][] = [];
      for (let t = 1; t <= maxDur; t = Math.ceil(t * 1.05) || t + 1) {
        let watts: number;
        if (t <= tau) {
          watts = pmax;
        } else {
          watts = (frc * 1000) / (t + t0) + mftp;
        }
        if (watts > 0) points.push([t, watts]);
      }

      const modelLine = d3.line<[number, number]>()
        .x(d => xScale(d[0]))
        .y(d => yScale(d[1]))
        .curve(d3.curveMonotoneX);

      content.append('path')
        .datum(points)
        .attr('d', modelLine)
        .style('fill', 'none')
        .style('stroke', COLORS.warning)
        .style('stroke-width', 1.5)
        .style('stroke-dasharray', '6,3')
        .style('opacity', 0.8);
    }

    // X axis (log scale, custom ticks)
    const tickValues = [1, 5, 30, 60, 300, 1200, 3600].filter(t => t <= maxDur);
    const xAxisG = g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(
        d3.axisBottom(xScale)
          .tickValues(tickValues)
          .tickFormat(d => fmtDurationShort(d as number))
      );
    styleAxis(xAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    // Y axis
    const yAxisG = g.append('g').call(d3.axisLeft(yScale).ticks(6));
    styleAxis(yAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    // Y axis label
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerH / 2).attr('y', -40)
      .attr('text-anchor', 'middle')
      .style('fill', COLORS.muted).style('font-size', '11px')
      .text('Watts');

    // Hover
    const crosshair = content.append('line')
      .attr('y1', 0).attr('y2', innerH)
      .style('stroke', COLORS.muted).style('stroke-width', 1)
      .style('display', 'none');

    const dot = content.append('circle')
      .attr('r', 4).style('fill', COLORS.primary).style('display', 'none');

    content.append('rect')
      .attr('width', innerW).attr('height', innerH)
      .style('fill', 'none').style('pointer-events', 'all')
      .on('mousemove', (event: MouseEvent) => {
        const [mx] = d3.pointer(event);
        const durAtMouse = xScale.invert(mx);
        const d = findNearest(mmpData, p => p[0], durAtMouse);
        if (!d) return;

        const cx = xScale(d[0]);
        const cy = yScale(d[1]);
        crosshair.attr('x1', cx).attr('x2', cx).style('display', null);
        dot.attr('cx', cx).attr('cy', cy).style('display', null);

        setTooltipContent(`${fmtDuration(d[0])}\n${d[1]} W`);
        setTooltipVisible(true);

        const tipW = tooltipRef.current?.offsetWidth ?? 80;
        const containerW = svgEl.parentElement?.getBoundingClientRect().width ?? 800;
        setTooltipPos({
          left: tooltipLeft(cx, MARGIN.left, tipW, containerW),
          top: MARGIN.top + 10,
        });
      })
      .on('mouseleave', () => {
        crosshair.style('display', 'none');
        dot.style('display', 'none');
        setTooltipVisible(false);
      });
  }, [mmpData, model]);

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

// ── Panel Registration ──────────────────────────────────────────────
registerPanel({
  id: 'mmp-curve',
  label: 'MMP / Power-Duration Curve',
  category: 'fitness',
  description: 'Mean Maximal Power envelope + PD model overlay',
  component: MMPCurve,
  dataKeys: ['model'],
});
