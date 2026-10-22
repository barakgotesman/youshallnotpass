import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// Local dev: the browser talks only to the Vite server, which forwards /api/*
// to the FastAPI process. This mirrors production (same origin on Vercel), so
// we never need CORS holes just to make development work.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  test: {
    environment: 'node',
  },
})
