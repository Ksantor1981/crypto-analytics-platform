# План устранения проблем готовности к PROD

Документ привязан к **crypto-analytics-platform** (без LLM/SHAP из чужих шаблонов). Статусы: сделано в коде / процесс / вне репозитория.

## Порядок выполнения (кратко)

1. **Фаза A (код):** readiness, ML gateway, CORS, request ID, `session_scope`, CI coverage — см. таблицу ниже.
2. **Фаза A (процесс):** k6 + строки в `LOAD_TEST_RESULTS.md` ([scripts/load-test/README.md](../scripts/load-test/README.md)); синхронизация доков CI.
3. **Фаза A (безопасность):** ротация секретов по [SECURITY_PUBLIC_REPO.md](./SECURITY_PUBLIC_REPO.md) — вручную.
4. **Фаза B:** Stripe идемпотентность webhook (Redis + память) — `stripe_webhook_dedup.py`; далее SLO/алерты, полный k6.
5. **Фазы C–D:** данные/ML roadmap, HA/Celery lock — по мере приоритета.

## Фаза A — уже заложено или частично есть

| Проблема | Действие | Статус |
|----------|----------|--------|
| Readiness только по БД | `/ready` возвращает `checks` (database, redis, ml_service); опционально жёсткий gate через `READINESS_REQUIRE_REDIS` / `READINESS_REQUIRE_ML` | код |
| Каскадные отказы ML | Circuit breaker + повторы HTTP к ML-сервису (`app/services/ml_gateway.py`), вызовы из `ml_integration` | код |
| CORS `allow_headers=*` | Список явных заголовков + `expose_headers` для `X-Request-ID` (`main.py`) | код |
| Нет correlation ID | `RequestIDMiddleware` + structlog context (`app/middleware/request_id_middleware.py`) | код |
| Утечка сессии при startup collect | `try` / `finally` + `db.close()` | код |
| Пул сессий в скриптах | `session_scope()` в `database.py` для ручного использования | код |
| Метрики Prometheus | Уже есть `/metrics` | есть |
| k6 / нагрузка | Скрипты + заполнение `LOAD_TEST_RESULTS.md` на стенде | процесс |
| Секреты в истории Git | `SECURITY_PUBLIC_REPO.md` + ротация ключей | процесс |
| Покрытие тестами | Постепенное повышение `--cov-fail-under` в CI | CI |

## Фаза B — 1–2 недели (операционка)

- Ротация всех секретов; секреты только из manager (Vault / cloud), не в compose в открытом виде.
- Полноценный прогон k6 (steady + spike), артефакты в `LOAD_TEST_RESULTS.md`.
- SLO: доступность API, успех Stripe webhook, lag очередей — алерты в Prometheus/Grafana.
- Stripe: тесты idempotency webhook, reconciliation job.

## Фаза C — данные и ML (ядро продукта)

- Roadmap: `ML_DATA_INTEGRITY_ROADMAP.md`, `ML_DATA_EXECUTION_CHECKLIST.md`.
- Минимальный объём размеченных сигналов, OOS/backtest как артефакт релиза.

## Фаза D — инфраструктура

- HA: managed Postgres/Redis или документированный single-node SLA.
- Celery beat: один инстанс или Redis lock (отдельная задача при горизонтальном масштабе).

---

**Версия:** 2026-04-04. Обновлять при закрытии крупных пунктов.
