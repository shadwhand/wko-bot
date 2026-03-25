import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PhaseTimeline } from './PhaseTimeline'

vi.mock('../../store/data-store', () => ({
  useDataStore: vi.fn(),
}))

import { useDataStore } from '../../store/data-store'
const mockUseDataStore = vi.mocked(useDataStore)

describe('PhaseTimeline', () => {
  it('shows empty when no phase data', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        clinicalFlags: null,
        loading: new Set(),
        errors: {},
      })
    )
    render(<PhaseTimeline />)
    expect(screen.getByText(/phase detection not available/i)).toBeInTheDocument()
  })

  it('renders detected phase with confidence', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        clinicalFlags: {
          flags: [],
          alert_level: 'ok',
          detected_phase: {
            phase: 'build',
            confidence: 0.82,
            reasoning: 'Increasing intensity over last 3 weeks',
          },
        },
        loading: new Set(),
        errors: {},
      })
    )
    render(<PhaseTimeline />)
    expect(screen.getByText('build')).toBeInTheDocument()
    expect(screen.getByText(/82%/)).toBeInTheDocument()
  })
})
