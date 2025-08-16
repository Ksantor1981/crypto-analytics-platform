import { test, expect } from '@playwright/test';

// Базовый URL для тестов
const BASE_URL = process.env.TEST_URL || 'http://localhost:3000';

test.describe('Crypto Analytics Platform E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Переходим на главную страницу перед каждым тестом
    await page.goto(BASE_URL);
  });

  test.describe('Landing Page', () => {
    test('should display landing page with all sections', async ({ page }) => {
      // Проверяем наличие основных секций
      await expect(page.locator('h1')).toContainText('Crypto Analytics Platform');
      
      // Проверяем навигацию
      await expect(page.locator('nav')).toBeVisible();
      
      // Проверяем основные секции
      await expect(page.locator('[data-testid="hero-section"]')).toBeVisible();
      await expect(page.locator('[data-testid="features-section"]')).toBeVisible();
      await expect(page.locator('[data-testid="pricing-section"]')).toBeVisible();
    });

    test('should navigate to login page', async ({ page }) => {
      // Нажимаем на кнопку "Войти"
      await page.click('[data-testid="login-button"]');
      
      // Проверяем, что перешли на страницу входа
      await expect(page).toHaveURL(/.*login/);
      await expect(page.locator('h1')).toContainText('Вход');
    });

    test('should navigate to registration page', async ({ page }) => {
      // Нажимаем на кнопку "Регистрация"
      await page.click('[data-testid="register-button"]');
      
      // Проверяем, что перешли на страницу регистрации
      await expect(page).toHaveURL(/.*register/);
      await expect(page.locator('h1')).toContainText('Регистрация');
    });
  });

  test.describe('Authentication Flow', () => {
    test('should register new user', async ({ page }) => {
      // Переходим на страницу регистрации
      await page.goto(`${BASE_URL}/register`);
      
      // Заполняем форму регистрации
      await page.fill('[data-testid="email-input"]', 'test@example.com');
      await page.fill('[data-testid="password-input"]', 'password123');
      await page.fill('[data-testid="confirm-password-input"]', 'password123');
      
      // Нажимаем кнопку регистрации
      await page.click('[data-testid="register-submit"]');
      
      // Проверяем успешную регистрацию (редирект на dashboard)
      await expect(page).toHaveURL(/.*dashboard/);
    });

    test('should login existing user', async ({ page }) => {
      // Переходим на страницу входа
      await page.goto(`${BASE_URL}/login`);
      
      // Заполняем форму входа
      await page.fill('[data-testid="email-input"]', 'test@example.com');
      await page.fill('[data-testid="password-input"]', 'password123');
      
      // Нажимаем кнопку входа
      await page.click('[data-testid="login-submit"]');
      
      // Проверяем успешный вход (редирект на dashboard)
      await expect(page).toHaveURL(/.*dashboard/);
    });

    test('should show error for invalid credentials', async ({ page }) => {
      // Переходим на страницу входа
      await page.goto(`${BASE_URL}/login`);
      
      // Заполняем форму неверными данными
      await page.fill('[data-testid="email-input"]', 'invalid@example.com');
      await page.fill('[data-testid="password-input"]', 'wrongpassword');
      
      // Нажимаем кнопку входа
      await page.click('[data-testid="login-submit"]');
      
      // Проверяем, что появилось сообщение об ошибке
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      await expect(page.locator('[data-testid="error-message"]')).toContainText('Неверные учетные данные');
    });
  });

  test.describe('Dashboard', () => {
    test.beforeEach(async ({ page }) => {
      // Логинимся перед тестами dashboard
      await page.goto(`${BASE_URL}/login`);
      await page.fill('[data-testid="email-input"]', 'test@example.com');
      await page.fill('[data-testid="password-input"]', 'password123');
      await page.click('[data-testid="login-submit"]');
      await page.waitForURL(/.*dashboard/);
    });

    test('should display dashboard with user metrics', async ({ page }) => {
      // Проверяем наличие основных элементов dashboard
      await expect(page.locator('[data-testid="dashboard-header"]')).toBeVisible();
      await expect(page.locator('[data-testid="user-metrics"]')).toBeVisible();
      await expect(page.locator('[data-testid="recent-signals"]')).toBeVisible();
      await expect(page.locator('[data-testid="quick-actions"]')).toBeVisible();
    });

    test('should navigate to channels page', async ({ page }) => {
      // Нажимаем на ссылку "Каналы"
      await page.click('[data-testid="nav-channels"]');
      
      // Проверяем, что перешли на страницу каналов
      await expect(page).toHaveURL(/.*channels/);
      await expect(page.locator('h1')).toContainText('Каналы');
    });

    test('should navigate to signals page', async ({ page }) => {
      // Нажимаем на ссылку "Сигналы"
      await page.click('[data-testid="nav-signals"]');
      
      // Проверяем, что перешли на страницу сигналов
      await expect(page).toHaveURL(/.*signals/);
      await expect(page.locator('h1')).toContainText('Сигналы');
    });
  });

  test.describe('Channels Management', () => {
    test.beforeEach(async ({ page }) => {
      // Логинимся и переходим на страницу каналов
      await page.goto(`${BASE_URL}/login`);
      await page.fill('[data-testid="email-input"]', 'test@example.com');
      await page.fill('[data-testid="password-input"]', 'password123');
      await page.click('[data-testid="login-submit"]');
      await page.waitForURL(/.*dashboard/);
      await page.click('[data-testid="nav-channels"]');
    });

    test('should display channels list', async ({ page }) => {
      // Проверяем наличие списка каналов
      await expect(page.locator('[data-testid="channels-list"]')).toBeVisible();
      
      // Проверяем наличие кнопки добавления канала
      await expect(page.locator('[data-testid="add-channel-button"]')).toBeVisible();
    });

    test('should add new channel', async ({ page }) => {
      // Нажимаем кнопку добавления канала
      await page.click('[data-testid="add-channel-button"]');
      
      // Заполняем форму добавления канала
      await page.fill('[data-testid="channel-name-input"]', 'Test Channel');
      await page.fill('[data-testid="channel-url-input"]', 'https://t.me/testchannel');
      await page.selectOption('[data-testid="channel-category-select"]', 'crypto');
      
      // Нажимаем кнопку сохранения
      await page.click('[data-testid="save-channel-button"]');
      
      // Проверяем, что канал добавлен
      await expect(page.locator('[data-testid="channel-card"]')).toContainText('Test Channel');
    });

    test('should delete channel', async ({ page }) => {
      // Находим первый канал и нажимаем кнопку удаления
      await page.click('[data-testid="delete-channel-button"]').first();
      
      // Подтверждаем удаление
      await page.click('[data-testid="confirm-delete-button"]');
      
      // Проверяем, что канал удален
      await expect(page.locator('[data-testid="channel-card"]')).toHaveCount(0);
    });
  });

  test.describe('Signals View', () => {
    test.beforeEach(async ({ page }) => {
      // Логинимся и переходим на страницу сигналов
      await page.goto(`${BASE_URL}/login`);
      await page.fill('[data-testid="email-input"]', 'test@example.com');
      await page.fill('[data-testid="password-input"]', 'password123');
      await page.click('[data-testid="login-submit"]');
      await page.waitForURL(/.*dashboard/);
      await page.click('[data-testid="nav-signals"]');
    });

    test('should display signals table', async ({ page }) => {
      // Проверяем наличие таблицы сигналов
      await expect(page.locator('[data-testid="signals-table"]')).toBeVisible();
      
      // Проверяем наличие фильтров
      await expect(page.locator('[data-testid="signals-filters"]')).toBeVisible();
    });

    test('should filter signals by type', async ({ page }) => {
      // Выбираем фильтр "Покупка"
      await page.selectOption('[data-testid="signal-type-filter"]', 'BUY');
      
      // Проверяем, что отображаются только сигналы покупки
      const buySignals = page.locator('[data-testid="signal-type"]');
      await expect(buySignals).toHaveCount(await buySignals.count());
      
      for (let i = 0; i < await buySignals.count(); i++) {
        await expect(buySignals.nth(i)).toContainText('BUY');
      }
    });

    test('should view signal details', async ({ page }) => {
      // Нажимаем на первый сигнал для просмотра деталей
      await page.click('[data-testid="signal-row"]').first();
      
      // Проверяем, что открылась модалка с деталями
      await expect(page.locator('[data-testid="signal-details-modal"]')).toBeVisible();
      await expect(page.locator('[data-testid="signal-pair"]')).toBeVisible();
      await expect(page.locator('[data-testid="signal-price"]')).toBeVisible();
    });
  });

  test.describe('User Profile', () => {
    test.beforeEach(async ({ page }) => {
      // Логинимся и переходим в профиль
      await page.goto(`${BASE_URL}/login`);
      await page.fill('[data-testid="email-input"]', 'test@example.com');
      await page.fill('[data-testid="password-input"]', 'password123');
      await page.click('[data-testid="login-submit"]');
      await page.waitForURL(/.*dashboard/);
      await page.click('[data-testid="nav-profile"]');
    });

    test('should display user profile information', async ({ page }) => {
      // Проверяем наличие информации профиля
      await expect(page.locator('[data-testid="profile-info"]')).toBeVisible();
      await expect(page.locator('[data-testid="user-email"]')).toContainText('test@example.com');
    });

    test('should update user profile', async ({ page }) => {
      // Нажимаем кнопку редактирования
      await page.click('[data-testid="edit-profile-button"]');
      
      // Изменяем имя пользователя
      await page.fill('[data-testid="user-name-input"]', 'New Name');
      
      // Сохраняем изменения
      await page.click('[data-testid="save-profile-button"]');
      
      // Проверяем, что изменения сохранились
      await expect(page.locator('[data-testid="user-name"]')).toContainText('New Name');
    });

    test('should change password', async ({ page }) => {
      // Нажимаем кнопку смены пароля
      await page.click('[data-testid="change-password-button"]');
      
      // Заполняем форму смены пароля
      await page.fill('[data-testid="current-password-input"]', 'password123');
      await page.fill('[data-testid="new-password-input"]', 'newpassword123');
      await page.fill('[data-testid="confirm-new-password-input"]', 'newpassword123');
      
      // Сохраняем новый пароль
      await page.click('[data-testid="save-password-button"]');
      
      // Проверяем успешную смену пароля
      await expect(page.locator('[data-testid="success-message"]')).toContainText('Пароль успешно изменен');
    });
  });

  test.describe('Subscription Management', () => {
    test.beforeEach(async ({ page }) => {
      // Логинимся и переходим в раздел подписок
      await page.goto(`${BASE_URL}/login`);
      await page.fill('[data-testid="email-input"]', 'test@example.com');
      await page.fill('[data-testid="password-input"]', 'password123');
      await page.click('[data-testid="login-submit"]');
      await page.waitForURL(/.*dashboard/);
      await page.click('[data-testid="nav-subscription"]');
    });

    test('should display subscription plans', async ({ page }) => {
      // Проверяем наличие планов подписки
      await expect(page.locator('[data-testid="subscription-plans"]')).toBeVisible();
      await expect(page.locator('[data-testid="free-plan"]')).toBeVisible();
      await expect(page.locator('[data-testid="premium-plan"]')).toBeVisible();
      await expect(page.locator('[data-testid="pro-plan"]')).toBeVisible();
    });

    test('should upgrade to premium plan', async ({ page }) => {
      // Нажимаем кнопку обновления до Premium
      await page.click('[data-testid="upgrade-premium-button"]');
      
      // Проверяем, что открылась форма оплаты
      await expect(page.locator('[data-testid="payment-form"]')).toBeVisible();
      
      // Заполняем тестовые данные карты
      await page.fill('[data-testid="card-number-input"]', '4242424242424242');
      await page.fill('[data-testid="card-expiry-input"]', '12/25');
      await page.fill('[data-testid="card-cvc-input"]', '123');
      
      // Нажимаем кнопку оплаты
      await page.click('[data-testid="pay-button"]');
      
      // Проверяем успешную оплату
      await expect(page.locator('[data-testid="success-message"]')).toContainText('Подписка успешно оформлена');
    });
  });

  test.describe('Error Handling', () => {
    test('should handle 404 errors', async ({ page }) => {
      // Переходим на несуществующую страницу
      await page.goto(`${BASE_URL}/non-existent-page`);
      
      // Проверяем, что отображается страница 404
      await expect(page.locator('h1')).toContainText('404');
      await expect(page.locator('[data-testid="back-home-button"]')).toBeVisible();
    });

    test('should handle network errors gracefully', async ({ page }) => {
      // Переходим на страницу, которая может вызвать сетевую ошибку
      await page.goto(`${BASE_URL}/channels`);
      
      // Симулируем сетевую ошибку
      await page.route('**/api/channels', route => route.abort());
      
      // Проверяем, что отображается сообщение об ошибке
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    });
  });

  test.describe('Responsive Design', () => {
    test('should work on mobile devices', async ({ page }) => {
      // Устанавливаем размер экрана для мобильного устройства
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Переходим на главную страницу
      await page.goto(BASE_URL);
      
      // Проверяем, что мобильное меню работает
      await page.click('[data-testid="mobile-menu-button"]');
      await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
      
      // Проверяем, что все элементы адаптивны
      await expect(page.locator('[data-testid="hero-section"]')).toBeVisible();
    });

    test('should work on tablet devices', async ({ page }) => {
      // Устанавливаем размер экрана для планшета
      await page.setViewportSize({ width: 768, height: 1024 });
      
      // Переходим на главную страницу
      await page.goto(BASE_URL);
      
      // Проверяем, что интерфейс корректно отображается
      await expect(page.locator('[data-testid="hero-section"]')).toBeVisible();
      await expect(page.locator('[data-testid="features-section"]')).toBeVisible();
    });
  });
});
