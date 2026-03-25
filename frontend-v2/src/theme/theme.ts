export type Theme = 'dark' | 'light'

const STORAGE_KEY = 'wko5-theme'

/** Detect OS color scheme preference. */
function getOsTheme(): Theme {
  if (typeof window === 'undefined') return 'dark'
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

/** Read persisted theme, falling back to OS preference. */
export function getStoredTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'dark' || stored === 'light') return stored
  } catch {
    // localStorage unavailable
  }
  return getOsTheme()
}

/** Apply theme to the document root. */
export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute('data-theme', theme)
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // localStorage unavailable
  }
}

/** Toggle between dark and light. Returns the new theme. */
export function toggleTheme(): Theme {
  const current = document.documentElement.getAttribute('data-theme') as Theme
  const next: Theme = current === 'dark' ? 'light' : 'dark'
  applyTheme(next)
  return next
}

/** Initialize theme on app start. */
export function initTheme(): Theme {
  const theme = getStoredTheme()
  applyTheme(theme)

  // Listen for OS preference changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    // Only follow OS if user hasn't manually set a preference
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) {
      applyTheme(e.matches ? 'dark' : 'light')
    }
  })

  return theme
}
