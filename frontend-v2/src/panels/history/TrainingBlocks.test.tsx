import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrainingBlocks } from './TrainingBlocks'

vi.mock('../../store/data-store', () => ({
  useDataStore: vi.fn(),
}))

import { useDataStore } from '../../store/data-store'
const mockUseDataStore = vi.mocked(useDataStore)

describe('TrainingBlocks', () => {
  it('shows empty state when no activities', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        activities: [],
        loading: new Set(),
        errors: {},
      })
    )
    render(<TrainingBlocks />)
    expect(screen.getByText(/no training data/i)).toBeInTheDocument()
  })

  it('renders block stats from recent activities', () => {
    const now = new Date()
    const recentDate = new Date(now.getTime() - 7 * 86_400_000).toISOString()
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        activities: [
          {
            id: 1,
            start_time: recentDate,
            total_elapsed_time: 3600,
            training_stress_score: 80,
            intensity_factor: 0.75,
            avg_power: 200,
          },
        ],
        loading: new Set(),
        errors: {},
      })
    )
    render(<TrainingBlocks />)
    expect(screen.getByText('1')).toBeInTheDocument() // 1 ride
    expect(screen.getByText('Rides')).toBeInTheDocument()
  })
})
