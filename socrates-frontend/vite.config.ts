import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Ensure public directory is served at root
  publicDir: 'public',
  server: {
    // Development server configuration
    middlewareMode: false,
  },
})
