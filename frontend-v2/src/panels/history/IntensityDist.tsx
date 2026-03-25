import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './IntensityDist.module.css'

const ZONES = [
  { key: 'zone1', label: 'Zone 1 (Easy)', color: '#3fb950', seiler: 'Low' },
  { key: 'zone2', label: 'Zone 2 (Threshold)', color: '#d29922', seiler: 'Medium' },
  { key: 'zone3', label: 'Zone 3 (High)', color: '#f85149', seiler: 'High' },
]

export function IntensityDist() {
  const ifDist = useDataStore(s => s.ifDistribution)
  const loading = useDataStore(s => s.loading.has('ifDistribution'))
  const error = useDataStore(s => s.errors['ifDistribution'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!ifDist) return <PanelEmpty message="No intensity distribution data" />

  // Derive Seiler 3-zone from IF distribution
  // Zone 1: IF < 0.75, Zone 2: IF 0.75-0.90, Zone 3: IF > 0.90
  const histogram = ifDist.histogram ?? {}
  let z1 = 0, z2 = 0, z3 = 0, total = 0

  for (const [bin, count] of Object.entries(histogram)) {
    const ifVal = parseFloat(bin)
    const c = count as number
    total += c
    if (ifVal < 0.75) z1 += c
    else if (ifVal < 0.90) z2 += c
    else z3 += c
  }

  if (total === 0) return <PanelEmpty message="No rides to analyze" />

  const pcts = [
    { ...ZONES[0], pct: (z1 / total) * 100 },
    { ...ZONES[1], pct: (z2 / total) * 100 },
    { ...ZONES[2], pct: (z3 / total) * 100 },
  ]

  return (
    <Tooltip
      label="IntensityDist"
      fullName="Seiler 3-Zone Intensity Distribution"
      derivation="Rides categorized by IF into 3 Seiler zones. Zone 1 < 0.75 IF, Zone 2 = 0.75-0.90, Zone 3 > 0.90."
      context="Polarized training: ~80% Zone 1, ~5% Zone 2, ~15% Zone 3. Pyramidal allows more Zone 2."
    >
      <div className={styles.container}>
        {pcts.map(z => (
          <div key={z.key} className={styles.zoneRow}>
            <div className={styles.zoneLabel}>{z.label}</div>
            <div className={styles.barContainer}>
              <div
                className={styles.bar}
                style={{ width: `${z.pct}%`, background: z.color }}
              />
            </div>
            <div className={styles.pct}>{z.pct.toFixed(1)}%</div>
          </div>
        ))}
        <div className={styles.meta}>
          {ifDist.rides_analyzed} rides analyzed
        </div>
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'intensity-dist',
  label: 'Intensity Distribution',
  category: 'history',
  description: 'Seiler 3-zone percentages — polarized training check',
  component: IntensityDist,
  dataKeys: ['ifDistribution'],
})
