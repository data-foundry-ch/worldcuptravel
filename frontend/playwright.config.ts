import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: 'http://127.0.0.1:8000',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'cd .. && .venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000',
    port: 8000,
    reuseExistingServer: !process.env.CI,
    env: {
      APP_ENV: 'production',
      DUCKDB_PATH: 'data/worldcup.duckdb',
    },
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
