import { test, expect } from '@playwright/test';

test.describe('Full user flow (Stripe critical path)', () => {
  test.describe.configure({ mode: 'serial' });

  test('create user → subscribe → checkout → success banner', async ({
    page,
    request,
  }) => {
    const password = 'SecurePass1!123';
    const fullName = 'E2E User';
    /** Новый пользователь каждый прогон — иначе после mock-checkout в БД уже Premium и кнопка Premium disabled. */
    const email = `e2e_stripe_${Date.now()}@example.com`;

    const apiUrl = process.env.API_URL || 'http://localhost:8000';

    const registerRes = await request.post(`${apiUrl}/api/v1/users/register`, {
      data: {
        email,
        password,
        confirm_password: password,
        full_name: fullName,
      },
    });
    expect(registerRes.ok(), await registerRes.text()).toBeTruthy();

    const loginResponse = await request.post(`${apiUrl}/api/v1/users/login`, {
      data: { email, password },
    });
    expect(loginResponse.ok(), await loginResponse.text()).toBeTruthy();

    const loginJson = (await loginResponse.json()) as {
      access_token?: string;
    };
    expect(loginJson.access_token).toBeTruthy();

    // Ensure token is accepted by the backend auth layer.
    const meRes = await request.get(`${apiUrl}/api/v1/users/me`, {
      headers: {
        Authorization: `Bearer ${loginJson.access_token}`,
      },
    });
    expect(meRes.ok(), await meRes.text()).toBeTruthy();

    const token = loginJson.access_token as string;
    await page.addInitScript(t => {
      window.localStorage.setItem('access_token', t);
    }, token);

    await page.goto('/subscription');

    await expect(page.getByRole('button', { name: 'Выйти' })).toBeVisible({
      timeout: 30000,
    });

    await page.locator('[data-test="premium-subscribe-btn"]').click({
      timeout: 30000,
    });

    // In mock mode, intermediate page may auto-redirect quickly.
    try {
      await page.waitForURL('**/mock-checkout/**', { timeout: 10000 });
      await expect(
        page.getByRole('heading', { name: 'Mock Stripe Checkout' })
      ).toBeVisible({ timeout: 10000 });
    } catch {
      // It's fine; we validate the final success banner below.
    }

    await page.waitForURL('**/subscription?success=true', { timeout: 60000 });
    await expect(
      page.getByText('Подписка успешно оформлена!')
    ).toBeVisible({ timeout: 30000 });
  });
});

