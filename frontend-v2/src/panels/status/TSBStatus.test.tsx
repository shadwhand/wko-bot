import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TSBStatus } from './TSBStatus'
import { useDataStore } from '../../store/data-store'

// Mock the API client (store imports it)
vi.mock('../../api/client', () => ({
  getFitness: vi.fn(),
  getPmc: vi.fn(),
  getClinicalFlags: vi.fn(),
  getProfile: vi.fn(),
  getConfig: vi.fn(),
  getModel: vi.fn(),
  getActivities: vi.fn(),
  getRollingFtp: vi.fn(),
  getFtpGrowth: vi.fn(),
  getRollingPdProfile: vi.fn(),
  getIfDistribution: vi.fn(),
  getFreshBaseline: vi.fn(),
  getShortPowerConsistency: vi.fn(),
  getPerformanceTrend: vi.fn(),
  getHealth: vi.fn(),
  getRide: vi.fn(),
}))

beforeEach(() => {
  useDataStore.setState({
    fitness: null,
    loading: new Set(),
    errors: {},
  })
})

describe('TSBStatus', () => {
  it('renders loading skeleton when fitness is loading', () => {
    useDataStore.setState({ loading: new Set(['fitness']) })
    render(<TSBStatus />)
    // PanelSkeleton renders bars
    expect(document.querySelector('[class*="skeleton"]')).toBeTruthy()
  })

  it('renders error with message', () => {
    useDataStore.setState({ errors: { fitness: 'Network error' } })
    render(<TSBStatus />)
    expect(screen.getByText('Network error')).toBeTruthy()
  })

  it('renders empty state when no data', () => {
    render(<TSBStatus />)
    expect(screen.getByText('No fitness data available')).toBeTruthy()
  })

  it('renders TSB, CTL, ATL from store', () => {
    useDataStore.setState({
      fitness: { CTL: 55, ATL: 60, TSB: -5, date: '2026-03-24' },
    })
    render(<TSBStatus />)
    expect(screen.getByText('-5')).toBeTruthy()
    expect(screen.getByText('TSB')).toBeTruthy()
    expect(screen.getByText('55')).toBeTruthy()
    expect(screen.getByText('CTL')).toBeTruthy()
    expect(screen.getByText('60')).toBeTruthy()
    expect(screen.getByText('ATL')).toBeTruthy()
  })

  it('shows "Neutral" label for TSB between -10 and 5', () => {
    useDataStore.setState({
      fitness: { CTL: 55, ATL: 60, TSB: -5, date: '2026-03-24' },
    })
    render(<TSBStatus />)
    expect(screen.getByText('Neutral')).toBeTruthy()
  })

  it('shows "Fresh" label for TSB > 5', () => {
    useDataStore.setState({
      fitness: { CTL: 55, ATL: 40, TSB: 15, date: '2026-03-24' },
    })
    render(<TSBStatus />)
    expect(screen.getByText('Fresh')).toBeTruthy()
  })
})
