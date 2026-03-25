import type { Layout } from './types'

export const LAYOUT_VERSION = 1

export const ATHLETE_PRESET: Layout = {
  version: LAYOUT_VERSION,
  tabs: [
    {
      id: 'today',
      label: 'Today',
      panels: ['tsb-status', 'recent-rides', 'clinical-alert'],
    },
    {
      id: 'health',
      label: 'Health',
      panels: [
        'clinical-flags',
        'if-floor',
        'panic-training',
        'reds-screen',
        'fresh-baseline',
      ],
    },
    {
      id: 'fitness',
      label: 'Fitness',
      panels: [
        'pmc-chart',
        'mmp-curve',
        'rolling-ftp',
        'ftp-growth',
        'rolling-pd',
        'short-power',
        'power-profile',
      ],
    },
    {
      id: 'event-prep',
      label: 'Event Prep',
      panels: [
        'route-selector',
        'segment-profile',
        'demand-heatmap',
        'gap-analysis',
        'pacing',
        'opportunity-cost',
        'glycogen-budget',
      ],
    },
    {
      id: 'history',
      label: 'History',
      panels: [
        'rides-table',
        'training-blocks',
        'phase-timeline',
        'intensity-dist',
      ],
    },
    {
      id: 'profile',
      label: 'Profile',
      panels: [
        'coggan-ranking',
        'phenotype',
        'posterior-summary',
        'feasibility',
        'athlete-config',
      ],
    },
    {
      id: 'settings',
      label: 'Settings',
      panels: ['athlete-config'],
    },
  ],
}

export const COACH_PRESET: Layout = {
  version: LAYOUT_VERSION,
  tabs: [
    {
      id: 'health',
      label: 'Health',
      panels: [
        'clinical-flags',
        'if-floor',
        'panic-training',
        'reds-screen',
        'fresh-baseline',
      ],
    },
    {
      id: 'today',
      label: 'Today',
      panels: ['tsb-status', 'recent-rides', 'clinical-alert'],
    },
    {
      id: 'fitness',
      label: 'Fitness',
      panels: [
        'pmc-chart',
        'mmp-curve',
        'rolling-ftp',
        'ftp-growth',
        'rolling-pd',
        'short-power',
        'power-profile',
      ],
    },
    {
      id: 'history',
      label: 'History',
      panels: ['rides-table', 'training-blocks', 'phase-timeline'],
    },
    {
      id: 'profile',
      label: 'Profile',
      panels: [
        'coggan-ranking',
        'phenotype',
        'posterior-summary',
        'feasibility',
      ],
    },
    {
      id: 'event-prep',
      label: 'Event Prep',
      panels: [
        'route-selector',
        'gap-analysis',
        'opportunity-cost',
        'pacing',
        'glycogen-budget',
      ],
    },
  ],
}

/** Get default layout for a role */
export function getDefaultPreset(role: 'athlete' | 'coach' = 'athlete'): Layout {
  const source = role === 'coach' ? COACH_PRESET : ATHLETE_PRESET
  return JSON.parse(JSON.stringify(source)) // deep clone
}
