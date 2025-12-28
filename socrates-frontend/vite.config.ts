import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Ensure public directory is served at root
  publicDir: 'public',
  server: {
    // Development server configuration
    middlewareMode: false,
    port: parseInt(process.env.PORT || '5173', 10),
    host: '127.0.0.1',
  },
})
