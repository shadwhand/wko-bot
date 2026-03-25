import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PowerProfile } from './PowerProfile'
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
    profile: null,
    loading: new Set(),
    errors: {},
  })
})

describe('PowerProfile', () => {
  it('shows skeleton while loading', () => {
    useDataStore.setState({ loading: new Set(['profile']) })
    render(<PowerProfile />)
    expect(document.querySelector('[class*="skeleton"]')).toBeTruthy()
  })

  it('shows error when fetch fails', () => {
    useDataStore.setState({ errors: { profile: 'Network error' } })
    render(<PowerProfile />)
    expect(screen.getByText('Network error')).toBeTruthy()
  })

  it('shows empty state when no data', () => {
    render(<PowerProfile />)
    expect(screen.getByText(/no power profile/i)).toBeTruthy()
  })

  it('renders W and W/kg for each duration', () => {
    useDataStore.setState({
      profile: {
        profile: {
          watts: { '5s': 1100, '1min': 480, '5min': 340, '20min': 290, '60min': 270 },
          wkg: { '5s': 14.5, '1min': 6.3, '5min': 4.5, '20min': 3.8, '60min': 3.6 },
        },
        ranking: {
          '5s': 'very_good',
          '1min': 'good',
          '5min': 'good',
          '20min': 'moderate',
          '60min': 'moderate',
        },
        strengths_limiters: { strengths: [], limiters: [] },
      },
    })
    render(<PowerProfile />)
    expect(screen.getByText('1100W')).toBeTruthy()
    expect(screen.getByText('14.50 W/kg')).toBeTruthy()
    expect(screen.getByText('Very Good')).toBeTruthy()
    expect(screen.getByText('480W')).toBeTruthy()
    expect(screen.getByText('6.30 W/kg')).toBeTruthy()
    expect(screen.getByText('270W')).toBeTruthy()
  })

  it('renders all five duration labels', () => {
    useDataStore.setState({
      profile: {
        profile: {
          watts: { '5s': 1100, '1min': 480, '5min': 340, '20min': 290, '60min': 270 },
          wkg: { '5s': 14.5, '1min': 6.3, '5min': 4.5, '20min': 3.8, '60min': 3.6 },
        },
        ranking: {},
        strengths_limiters: { strengths: [], limiters: [] },
      },
    })
    render(<PowerProfile />)
    expect(screen.getByText('5s')).toBeTruthy()
    expect(screen.getByText('1min')).toBeTruthy()
    expect(screen.getByText('5min')).toBeTruthy()
    expect(screen.getByText('20min')).toBeTruthy()
    expect(screen.getByText('60min')).toBeTruthy()
  })
})
