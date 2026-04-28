# Чеклист: прод-запуск и безопасность

**Назначение:** что сделать, чтобы выпуск был **рабочим** и без очевидных дыр. Детали процессов — в [`PROD_REMEDIATION_PLAN.md`](./PROD_REMEDIATION_PLAN.md), аудит — в [`SECURITY_AUDIT_RUNBOOK.md`](./SECURITY_AUDIT_RUNBOOK.md), публичный репо — [`SECURITY_PUBLIC_REPO.md`](./SECURITY_PUBLIC_REPO.md).

---

## 1. Секреты и конфигурация

| # | Действие | Зачем |
|---|----------|--------|
| 1.1 | `SECRET_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, Stripe (`STRIPE_*`), Telegram — **уникальные** значения, не из примеров | Компрометация аккаунтов и данных |
| 1.2 | Ротация ключей, когда-либо попавших в git — см. `SECURITY_PUBLIC_REPO.md` | История репозитория публична |
| 1.3 | `ENVIRONMENT=production`, `DEBUG=false` | Не утекать stack trace в ответах |
| 1.4 | `BACKEND_CORS_ORIGINS` — **только** домены вашего фронта (JSON-массив в compose) | Защита от чужих сайтов с браузера пользователя |
| 1.5 | `TRUSTED_HOSTS` при необходимости + домены из CORS — уже собираются в [`trusted_hosts.py`](../backend/app/core/trusted_hosts.py) | Host header attacks |
| 1.6 | `OPENAPI_DOCS_ENABLED=false` в проде (см. `docker-compose.production.yml`) | Меньше поверхность разведки API |

---

## 2. Сеть и доступ к данным

| # | Действие | Зачем |
|---|----------|--------|
| 2.1 | Postgres/Redis **не** слушать `0.0.0.0` в интернет без firewall; лучше только internal Docker network / managed DB. В `docker-compose.production.yml` они уже забиндены на `${POSTGRES_BIND_HOST:-127.0.0.1}` / `${REDIS_BIND_HOST:-127.0.0.1}` — для полного отключения публикации удалите `ports:` блоки. | Прямой доступ к БД |
| 2.2 | Backend за reverse proxy (nginx/Traefik) с **TLS**, редирект HTTP→HTTPS | Перехват трафика |
| 2.3 | Ограничить SSH, при необходимости VPN/bastion для админки | Компрометация хоста |

---

## 3. Приложение (уже заложено в коде)

| Тема | Где |
|------|-----|
| Security headers (X-Frame-Options, nosniff, …) | `main.py` |
| CORS: явный список заголовков, не `*` | `main.py` |
| Rate limit (slowapi + Redis middleware) | `main.py`, `rate_limit_middleware.py` |
| Readiness `/ready` | `main.py` |
| Stripe webhook — проверка подписи | endpoints payments |
| CI: grep запрещённых паттернов в compose/helm, `pip-audit` / `npm audit` | `.github/workflows/ci.yml` |
| Pre-commit + detect-secrets | `.pre-commit-config.yaml` |

---

## 4. Операционка после деплоя

| # | Действие |
|---|----------|
| 4.1 | Мониторинг: Prometheus `/metrics`, алерты — `monitoring/alert_rules.yml`, Grafana |
| 4.2 | Бэкапы Postgres (расписание + тест восстановления) — `docs/DISASTER_RECOVERY.md` при наличии |
| 4.3 | Sentry (`SENTRY_DSN`) для 5xx и необработанных исключений |
| 4.4 | Периодическая сверка Stripe↔БД — `backend/scripts/stripe_reconcile_subscriptions.py` |

---

## 5. Минимальная проверка перед «включаем трафик»

```text
curl -fsS https://<api>/ready
curl -fsS https://<api>/health
# Убедиться, что /docs недоступен или 404, если OPENAPI_DOCS_ENABLED=false
curl -o /dev/null -w "%{http_code}" https://<api>/docs
```

Локальный смоук после compose: `python backend/scripts/smoke_real_services.py`, `make smoke-local`.

---

**Версия:** 2026-04-05. Дополнять по итогам инцидентов и аудитов.
