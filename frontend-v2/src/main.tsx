import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { initTheme } from './theme/theme'
import './theme/variables.css'
import { App } from './App'

// Initialize theme before first render
initTheme()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
