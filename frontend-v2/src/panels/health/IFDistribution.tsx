// frontend-v2/src/panels/health/IFDistribution.tsx
import { useCallback } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { COLORS } from '../../shared/tokens';
import { styleAxis, ifZoneColor } from '../../shared/chart-utils';
import { PanelSkeleton } from '../../shared/PanelSkeleton';
import { PanelError } from '../../shared/PanelError';
import { PanelEmpty } from '../../shared/PanelEmpty';
import { registerPanel } from '../../layout/PanelRegistry';
import type { IfDistributionResponse } from '../../api/types';
import styles from './IFDistribution.module.css';

const CHART_HEIGHT = 220;
const MARGIN = { top: 20, right: 20, bottom: 35, left: 40 };

interface BarDatum {
  lo: number;
  hi: number;
  count: number;
}

function parseHistogram(data: IfDistributionResponse): BarDatum[] {
  const histogram = data.histogram || {};
  const barData: BarDatum[] = [];

  // Object form: {"0.40-0.45": 2, ...}
  for (const key of Object.keys(histogram)) {
    const parts = key.split('-');
    if (parts.length === 2) {
      barData.push({
        lo: parseFloat(parts[0]),
        hi: parseFloat(parts[1]),
        count: histogram[key],
      });
    }
  }
  return barData.sort((a, b) => a.lo - b.lo);
}

export function IFDistribution() {
  const ifDist = useDataStore(s => s.ifDistribution);
  const loading = useDataStore(s => s.loading.has('ifDistribution'));
  const error = useDataStore(s => s.errors['ifDistribution']);

  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!ifDist) return <PanelEmpty message="No IF distribution data" />;

  const barData = parseHistogram(ifDist);
  if (!barData.length) return <PanelEmpty message="No IF distribution data" />;

  return (
    <div className={styles.wrapper}>
      <IFDistributionInner barData={barData} data={ifDist} />
      <div className={styles.summary}>
        {ifDist.rides_analyzed != null && (
          <span>Rides: <span className="mono">{ifDist.rides_analyzed}</span></span>
        )}
        {ifDist.spread != null && (
          <span>Spread: <span className="mono">{ifDist.spread.toFixed(2)}</span></span>
        )}
        {ifDist.compressed != null && (
          <span style={{ color: ifDist.compressed ? COLORS.warning : COLORS.success }}>
            {ifDist.compressed ? 'Compressed' : 'Good spread'}
          </span>
        )}
      </div>
    </div>
  );
}

function IFDistributionInner({ barData, data }: { barData: BarDatum[]; data: IfDistributionResponse }) {
  const renderChart = useCallback((svgEl: SVGSVGElement, width: number) => {
    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = CHART_HEIGHT - MARGIN.top - MARGIN.bottom;
    svg.attr('width', width).attr('height', CHART_HEIGHT);

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const x = d3.scaleLinear()
      .domain([d3.min(barData, d => d.lo)!, d3.max(barData, d => d.hi)!])
      .range([0, innerW]);

    const y = d3.scaleLinear()
      .domain([0, d3.max(barData, d => d.count)! * 1.1])
      .range([innerH, 0]);

    // Bars colored by IF zone
    g.selectAll('rect.bar').data(barData).enter().append('rect')
      .attr('x', d => x(d.lo))
      .attr('width', d => Math.max(1, x(d.hi) - x(d.lo) - 1))
      .attr('y', d => y(d.count))
      .attr('height', d => innerH - y(d.count))
      .attr('fill', d => ifZoneColor(d.lo))
      .attr('rx', 2);

    // Floor marker line (red dashed)
    if (data.floor != null) {
      g.append('line')
        .attr('x1', x(data.floor)).attr('x2', x(data.floor))
        .attr('y1', 0).attr('y2', innerH)
        .attr('stroke', COLORS.danger).attr('stroke-width', 2)
        .attr('stroke-dasharray', '4,3');
      g.append('text')
        .attr('x', x(data.floor) + 4).attr('y', 12)
        .text(`Floor ${data.floor.toFixed(2)}`)
        .attr('fill', COLORS.danger).attr('font-size', '10px');
    }

    // Ceiling marker line (amber dashed)
    if (data.ceiling != null) {
      g.append('line')
        .attr('x1', x(data.ceiling)).attr('x2', x(data.ceiling))
        .attr('y1', 0).attr('y2', innerH)
        .attr('stroke', COLORS.warning).attr('stroke-width', 2)
        .attr('stroke-dasharray', '4,3');
      g.append('text')
        .attr('x', x(data.ceiling) + 4).attr('y', 12)
        .text(`Ceiling ${data.ceiling.toFixed(2)}`)
        .attr('fill', COLORS.warning).attr('font-size', '10px');
    }

    // Axes
    const xAxisG = g.append('g').attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(8).tickFormat(d => (d as number).toFixed(2)));
    styleAxis(xAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    const yAxisG = g.append('g').call(d3.axisLeft(y).ticks(5));
    styleAxis(yAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);
  }, [barData, data.floor, data.ceiling]);

  return (
    <ChartContainer renderChart={renderChart} minHeight={CHART_HEIGHT} />
  );
}

// -- Panel Registration --
registerPanel({
  id: 'if-distribution',
  label: 'IF Distribution',
  category: 'health',
  description: 'Intensity Factor histogram with zone colors and floor/ceiling markers',
  component: IFDistribution,
  dataKeys: ['ifDistribution'],
});
