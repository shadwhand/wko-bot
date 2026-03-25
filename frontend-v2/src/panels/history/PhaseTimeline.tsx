import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

const PHASE_COLORS: Record<string, string> = {
  base: 'var(--color-accent, #58a6ff)',
  build: 'var(--color-warning, #d29922)',
  peak: 'var(--color-danger, #f85149)',
  recovery: 'var(--color-success, #3fb950)',
  transition: 'var(--color-text-secondary, #8b949e)',
}

export function PhaseTimeline() {
  // Phase detection comes from the clinical/model endpoint
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />

  const phase = (flags as any)?.detected_phase
  if (!phase) return <PanelEmpty message="Phase detection not available" />

  const phaseColor = PHASE_COLORS[phase.phase] ?? 'var(--color-text-secondary)'

  return (
    <Tooltip
      label="Phase"
      fullName="Detected Training Phase"
      derivation={`Phase detection based on CTL trend, intensity distribution, and volume patterns. Confidence: ${(phase.confidence * 100).toFixed(0)}%.`}
      context="Base = aerobic focus. Build = intensity increasing. Peak = race-specific. Recovery = deload."
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        padding: '8px 0',
      }}>
        <div style={{
          fontSize: '28px',
          fontWeight: 700,
          color: phaseColor,
          textTransform: 'capitalize',
        }}>
          {phase.phase}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: '13px',
            color: 'var(--color-text-secondary)',
            marginBottom: '4px',
          }}>
            Confidence: {(phase.confidence * 100).toFixed(0)}%
          </div>
          <div style={{
            width: '100%',
            height: '6px',
            background: 'var(--color-bg-secondary, #21262d)',
            borderRadius: '3px',
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${phase.confidence * 100}%`,
              height: '100%',
              background: phaseColor,
              borderRadius: '3px',
            }} />
          </div>
          {phase.reasoning && (
            <div style={{
              fontSize: '12px',
              color: 'var(--color-text-secondary)',
              marginTop: '6px',
              lineHeight: 1.4,
            }}>
              {phase.reasoning}
            </div>
          )}
        </div>
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'phase-timeline',
  label: 'Phase Timeline',
  category: 'history',
  description: 'Current detected training phase with confidence',
  component: PhaseTimeline,
  dataKeys: ['clinicalFlags'],
})
