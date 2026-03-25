import { useEffect } from 'react'
import { useDataStore } from './store/data-store'
import { initLayoutStore, useLayoutStore } from './layout/layoutStore'
import { Header } from './components/Header'
import { FilterBar } from './components/FilterBar'
import { LayoutEngine } from './layout/LayoutEngine'
import { EditMode } from './layout/EditMode'
import { WarmupScreen } from './startup/WarmupScreen'
import { useStartup } from './startup/useStartup'
import { useAutoRefresh } from './startup/useAutoRefresh'
import { RideDetail } from './ride/RideDetail'

// Register all panels (side-effect imports)
import './panels'

import styles from './App.module.css'

export function App() {
  const { phase, warmupStatus, error } = useStartup()
  const athleteSlug = useDataStore(s => s.athleteSlug)

  // Initialize layout store on first render
  useEffect(() => {
    initLayoutStore(athleteSlug || 'default')
  }, [athleteSlug])

  // Auto-refresh only when startup is complete
  useAutoRefresh(phase === 'ready')

  if (phase === 'warming' || phase === 'loading' || phase === 'error') {
    return <WarmupScreen status={warmupStatus} error={error} />
  }

  // Wait for layout store initialization
  if (!useLayoutStore) {
    return <div>Initializing...</div>
  }

  return <AppShell />
}

/** Inner shell — only renders after layout store is initialized */
function AppShell() {
  const editMode = useLayoutStore(s => s.editMode)
  const selectedRideId = useDataStore(s => s.selectedRideId)
  const setSelectedRide = useDataStore(s => s.setSelectedRide)

  // State-based routing: if a ride is selected, show RideDetail instead of main layout
  if (selectedRideId != null) {
    return (
      <div className={styles.app}>
        <Header />
        <main className={styles.main}>
          <RideDetail
            rideId={selectedRideId}
            onBack={() => setSelectedRide(null)}
          />
        </main>
      </div>
    )
  }

  return (
    <div className={styles.app}>
      <Header />
      <FilterBar />
      <main className={styles.main}>
        {editMode ? <EditMode /> : <LayoutEngine />}
      </main>
    </div>
  )
}
