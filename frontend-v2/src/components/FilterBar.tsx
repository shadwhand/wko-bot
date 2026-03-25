import { useState } from 'react'
import { useDataStore } from '../store/data-store'
import styles from './FilterBar.module.css'

export function FilterBar() {
  const globalTimeRange = useDataStore(s => s.globalTimeRange)
  const setTimeRange = useDataStore(s => s.setTimeRange)

  const [startInput, setStartInput] = useState(globalTimeRange?.start ?? '')
  const [endInput, setEndInput] = useState(globalTimeRange?.end ?? '')

  const handleApply = () => {
    if (startInput && endInput) {
      setTimeRange({ start: startInput, end: endInput })
    }
  }

  const handleReset = () => {
    setStartInput('')
    setEndInput('')
    setTimeRange(null)
  }

  const rangeLabel = globalTimeRange
    ? `${globalTimeRange.start} to ${globalTimeRange.end}`
    : 'All Time'

  return (
    <div className={styles.filterBar} role="toolbar" aria-label="Time range filter">
      <span className={styles.label}>Range:</span>
      <span className={styles.rangeDisplay}>{rangeLabel}</span>

      <input
        type="date"
        className={styles.dateInput}
        value={startInput}
        onChange={e => setStartInput(e.target.value)}
        aria-label="Start date"
      />
      <span className={styles.separator}>to</span>
      <input
        type="date"
        className={styles.dateInput}
        value={endInput}
        onChange={e => setEndInput(e.target.value)}
        aria-label="End date"
      />

      <button
        className={styles.applyButton}
        onClick={handleApply}
        disabled={!startInput || !endInput}
      >
        Apply
      </button>

      {globalTimeRange && (
        <button className={styles.resetButton} onClick={handleReset}>
          Reset
        </button>
      )}
    </div>
  )
}
