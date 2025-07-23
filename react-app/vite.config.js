import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const allowedHost = process.env.NGROK_HOSTNAME || '';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Allows connections from external devices (equivalent to 0.0.0.0)
    port: 5173,
    allowedHosts: allowedHost ? [allowedHost] : [],
    proxy: {
      '/api': 'http://localhost:5000',
    },
  },
});

