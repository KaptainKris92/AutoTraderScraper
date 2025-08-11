/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const dirname = typeof __dirname !== 'undefined' ? __dirname : path.dirname(fileURLToPath(import.meta.url));

// More info at: https://storybook.js.org/docs/next/writing-tests/integrations/vitest-addon
const allowedHost = process.env.NGROK_HOSTNAME || '';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    // Allows connections from external devices (equivalent to 0.0.0.0)
    port: 5173,
    allowedHosts: allowedHost ? [allowedHost] : [],
    proxy: {
    '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
    }
    }
  }
});