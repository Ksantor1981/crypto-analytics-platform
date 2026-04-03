# CI и качество: следующие шаги (приближение к production)

**Дата:** 2026-04-04  

Практические шаги из ревью; выполнять по мере готовности, чтобы не ломать `main`.

## 1. Покрытие тестами

- **Факт (2026-04):** в `.github/workflows/ci.yml` для backend задано `--cov-fail-under=60`. Локально: `cd backend && set USE_SQLITE=true` (или экспорт) и `pytest tests/ --ignore=tests/test_z_production_integration.py --cov=app --cov-fail-under=60`.
- **Сделано для 60%:** юнит-тесты `trusted_hosts`, `ml_gateway`, `notification_service`, `email_tasks` (`.run()`), `dedup`/`stripe_webhook_dedup`, `service_probes`, `user_service` (моки `Session`).
- **План:** дальше поднимать порог (60 → 65 → …) только когда локально `pytest --cov=app` стабильно выше нового значения (запас ~0.3 п.п. к лучшему).
- **Документ:** актуальный порог дублировать в `docs/TZ_GAPS_REMEDIATION.md` § про покрытие.

## 2. E2E как gate

- **Факт:** для `e2e` в `ci.yml` задано `continue-on-error: false` (регрессии блокируют CI).
- **План:** при флаках — стабилизировать Playwright (тайминги, фикстуры), не отключать gate без причины.

## 3. Нагрузочное тестирование как артефакт

- Прогнать `scripts/load-test/k6-load.js` / `k6-stress.js` на поднятом стеке.
- Зафиксировать RPS, p95, error rate в `docs/LOAD_TEST_RESULTS.md` (см. шаблон таблицы там).

## 4. Контракт API (опционально)

- OpenAPI уже генерируется FastAPI; при росте команды — schemathesis / Dredd против `/openapi.json` в CI.

## 5. Безопасность

- Следовать `docs/SECURITY_AUDIT_RUNBOOK.md` (pre-commit, при необходимости TruffleHog по истории).
