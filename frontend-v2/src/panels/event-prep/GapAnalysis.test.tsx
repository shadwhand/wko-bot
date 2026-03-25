import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { GapAnalysis } from './GapAnalysis'

vi.mock('../../store/data-store', () => ({
  useDataStore: vi.fn(),
}))

import { useDataStore } from '../../store/data-store'
const mockUseDataStore = vi.mocked(useDataStore)

describe('GapAnalysis', () => {
  it('shows "select a route" when no route selected', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        selectedRouteId: null,
        routeDetail: {},
        loading: new Set(),
        errors: {},
      })
    )
    render(<GapAnalysis />)
    expect(screen.getByText(/select a route/i)).toBeInTheDocument()
  })

  it('shows feasible result', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        selectedRouteId: 1,
        routeDetail: {
          1: {
            gap_analysis: { feasible: true, bottleneck: null, margin: 0.12, message: 'Good to go' },
          },
        },
        loading: new Set(),
        errors: {},
      })
    )
    render(<GapAnalysis />)
    expect(screen.getByText('Feasible')).toBeInTheDocument()
    expect(screen.getByText(/12\.0%/)).toBeInTheDocument()
  })

  it('shows not feasible with bottleneck', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        selectedRouteId: 1,
        routeDetail: {
          1: {
            gap_analysis: { feasible: false, bottleneck: '5min power', margin: -0.08 },
          },
        },
        loading: new Set(),
        errors: {},
      })
    )
    render(<GapAnalysis />)
    expect(screen.getByText('Not Feasible')).toBeInTheDocument()
    expect(screen.getByText(/5min power/)).toBeInTheDocument()
  })
})
