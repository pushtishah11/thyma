import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    // The browser only talks to Vite. Vite forwards /api to FastAPI, so there's
    // no CORS setup and the frontend never needs to know the backend's port.
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
