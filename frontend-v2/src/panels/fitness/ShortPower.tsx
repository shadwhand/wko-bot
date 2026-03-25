import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Metric } from '../../shared/Metric'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function ShortPower() {
  const data = useDataStore(s => s.shortPower)
  const loading = useDataStore(s => s.loading.has('shortPower'))
  const error = useDataStore(s => s.errors['shortPower'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!data) return <PanelEmpty message="No short power data" />

  const ratioColor =
    data.ratio > 1.3 ? 'var(--color-success, #3fb950)'
    : data.ratio < 1.1 ? 'var(--color-warning, #d29922)'
    : 'var(--color-text-primary, #e6edf3)'

  return (
    <Tooltip
      label="ShortPower"
      fullName="Short Power Consistency"
      derivation={`Peak 1min: ${data.peak}W, Typical 1min: ${data.typical}W. Ratio = peak/typical.`}
      context="High ratio (>1.3) = big sprint but inconsistent. Low (<1.1) = very repeatable but may lack top end."
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <Metric value={data.peak} label="Peak 1min" unit="W" />
        <Metric value={data.typical} label="Typical 1min" unit="W" />
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '24px', fontWeight: 700, color: ratioColor }}>
            {data.ratio.toFixed(2)}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Ratio</div>
        </div>
        <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', flex: 1, minWidth: '150px' }}>
          {data.diagnosis}
        </div>
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'short-power',
  label: 'Short Power',
  category: 'fitness',
  description: 'Peak vs median 1min ratio — consistency diagnosis',
  component: ShortPower,
  dataKeys: ['shortPower'],
})
