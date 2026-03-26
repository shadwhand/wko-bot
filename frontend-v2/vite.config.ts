import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync, existsSync } from 'fs'

function getBackendPort(): number {
  try {
    if (existsSync('../.runtime.json')) {
      const runtime = JSON.parse(readFileSync('../.runtime.json', 'utf-8'))
      return runtime.port || 8000
    }
  } catch {
    // Fall back to default if .runtime.json is missing or malformed
  }
  return 8000
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${getBackendPort()}`,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
