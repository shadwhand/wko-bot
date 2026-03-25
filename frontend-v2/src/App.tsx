import { useState } from 'react'
import { Header } from './header/Header'
import { TabBar } from './layout/TabBar'
import { Footer } from './footer/Footer'
import { WarmupScreen } from './startup/WarmupScreen'
import { useStartup } from './startup/useStartup'
import { useAutoRefresh } from './startup/useAutoRefresh'
import { TSBStatus } from './panels/status/TSBStatus'
import styles from './App.module.css'

export function App() {
  const { phase, warmupStatus, error } = useStartup()
  const [activeTab, setActiveTab] = useState('today')

  // Auto-refresh only when startup is complete
  useAutoRefresh(phase === 'ready')

  if (phase === 'warming' || phase === 'loading' || phase === 'error') {
    return <WarmupScreen status={warmupStatus} error={error} />
  }

  return (
    <div className={styles.app}>
      <Header />
      <TabBar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className={styles.main}>
        {activeTab === 'today' && (
          <div className={styles.panelGrid}>
            <TSBStatus />
          </div>
        )}
        {activeTab !== 'today' && (
          <div className={styles.placeholder}>
            <p>{activeTab} tab — panels coming in Phase 1B</p>
          </div>
        )}
      </main>
      <Footer />
    </div>
  )
}
