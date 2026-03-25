// frontend-v2/src/shared/AnnotationOverlay.tsx
import { useState } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../store/data-store';
import type { Annotation } from '../api/types';
import styles from './AnnotationOverlay.module.css';

interface AnnotationOverlayProps {
  panelId: string;
  annotations: Annotation[];
}

/**
 * Renders annotation overlays on top of a D3 chart.
 *
 * Toolbar with count badge, hide/show toggle, and clear-all button.
 * Callout cards with severity badge, label, source ("Claude"), and dismiss button.
 *
 * The D3 SVG overlays are rendered separately via renderAnnotationsSvg(),
 * which charts call directly from their render callback.
 */
export function AnnotationOverlay({ panelId, annotations }: AnnotationOverlayProps) {
  const clearAnnotations = useDataStore(s => s.clearAnnotations);
  const [hidden, setHidden] = useState(false);

  if (!annotations.length) return null;

  const removeAnnotation = (annotationId: string) => {
    // Remove single annotation by filtering
    const store = useDataStore.getState();
    const current = store.annotations[panelId] || [];
    const filtered = current.filter(a => a.id !== annotationId);
    // We need to set the filtered list back. Since the store only has
    // addAnnotation and clearAnnotations, we clear and re-add.
    store.clearAnnotations(panelId);
    filtered.forEach(a => store.addAnnotation(panelId, a));
  };

  return (
    <div>
      {/* Toolbar */}
      <div className={styles.toolbar}>
        <span className={styles.badge}>{annotations.length}</span>
        <span>annotation{annotations.length !== 1 ? 's' : ''}</span>
        <button
          className={styles.toolbarBtn}
          onClick={() => setHidden(h => !h)}
        >
          {hidden ? 'Show' : 'Hide'}
        </button>
        <button
          className={styles.toolbarBtn}
          onClick={() => clearAnnotations(panelId)}
        >
          Clear all
        </button>
      </div>

      {/* Callout cards */}
      {!hidden && annotations.map(ann => (
        <AnnotationCallout
          key={ann.id}
          annotation={ann}
          onDismiss={() => removeAnnotation(ann.id)}
        />
      ))}
    </div>
  );
}

interface CalloutProps {
  annotation: Annotation;
  onDismiss: () => void;
}

function AnnotationCallout({ annotation, onDismiss }: CalloutProps) {
  const severity = (annotation as Record<string, unknown>).severity as string || 'info';

  return (
    <div className={styles.calloutCard}>
      <button className={styles.dismissBtn} onClick={onDismiss} aria-label="Dismiss">
        x
      </button>
      <div>
        <span className={`${styles.calloutSeverity} ${styles[severity] || styles.info}`}>
          {severity}
        </span>
        {/* Always textContent, never innerHTML -- XSS prevention */}
        <span>{annotation.label}</span>
      </div>
      <div className={styles.calloutSource}>
        {annotation.source === 'claude' ? 'Claude' : 'User'} --{' '}
        {new Date(annotation.timestamp).toLocaleTimeString()}
      </div>
    </div>
  );
}

/**
 * D3 SVG annotation layer -- renders directly into the chart SVG.
 * Call this function from inside a chart's render callback, passing the
 * D3 content group and scales.
 *
 * Usage inside a chart component's renderChart():
 *   renderAnnotationsSvg(contentGroup, annotations, xScale, yScale, innerH);
 */
export function renderAnnotationsSvg(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  annotations: Annotation[],
  xScale: d3.ScaleTime<number, number>,
  yScaleRight: d3.ScaleLinear<number, number> | null,
  innerH: number
): void {
  const parseDate = d3.timeParse('%Y-%m-%d');

  annotations.forEach(ann => {
    const color = ann.color || '#58a6ff';

    if (ann.type === 'region' && Array.isArray(ann.x) && ann.x.length === 2) {
      const x0 = parseDate(ann.x[0]);
      const x1 = parseDate(ann.x[1]);
      if (!x0 || !x1) return;

      const px0 = xScale(x0);
      const px1 = xScale(x1);

      // Shaded region
      g.append('rect')
        .attr('x', Math.min(px0, px1))
        .attr('y', 0)
        .attr('width', Math.abs(px1 - px0))
        .attr('height', innerH)
        .attr('fill', color)
        .attr('opacity', 0.12)
        .attr('class', 'annotation-region');

      // Dashed borders
      [px0, px1].forEach(px => {
        g.append('line')
          .attr('x1', px).attr('x2', px)
          .attr('y1', 0).attr('y2', innerH)
          .attr('stroke', color)
          .attr('stroke-width', 1)
          .attr('stroke-dasharray', '4,3')
          .attr('opacity', 0.6);
      });
    }

    if (ann.type === 'line' && typeof ann.x === 'string') {
      const date = parseDate(ann.x);
      if (!date) return;
      const px = xScale(date);

      g.append('line')
        .attr('x1', px).attr('x2', px)
        .attr('y1', 0).attr('y2', innerH)
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .attr('opacity', 0.8)
        .attr('class', 'annotation-line');
    }

    if ((ann as Record<string, unknown>).type === 'dashed' && typeof ann.x === 'string') {
      const date = parseDate(ann.x);
      if (!date) return;
      const px = xScale(date);

      g.append('line')
        .attr('x1', px).attr('x2', px)
        .attr('y1', 0).attr('y2', innerH)
        .attr('stroke', color)
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '6,4')
        .attr('opacity', 0.7)
        .attr('class', 'annotation-dashed');
    }

    if (ann.type === 'point' && typeof ann.x === 'string' && ann.y != null) {
      const date = parseDate(ann.x);
      if (!date || !yScaleRight) return;
      const px = xScale(date);
      const py = yScaleRight(ann.y);

      g.append('circle')
        .attr('cx', px).attr('cy', py)
        .attr('r', 5)
        .attr('fill', color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .attr('opacity', 0.9)
        .attr('class', 'annotation-point');
    }
  });
}
