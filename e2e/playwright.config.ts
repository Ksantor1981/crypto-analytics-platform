import { defineConfig, devices } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_URL = process.env.API_URL || 'http://localhost:8000';

/** Passed to uvicorn subprocess when webServer auto-starts backend (local runs). */
const e2eBackendEnv = {
  ...process.env,
  USE_SQLITE: process.env.USE_SQLITE ?? 'true',
  SECRET_KEY: process.env.SECRET_KEY ?? 'ci-e2e-secret-key-32-chars-minimum',
  STRIPE_MOCK_MODE: process.env.STRIPE_MOCK_MODE ?? 'true',
  DEBUG: process.env.DEBUG ?? 'true',
  // Make auth/register/login stable for E2E runs.
  AUTH_RATE_LIMIT_REQUESTS: process.env.AUTH_RATE_LIMIT_REQUESTS ?? '200',
  AUTH_RATE_LIMIT_WINDOW: process.env.AUTH_RATE_LIMIT_WINDOW ?? '900',
};

export default defineConfig({
  testDir: './',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 3 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    actionTimeout: 15000,
    navigationTimeout: 30000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  // webServer started manually in CI
  webServer: process.env.CI ? undefined : [
    {
      command: 'cd ../frontend && npm run dev',
      url: BASE_URL,
      reuseExistingServer: false,
    },
    {
      command: 'cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000',
      url: `${API_URL}/health`,
      reuseExistingServer: false,
      env: e2eBackendEnv,
    },
  ],
  /** Stripe mock + navigation может занимать >30s на медленных машинах */
  timeout: 120000,
  expect: { timeout: 10000 },
});
