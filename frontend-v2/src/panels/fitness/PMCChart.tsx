// frontend-v2/src/panels/fitness/PMCChart.tsx
import { useRef, useCallback, useState } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { AnnotationOverlay, renderAnnotationsSvg } from '../../shared/AnnotationOverlay';
import { COLORS, AXIS } from '../../shared/tokens';
import { styleAxis, drawGridY, tooltipLeft, findNearest } from '../../shared/chart-utils';
import { PanelSkeleton } from '../../shared/PanelSkeleton';
import { PanelError } from '../../shared/PanelError';
import { PanelEmpty } from '../../shared/PanelEmpty';
import { registerPanel } from '../../layout/PanelRegistry';
import type { PMCRow, Annotation } from '../../api/types';
import styles from './PMCChart.module.css';

const PANEL_ID = 'pmc-chart';
const CHART_HEIGHT = 280;
const MARGIN = { top: 20, right: 50, bottom: 30, left: 50 };

/** Chart line colors consistent with the original PMC chart */
const LINE_COLORS = {
  ctl: COLORS.ctl,
  atl: COLORS.atl,
  tsb: COLORS.tsb,
} as const;

export function PMCChart() {
  const pmc = useDataStore(s => s.pmc);
  const loading = useDataStore(s => s.loading.has('pmc'));
  const error = useDataStore(s => s.errors['pmc']);
  const annotations = useDataStore(s => s.annotations[PANEL_ID] || []);
  const addAnnotation = useDataStore(s => s.addAnnotation);

  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!pmc || !pmc.length) return <PanelEmpty message="No PMC data available" />;

  const pushTestAnnotation = () => {
    addAnnotation(PANEL_ID, {
      id: `test-${Date.now()}`,
      source: 'claude',
      type: 'region',
      x: [
        // Use recent dates from the PMC data
        pmc[Math.max(0, pmc.length - 60)]?.date || '2026-01-01',
        pmc[Math.max(0, pmc.length - 45)]?.date || '2026-01-15',
      ],
      label: 'CTL plateau — recovery block detected',
      color: '#f85149',
      timestamp: new Date().toISOString(),
    } as Annotation);
  };

  return (
    <div className={styles.wrapper}>
      <AnnotationOverlay panelId={PANEL_ID} annotations={annotations} />
      <PMCChartInner data={pmc} annotations={annotations} />
      {/* Temporary test button — remove before production */}
      <button
        onClick={pushTestAnnotation}
        style={{
          position: 'absolute', bottom: 8, right: 8,
          fontSize: '0.7rem', padding: '3px 8px',
          background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
          borderRadius: 4, color: 'var(--text-secondary)', cursor: 'pointer',
        }}
      >
        + Test Annotation
      </button>
    </div>
  );
}

interface PMCChartInnerProps {
  data: PMCRow[];
  annotations: Annotation[];
}

interface ParsedRow {
  _date: Date;
  ctl: number;
  atl: number;
  tsb: number;
  tss: number;
}

