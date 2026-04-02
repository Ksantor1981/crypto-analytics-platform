/**
 * E2E smoke tests for Crypto Analytics Platform.
 * Run: npx playwright test (from e2e/)
 * Or: BASE_URL=http://... API_URL=... npx playwright test
 */
import { test, expect } from '@playwright/test';

test.describe('Smoke tests', () => {
  test('home page loads', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/\S/);  // non-empty title
  });

  test('backend health check', async ({ request }) => {
    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    const res = await request.get(`${apiUrl}/health`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('status', 'healthy');
  });

  test('api root returns docs info', async ({ request }) => {
    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    const res = await request.get(`${apiUrl}/`);
    expect(res.ok()).toBeTruthy();
  });

  test('channels page accessible when logged out', async ({ page }) => {
    await page.goto('/channels');
    await page.waitForLoadState('load');
    // Should show channels list or login prompt
    const body = await page.textContent('body');
    expect(body).toBeTruthy();
  });

  test('dashboard page loads', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('load');
    const body = await page.textContent('body');
    expect(body).toBeTruthy();
  });
});
