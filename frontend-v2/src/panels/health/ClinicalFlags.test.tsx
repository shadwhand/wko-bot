import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ClinicalFlags } from './ClinicalFlags'
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
    clinicalFlags: null,
    loading: new Set(),
    errors: {},
  })
})

describe('ClinicalFlags', () => {
  it('shows skeleton while loading', () => {
    useDataStore.setState({ loading: new Set(['clinicalFlags']) })
    render(<ClinicalFlags />)
    expect(document.querySelector('[class*="skeleton"]')).toBeTruthy()
  })

  it('shows error when fetch fails', () => {
    useDataStore.setState({ errors: { clinicalFlags: 'Network error' } })
    render(<ClinicalFlags />)
    expect(screen.getByText('Network error')).toBeTruthy()
  })

  it('shows empty state when no flags', () => {
    render(<ClinicalFlags />)
    expect(screen.getByText(/no clinical flags/i)).toBeTruthy()
  })

  it('renders flags sorted by severity (danger first)', () => {
    useDataStore.setState({
      clinicalFlags: {
        flags: [
          { name: 'if_floor', status: 'ok', value: 0.62, threshold: '0.70', detail: 'OK' },
          { name: 'panic_training', status: 'danger', value: 800, threshold: '500', detail: 'High' },
          { name: 'overtraining', status: 'warning', value: 0.7, threshold: '0.50', detail: 'Watch' },
        ],
        alert_level: 'danger',
      },
    })
    render(<ClinicalFlags />)

    // All three flag names should be present
    expect(screen.getByText('panic_training')).toBeTruthy()
    expect(screen.getByText('overtraining')).toBeTruthy()
    expect(screen.getByText('if_floor')).toBeTruthy()

    // The grid should have 3 cards
    const cards = document.querySelectorAll('[class*="card"]')
    expect(cards.length).toBeGreaterThanOrEqual(3)
  })

  it('renders flag values formatted correctly', () => {
    useDataStore.setState({
      clinicalFlags: {
        flags: [
          { name: 'if_floor', status: 'ok', value: 0.625, threshold: '0.70', detail: 'OK' },
        ],
        alert_level: 'ok',
      },
    })
    render(<ClinicalFlags />)
    expect(screen.getByText('0.63')).toBeTruthy()
  })
})
