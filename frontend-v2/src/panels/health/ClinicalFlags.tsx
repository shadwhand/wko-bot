import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { FlagCard } from './FlagCard'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './ClinicalFlags.module.css'

/** Severity sort order: danger first, then warning, then ok */
const SEVERITY_ORDER: Record<string, number> = { danger: 0, warning: 1, ok: 2 }

/** Tooltip metadata per flag type */
const FLAG_TOOLTIPS: Record<string, { fullName: string; derivation: string; context?: string }> = {
  if_floor: {
    fullName: 'Intensity Factor Floor',
    derivation: 'Median IF of endurance rides (IF < 0.75). Flags if consistently above threshold.',
    context: 'High IF floor suggests riding too hard on easy days, limiting recovery.',
  },
  panic_training: {
    fullName: 'Panic Training Detection',
    derivation: 'Sudden jump in weekly TSS following a low-load period. Compares recent ATL to prior baseline.',
    context: 'Sudden volume spikes after detraining increase injury risk.',
  },
  reds_screen: {
    fullName: 'RED-S Screening',
    derivation: 'Pattern analysis of training load vs performance trends indicating energy deficiency.',
    context: 'RED-S (Relative Energy Deficiency in Sport) requires medical evaluation.',
  },
  overtraining: {
    fullName: 'Overtraining Risk',
    derivation: 'Sustained high ATL with declining performance markers.',
    context: 'Extended negative TSB with declining power suggests non-functional overreaching.',
  },
}

export function ClinicalFlags() {
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!flags) return <PanelEmpty message="No clinical flags data" />

  const flagList = [...(flags.flags ?? [])].sort(
    (a, b) => (SEVERITY_ORDER[a.status] ?? 2) - (SEVERITY_ORDER[b.status] ?? 2)
  )

  return (
    <div className={styles.grid}>
      {flagList.map((flag) => (
        <FlagCard
          key={flag.name}
          name={flag.name}
          status={flag.status}
          value={typeof flag.value === 'number' ? flag.value.toFixed(2) : flag.value}
          threshold={typeof flag.threshold === 'number' ? flag.threshold.toFixed(2) : flag.threshold}
          detail={flag.detail}
          tooltip={FLAG_TOOLTIPS[flag.name] ?? {
            fullName: flag.name,
            derivation: 'Clinical screening check',
          }}
        />
      ))}
    </div>
  )
}

registerPanel({
  id: 'clinical-flags',
  label: 'Clinical Flags',
  category: 'health',
  description: 'Flag card grid, severity-ordered (danger first)',
  component: ClinicalFlags,
  dataKeys: ['clinicalFlags'],
})
