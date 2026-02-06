import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Generate timestamp for build artifacts (YYYYMMDD-HHMMSS format)
const buildTimestamp = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  return `${year}${month}${day}-${hours}${minutes}${seconds}`;
};

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['inverness.valley'],
  },
  build: {
    rollupOptions: {
      output: {
        entryFileNames: `assets/[name]-${buildTimestamp()}.js`,
        chunkFileNames: `assets/[name]-${buildTimestamp()}.js`,
        assetFileNames: `assets/[name]-${buildTimestamp()}.[ext]`,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.config.js',
        '**/*.config.ts',
        '**/main.jsx',
        'src/services/api.js', // API client - will be tested via integration tests
      ],
      thresholds: {
        lines: 60,
        functions: 60,
        branches: 60,
        statements: 60,
      },
    },
  },
})
