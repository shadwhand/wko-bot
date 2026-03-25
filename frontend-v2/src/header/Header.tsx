import { useState } from 'react'
import { toggleTheme } from '../theme/theme'
import { SyncIndicator } from './SyncIndicator'
import styles from './Header.module.css'

export function Header() {
  const [theme, setTheme] = useState(
    () => (document.documentElement.getAttribute('data-theme') as 'dark' | 'light') ?? 'dark',
  )

  function handleToggleTheme() {
    const next = toggleTheme()
    setTheme(next)
  }

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <h1 className={styles.logo}>WKO5</h1>
        <span className={styles.version}>v2</span>
      </div>
      <div className={styles.right}>
        <SyncIndicator />
        <button
          className={styles.themeBtn}
          onClick={handleToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? '\u2600' : '\u263D'}
        </button>
      </div>
    </header>
  )
}
