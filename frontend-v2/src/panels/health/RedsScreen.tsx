import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { FlagCard } from './FlagCard'
import { registerPanel } from '../../layout/PanelRegistry'

export function RedsScreen() {
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!flags) return <PanelEmpty message="No clinical data" />

  const flag = (flags.flags ?? []).find((f) =>
    f.name === 'reds_screen' || f.name === 'reds'
  )
  if (!flag) return <PanelEmpty message="RED-S screening not available" />

  return (
    <FlagCard
      name="RED-S Screen"
      status={flag.status}
      value={flag.status === 'ok' ? 'Low Risk' : flag.status === 'warning' ? 'Moderate' : 'High Risk'}
      detail={flag.detail}
      tooltip={{
        fullName: 'RED-S Screening (Relative Energy Deficiency in Sport)',
        derivation: 'Pattern analysis of training load vs performance trends.',
        context: 'RED-S requires medical evaluation. This is a screening tool, not a diagnosis.',
      }}
    />
  )
}

registerPanel({
  id: 'reds-screen',
  label: 'RED-S Screen',
  category: 'health',
  description: 'Relative Energy Deficiency screening',
  component: RedsScreen,
  dataKeys: ['clinicalFlags'],
})
