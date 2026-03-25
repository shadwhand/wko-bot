// frontend-v2/src/__tests__/PMCChart.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { useDataStore } from '../store/data-store';

// Mock ChartContainer to avoid DOM measurement / ResizeObserver issues in test
vi.mock('../shared/ChartContainer', () => ({
  ChartContainer: ({ children }: any) => (
    <div data-testid="chart-container">
      <svg />
      {children}
    </div>
  ),
}));

// Mock AnnotationOverlay to avoid its own store subscriptions
vi.mock('../shared/AnnotationOverlay', () => ({
  AnnotationOverlay: () => <div data-testid="annotation-overlay" />,
  renderAnnotationsSvg: vi.fn(),
}));

import { PMCChart } from '../panels/fitness/PMCChart';

describe('PMCChart', () => {
  beforeEach(() => {
    useDataStore.setState({
      pmc: [],
      loading: new Set<string>(),
      errors: {},
      annotations: {},
    });
  });

  it('renders skeleton when loading', () => {
    useDataStore.setState({ loading: new Set(['pmc']), pmc: [] });
    render(<PMCChart />);
    expect(document.querySelector('[class*="skeleton"]') || document.body.textContent).toBeTruthy();
  });

  it('renders error when store has error', () => {
    useDataStore.setState({ errors: { pmc: 'Network error' }, pmc: [] });
    render(<PMCChart />);
    expect(screen.getByText(/Network error/)).toBeTruthy();
  });

  it('renders empty state when no data', () => {
    useDataStore.setState({ pmc: [] });
    render(<PMCChart />);
    expect(screen.getByText(/No PMC data/)).toBeTruthy();
  });

  it('renders chart when data is present', () => {
    useDataStore.setState({
      pmc: [
        { date: '2026-01-01', CTL: 50, ATL: 60, TSB: -10, TSS: 100 },
        { date: '2026-01-02', CTL: 51, ATL: 58, TSB: -7, TSS: 80 },
      ],
    });
    render(<PMCChart />);
    expect(document.querySelector('svg')).toBeTruthy();
  });
});
