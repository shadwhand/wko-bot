import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { FlagCard } from './FlagCard'
import { registerPanel } from '../../layout/PanelRegistry'

export function IFFloor() {
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!flags) return <PanelEmpty message="No clinical data" />

  const flag = (flags.flags ?? []).find((f) => {
    const n = f.name.toLowerCase().replace(/[\s\-]+/g, '_')
    return n === 'if_floor' || n === 'intensity_floor'
  })
  if (!flag) return <PanelEmpty message="IF Floor check not available" />

  return (
    <FlagCard
      name="IF Floor"
      status={flag.status}
      value={typeof flag.value === 'number' ? flag.value.toFixed(3) : flag.value}
      threshold={typeof flag.threshold === 'number' ? flag.threshold.toFixed(2) : flag.threshold}
      detail={flag.detail}
      tooltip={{
        fullName: 'Intensity Factor Floor',
        derivation: 'Median IF of endurance rides (IF < 0.75). Flags if consistently above threshold.',
        context: 'High IF floor means easy rides are too hard, limiting adaptation.',
      }}
    />
  )
}

registerPanel({
  id: 'if-floor',
  label: 'IF Floor',
  category: 'health',
  description: 'Endurance ride intensity floor flag',
  component: IFFloor,
  dataKeys: ['clinicalFlags'],
})
