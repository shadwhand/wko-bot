import { useState, useCallback } from 'react'
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Metric } from '../../shared/Metric'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import { postGlycogenBudget } from '../../api/client'
import styles from './GlycogenBudget.module.css'

interface BudgetForm {
  ride_kj: number
  duration_hours: number
  carbs_per_hour: number
  delay_min: number
  weight_kg: number
}

const DEFAULT_FORM: BudgetForm = {
  ride_kj: 2500,
  duration_hours: 4,
  carbs_per_hour: 60,
  delay_min: 30,
  weight_kg: 76,
}

export function GlycogenBudget() {
  const selectedRouteId = useDataStore(s => s.selectedRouteId)
  const config = useDataStore(s => s.config)

  const [form, setForm] = useState<BudgetForm>({
    ...DEFAULT_FORM,
    weight_kg: config?.weight_kg ?? DEFAULT_FORM.weight_kg,
  })
  const [result, setResult] = useState<any>(null)
  const [computing, setComputing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const debounceRef = useState<ReturnType<typeof setTimeout> | null>(null)

  const handleChange = useCallback((field: keyof BudgetForm, value: number) => {
    setForm(prev => {
      const next = { ...prev, [field]: value }
      // Debounced compute
      if (debounceRef[0]) clearTimeout(debounceRef[0])
      debounceRef[0] = setTimeout(async () => {
        setComputing(true)
        setError(null)
        try {
          const res = await postGlycogenBudget(next)
          setResult(res)
        } catch (e: any) {
          setError(e.message ?? 'Computation failed')
        } finally {
          setComputing(false)
        }
      }, 500)
      return next
    })
  }, [])

  return (
    <Tooltip
      label="GlycogenBudget"
      fullName="Glycogen Budget Calculator"
      derivation="Models muscle glycogen depletion over ride duration given intake rate."
      context="Bonk risk = glycogen drops below ~25% capacity. Increase carb intake or reduce intensity."
    >
      <div className={styles.container}>
        <div className={styles.form}>
          <div className={styles.field}>
            <label>Ride kJ</label>
            <input
              type="number"
              value={form.ride_kj}
              onChange={e => handleChange('ride_kj', Number(e.target.value))}
              min={0}
              step={100}
            />
          </div>
          <div className={styles.field}>
            <label>Duration (h)</label>
            <input
              type="number"
              value={form.duration_hours}
              onChange={e => handleChange('duration_hours', Number(e.target.value))}
              min={0.5}
              step={0.5}
            />
          </div>
          <div className={styles.field}>
            <label>Carbs/hr (g)</label>
            <input
              type="number"
              value={form.carbs_per_hour}
              onChange={e => handleChange('carbs_per_hour', Number(e.target.value))}
              min={0}
              step={10}
            />
          </div>
          <div className={styles.field}>
            <label>Delay (min)</label>
            <input
              type="number"
              value={form.delay_min}
              onChange={e => handleChange('delay_min', Number(e.target.value))}
              min={0}
              step={5}
            />
          </div>
          <div className={styles.field}>
            <label>Weight (kg)</label>
            <input
              type="number"
              value={form.weight_kg}
              onChange={e => handleChange('weight_kg', Number(e.target.value))}
              min={30}
              step={1}
            />
          </div>
        </div>

        {computing && <div className={styles.computing}>Computing...</div>}
        {error && <PanelError message={error} />}

        {result && !computing && (
          <div className={styles.results}>
            <Metric
              value={result.bonk_risk != null ? `${(result.bonk_risk * 100).toFixed(0)}%` : '\u2014'}
              label="Bonk Risk"
            />
            <Metric
              value={result.min_glycogen_pct != null ? `${(result.min_glycogen_pct * 100).toFixed(0)}%` : '\u2014'}
              label="Min Glycogen"
            />
            <Metric
              value={result.time_to_bonk_min != null ? `${result.time_to_bonk_min.toFixed(0)} min` : 'N/A'}
              label="Time to Bonk"
            />
            {result.recommendation && (
              <div className={styles.recommendation}>{result.recommendation}</div>
            )}
            {/* Chart placeholder — wired in Plan 1C with D3 timeline */}
            <div className={styles.chartPlaceholder}>
              Glycogen timeline chart will render here (Plan 1C)
            </div>
          </div>
        )}
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'glycogen-budget',
  label: 'Glycogen Budget',
  category: 'event-prep',
  description: 'Interactive glycogen calculator — form + results (chart in 1C)',
  component: GlycogenBudget,
  dataKeys: ['config', 'selectedRouteId'],
})
