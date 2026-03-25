import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function Phenotype() {
  const profile = useDataStore(s => s.profile)
  const loading = useDataStore(s => s.loading.has('profile'))
  const error = useDataStore(s => s.errors['profile'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!profile?.strengths_limiters) return <PanelEmpty message="No phenotype data" />

  const sl = profile.strengths_limiters as any

  return (
    <Tooltip
      label="Phenotype"
      fullName="Rider Phenotype — Strengths and Limiters"
      derivation="Derived from power profile shape — ratio of short-duration to long-duration power."
      context="Sprinter = high 5s/1min relative to FTP. TTer = high 20min/60min relative to sprint."
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {sl.phenotype && (
          <div style={{
            fontSize: '20px',
            fontWeight: 700,
            color: 'var(--color-accent, #58a6ff)',
          }}>
            {sl.phenotype}
          </div>
        )}
        {sl.strengths && sl.strengths.length > 0 && (
          <div>
            <div style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--color-success, #3fb950)',
              textTransform: 'uppercase',
              marginBottom: '4px',
            }}>
              Strengths
            </div>
            {sl.strengths.map((s: string, i: number) => (
              <div key={i} style={{ fontSize: '13px', color: 'var(--color-text-primary)' }}>
                {s}
              </div>
            ))}
          </div>
        )}
        {sl.limiters && sl.limiters.length > 0 && (
          <div>
            <div style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--color-warning, #d29922)',
              textTransform: 'uppercase',
              marginBottom: '4px',
            }}>
              Limiters
            </div>
            {sl.limiters.map((l: string, i: number) => (
              <div key={i} style={{ fontSize: '13px', color: 'var(--color-text-primary)' }}>
                {l}
              </div>
            ))}
          </div>
        )}
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'phenotype',
  label: 'Phenotype',
  category: 'profile',
  description: 'Sprinter/Pursuiter/TTer classification with strengths and limiters',
  component: Phenotype,
  dataKeys: ['profile'],
})