function PMCChartInner({ data, annotations }: PMCChartInnerProps) {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const annotationsRef = useRef(annotations);
  annotationsRef.current = annotations;
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

    // Parse dates
    const parseDate = d3.timeParse('%Y-%m-%d');
    const parsed: ParsedRow[] = data.map(d => ({
      _date: parseDate(d.date)!,
      ctl: d.CTL ?? 0,
      atl: d.ATL ?? 0,
      tsb: d.TSB ?? 0,
      tss: d.TSS ?? 0,
    })).filter(d => d._date != null)
      .sort((a, b) => a._date.getTime() - b._date.getTime());

    if (!parsed.length) return;

    // Clip path
    const clipId = 'pmc-clip';
    const defs = svg.append('defs');
    defs.append('clipPath').attr('id', clipId)
      .append('rect').attr('width', innerW).attr('height', innerH);

    const g = svg.append('g')
      .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    // Scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(parsed, d => d._date) as [Date, Date])
      .range([0, innerW]);

    const maxLeft = d3.max(parsed, d => Math.max(d.ctl, d.atl, d.tss)) || 100;
    const yScaleLeft = d3.scaleLinear()
      .domain([0, maxLeft * 1.1])
      .range([innerH, 0]);

    const tsbExtent = d3.extent(parsed, d => d.tsb) as [number, number];
    const tsbPad = Math.max(
      Math.abs(tsbExtent[0] || 0),
      Math.abs(tsbExtent[1] || 0)
    ) * 1.2 || 30;
    const yScaleRight = d3.scaleLinear()
      .domain([-tsbPad, tsbPad])
      .range([innerH, 0]);

    const content = g.append('g').attr('clip-path', `url(#${clipId})`);

    // Grid
    drawGridY(g, yScaleLeft, innerW);

    // TSB zero line
    const zeroY = yScaleRight(0);
    if (zeroY >= 0 && zeroY <= innerH) {
      content.append('line')
        .attr('x1', 0).attr('x2', innerW)
        .attr('y1', zeroY).attr('y2', zeroY)
        .style('stroke', COLORS.muted)
        .style('stroke-dasharray', '4,3')
        .style('stroke-width', 1);
    }

    // TSB area -- positive (green shading above zero)
    const areaPositive = d3.area<ParsedRow>()
      .x(d => xScale(d._date))
      .y0(() => yScaleRight(0))
      .y1(d => yScaleRight(Math.max(0, d.tsb)))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(parsed)
      .attr('d', areaPositive)
      .style('fill', COLORS.success)
      .style('opacity', 0.12);

    // TSB area -- negative (red shading below zero)
    const areaNegative = d3.area<ParsedRow>()
      .x(d => xScale(d._date))
      .y0(() => yScaleRight(0))
      .y1(d => yScaleRight(Math.min(0, d.tsb)))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(parsed)
      .attr('d', areaNegative)
      .style('fill', COLORS.danger)
      .style('opacity', 0.10);

    // CTL line (blue)
    const ctlLine = d3.line<ParsedRow>()
      .x(d => xScale(d._date))
      .y(d => yScaleLeft(d.ctl))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(parsed)
      .attr('d', ctlLine)
      .style('fill', 'none')
      .style('stroke', LINE_COLORS.ctl)
      .style('stroke-width', 2);

    // ATL line (red/pink)
    const atlLine = d3.line<ParsedRow>()
      .x(d => xScale(d._date))
      .y(d => yScaleLeft(d.atl))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(parsed)
      .attr('d', atlLine)
      .style('fill', 'none')
      .style('stroke', LINE_COLORS.atl)
      .style('stroke-width', 1.5);

    // TSB dashed line (green)
    const tsbLine = d3.line<ParsedRow>()
      .x(d => xScale(d._date))
      .y(d => yScaleRight(d.tsb))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(parsed)
      .attr('d', tsbLine)
      .style('fill', 'none')
      .style('stroke', LINE_COLORS.tsb)
      .style('stroke-width', 1.5)
      .style('stroke-dasharray', '6,3');

    // Legend
    const legend = g.append('g').attr('transform', 'translate(0,-6)');
    const labels = [
      { text: 'CTL', color: LINE_COLORS.ctl },
      { text: 'ATL', color: LINE_COLORS.atl },
      { text: 'TSB', color: LINE_COLORS.tsb },
    ];
    let xOff = 0;
    labels.forEach(l => {
      legend.append('rect')
        .attr('x', xOff).attr('y', -8)
        .attr('width', 12).attr('height', 3)
        .style('fill', l.color);
      legend.append('text')
        .attr('x', xOff + 16).attr('y', -3)
        .text(l.text)
        .style('fill', AXIS.fontColor)
        .style('font-size', '11px');
      xOff += 55;
    });

    // X axis
    const xAxisG = g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(xScale).ticks(8));
    styleAxis(xAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    // Y axis left (CTL/ATL/TSS)
    const yAxisLeftG = g.append('g').call(d3.axisLeft(yScaleLeft).ticks(6));
    styleAxis(yAxisLeftG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    // Y axis right (TSB)
    const yAxisRightG = g.append('g')
      .attr('transform', `translate(${innerW},0)`)
      .call(d3.axisRight(yScaleRight).ticks(6));
    styleAxis(yAxisRightG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    // Annotation SVG overlays (via shared renderAnnotationsSvg helper)
    if (annotationsRef.current.length > 0) {
      const annotGroup = content.append('g').attr('class', 'annotations');
      renderAnnotationsSvg(
        annotGroup as unknown as d3.Selection<SVGGElement, unknown, null, undefined>,
        annotationsRef.current,
        xScale,
        yScaleRight,
        innerH,
      );
    }

    // Crosshair + hover overlay
    const crosshair = content.append('line')
      .attr('y1', 0).attr('y2', innerH)
      .style('stroke', COLORS.muted)
      .style('stroke-width', 1)
      .style('display', 'none');

    content.append('rect')
      .attr('width', innerW).attr('height', innerH)
      .style('fill', 'none').style('pointer-events', 'all')
      .on('mousemove', (event: MouseEvent) => {
        const [mx] = d3.pointer(event);
        const x0 = xScale.invert(mx);
        const d = findNearest(parsed, p => p._date.getTime(), x0.getTime());
        if (!d) return;

        const cx = xScale(d._date);
        crosshair.attr('x1', cx).attr('x2', cx).style('display', null);

        const fmt = d3.timeFormat('%Y-%m-%d');
        setTooltipContent(
          `${fmt(d._date)}\nCTL: ${d.ctl.toFixed(1)}\nATL: ${d.atl.toFixed(1)}\nTSB: ${d.tsb.toFixed(1)}\nTSS: ${d.tss ?? '\u2014'}`
        );
        setTooltipVisible(true);

        const tipW = tooltipRef.current?.offsetWidth ?? 100;
        const containerW = svgEl.parentElement?.getBoundingClientRect().width ?? 800;
        const left = tooltipLeft(cx, MARGIN.left, tipW, containerW);
        setTooltipPos({ left, top: MARGIN.top + 10 });
      })
      .on('mouseleave', () => {
        crosshair.style('display', 'none');
        setTooltipVisible(false);
      });

    // Store scales on SVG element for annotation overlay to read
    (svgEl as unknown as Record<string, unknown>).__scales = {
      xScale, yScaleLeft, yScaleRight, margin: MARGIN, innerW, innerH,
    };
  }, [data, annotations]);

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
  id: 'pmc-chart',
  label: 'Performance Management Chart',
  category: 'fitness',
  description: 'CTL, ATL, TSB over time \u2014 fitness/fatigue/form tracking',
  component: PMCChart,
  dataKeys: ['pmc'],
});
