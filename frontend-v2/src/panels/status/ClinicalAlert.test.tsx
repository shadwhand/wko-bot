import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ClinicalAlert } from './ClinicalAlert'
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

describe('ClinicalAlert', () => {
  it('shows skeleton while loading', () => {
    useDataStore.setState({ loading: new Set(['clinicalFlags']) })
    render(<ClinicalAlert />)
    expect(document.querySelector('[class*="skeleton"]')).toBeTruthy()
  })

  it('shows danger when flags have danger status', () => {
    useDataStore.setState({
      clinicalFlags: {
        flags: [
          { name: 'if_floor', status: 'danger', value: 0.82, threshold: 0.70 },
        ],
      },
    })
    render(<ClinicalAlert />)
    expect(screen.getByText(/1 critical alert/i)).toBeTruthy()
  })

  it('shows warning count', () => {
    useDataStore.setState({
      clinicalFlags: {
        flags: [
          { name: 'if_floor', status: 'warning', value: 0.72, threshold: 0.70 },
          { name: 'panic_training', status: 'warning', value: 600, threshold: 500 },
        ],
      },
    })
    render(<ClinicalAlert />)
    expect(screen.getByText(/2 warnings/i)).toBeTruthy()
  })

  it('shows all-clear when all flags ok', () => {
    useDataStore.setState({
      clinicalFlags: {
        flags: [{ name: 'test', status: 'ok', value: 0.5, threshold: 0.7 }],
      },
    })
    render(<ClinicalAlert />)
    expect(screen.getByText(/all clinical checks passed/i)).toBeTruthy()
  })

  it('shows empty state when no data', () => {
    render(<ClinicalAlert />)
    expect(screen.getByText(/no clinical data/i)).toBeTruthy()
  })
})
