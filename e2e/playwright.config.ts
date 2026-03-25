import { defineConfig, devices } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_URL = process.env.API_URL || 'http://localhost:8000';

/** Passed to uvicorn subprocess when webServer auto-starts backend (local runs). */
const e2eBackendEnv = {
  ...process.env,
  USE_SQLITE: process.env.USE_SQLITE ?? 'true',
  SECRET_KEY: process.env.SECRET_KEY ?? 'ci-e2e-secret-key-32-chars-minimum',
  DEBUG: process.env.DEBUG ?? 'true',
};

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
    {
      command: 'cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000',
      url: `${API_URL}/health`,
      reuseExistingServer: true,
      env: e2eBackendEnv,
    },
  ],
  timeout: 20000,
  expect: { timeout: 5000 },
});
