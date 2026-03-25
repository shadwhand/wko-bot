import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ShortPower } from './ShortPower'
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
    shortPower: null,
    loading: new Set(),
    errors: {},
  })
})

describe('ShortPower', () => {
  it('shows skeleton while loading', () => {
    useDataStore.setState({ loading: new Set(['shortPower']) })
    render(<ShortPower />)
    expect(document.querySelector('[class*="skeleton"]')).toBeTruthy()
  })

  it('shows error when fetch fails', () => {
    useDataStore.setState({ errors: { shortPower: 'Network error' } })
    render(<ShortPower />)
    expect(screen.getByText('Network error')).toBeTruthy()
  })

  it('shows empty state when no data', () => {
    render(<ShortPower />)
    expect(screen.getByText(/no short power/i)).toBeTruthy()
  })

  it('renders peak, typical, ratio, and diagnosis', () => {
    useDataStore.setState({
      shortPower: {
        peak: 520,
        typical: 410,
        ratio: 1.27,
        diagnosis: 'Good sprint but inconsistent repeatability.',
        efforts_analyzed: 24,
        message: 'Analyzed 24 efforts.',
      },
    })
    render(<ShortPower />)
    expect(screen.getByText('520')).toBeTruthy()
    expect(screen.getByText('410')).toBeTruthy()
    expect(screen.getByText('1.27')).toBeTruthy()
    expect(screen.getByText('Good sprint but inconsistent repeatability.')).toBeTruthy()
  })

  it('shows warning color for low ratio', () => {
    useDataStore.setState({
      shortPower: {
        peak: 400,
        typical: 380,
        ratio: 1.05,
        diagnosis: 'Very repeatable but may lack top end.',
        efforts_analyzed: 20,
        message: 'Analyzed 20 efforts.',
      },
    })
    render(<ShortPower />)
    expect(screen.getByText('1.05')).toBeTruthy()
  })
})
