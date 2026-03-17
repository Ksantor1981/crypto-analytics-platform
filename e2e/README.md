# E2E тесты (Playwright)

```bash
# Установка
npm install

# Запуск (backend + frontend должны быть запущены)
npx playwright test

# С UI
npx playwright test --ui

# headed
npx playwright test --headed
```

В CI E2E запускаются автоматически (job `e2e`, `continue-on-error: true` — возможны флаки из‑за таймаутов/сети).
