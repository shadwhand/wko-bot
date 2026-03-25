import { describe, it, expect, beforeEach } from 'vitest';
import { useDataStore } from '../store/data-store';
import type { Annotation } from '../api/types';

describe('Annotation store actions', () => {
  beforeEach(() => {
    // Reset annotations between tests
    useDataStore.getState().clearAnnotations();
  });

  it('addAnnotation adds to correct panelId', () => {
    const annotation: Annotation = {
      id: 'test-1',
      source: 'claude',
      type: 'region',
      x: ['2026-01-01', '2026-01-15'],
      label: 'CTL plateau',
      color: 'red',
      timestamp: new Date().toISOString(),
    };

    useDataStore.getState().addAnnotation('pmc-chart', annotation);

    const state = useDataStore.getState();
    expect(state.annotations['pmc-chart']).toHaveLength(1);
    expect(state.annotations['pmc-chart'][0].label).toBe('CTL plateau');
  });

  it('addAnnotation appends multiple annotations', () => {
    const a1: Annotation = {
      id: 'a1', source: 'claude', type: 'line',
      x: '2026-02-01', label: 'Event', color: 'blue',
      timestamp: new Date().toISOString(),
    };
    const a2: Annotation = {
      id: 'a2', source: 'claude', type: 'point',
      x: '2026-03-01', y: 50, label: 'Peak', color: 'green',
      timestamp: new Date().toISOString(),
    };

    useDataStore.getState().addAnnotation('pmc-chart', a1);
    useDataStore.getState().addAnnotation('pmc-chart', a2);

    expect(useDataStore.getState().annotations['pmc-chart']).toHaveLength(2);
  });

  it('clearAnnotations with panelId clears only that panel', () => {
    const a: Annotation = {
      id: 'a1', source: 'claude', type: 'line',
      x: '2026-01-01', label: 'Test', color: 'red',
      timestamp: new Date().toISOString(),
    };
    useDataStore.getState().addAnnotation('pmc-chart', a);
    useDataStore.getState().addAnnotation('other-chart', { ...a, id: 'a2' });

    useDataStore.getState().clearAnnotations('pmc-chart');

    expect(useDataStore.getState().annotations['pmc-chart'] || []).toHaveLength(0);
    expect(useDataStore.getState().annotations['other-chart']).toHaveLength(1);
  });

  it('clearAnnotations without panelId clears all', () => {
    const a: Annotation = {
      id: 'a1', source: 'claude', type: 'line',
      x: '2026-01-01', label: 'Test', color: 'red',
      timestamp: new Date().toISOString(),
    };
    useDataStore.getState().addAnnotation('pmc-chart', a);
    useDataStore.getState().addAnnotation('other-chart', { ...a, id: 'a2' });

    useDataStore.getState().clearAnnotations();

    expect(Object.keys(useDataStore.getState().annotations)).toHaveLength(0);
  });

  it('truncates labels longer than 200 chars', () => {
    const longLabel = 'x'.repeat(250);
    const a: Annotation = {
      id: 'a1', source: 'claude', type: 'line',
      x: '2026-01-01', label: longLabel, color: 'red',
      timestamp: new Date().toISOString(),
    };

    useDataStore.getState().addAnnotation('pmc-chart', a);

    const stored = useDataStore.getState().annotations['pmc-chart'][0];
    expect(stored.label.length).toBeLessThanOrEqual(203); // 200 + '...'
  });
});
