import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/jobs': 'http://127.0.0.1:8000',
      '/job-analyses': 'http://127.0.0.1:8000',
      '/applications': 'http://127.0.0.1:8000',
      '/profiles': 'http://127.0.0.1:8000',
      '/agent-runs': 'http://127.0.0.1:8000',
    },
  },
})
