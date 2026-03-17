import { defineConfig, devices } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_URL = process.env.API_URL || 'http://localhost:8000';

export default defineConfig({
  testDir: './',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  // webServer started manually in CI
  webServer: process.env.CI ? undefined : [
    { command: 'cd ../frontend && npm run dev', url: BASE_URL, reuseExistingServer: true },
    { command: 'cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000', url: `${API_URL}/health`, reuseExistingServer: true },
  ],
  timeout: 20000,
  expect: { timeout: 5000 },
});
