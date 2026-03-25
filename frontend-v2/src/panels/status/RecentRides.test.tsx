import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RecentRides } from './RecentRides'
import { useDataStore } from '../../store/data-store'

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
    activities: [],
    loading: new Set(),
    errors: {},
  })
})

describe('RecentRides', () => {
  it('renders loading skeleton when activities are loading', () => {
    useDataStore.setState({ loading: new Set(['activities']) })
    render(<RecentRides />)
    expect(document.querySelector('[class*="skeleton"]')).toBeTruthy()
  })

  it('renders error with message', () => {
    useDataStore.setState({ errors: { activities: 'Network error' } })
    render(<RecentRides />)
    expect(screen.getByText('Network error')).toBeTruthy()
  })

  it('renders empty state when no rides', () => {
    render(<RecentRides />)
    expect(screen.getByText('No recent rides')).toBeTruthy()
  })

  it('renders a table of recent rides', () => {
    useDataStore.setState({
      activities: [
        {
          id: 1,
          start_time: '2026-03-22T08:00:00Z',
          sub_sport: 'road',
          total_elapsed_time: 5400,
          normalized_power: 220,
          training_stress_score: 85,
        },
        {
          id: 2,
          start_time: '2026-03-20T07:00:00Z',
          sub_sport: null,
          total_elapsed_time: 3600,
          normalized_power: null,
          training_stress_score: null,
        },
      ],
    })
    render(<RecentRides />)
    expect(screen.getByText('220W')).toBeTruthy()
    expect(screen.getByText('85')).toBeTruthy()
    expect(screen.getByText('1h 30m')).toBeTruthy()
    expect(screen.getByText('ride')).toBeTruthy()
  })
})
