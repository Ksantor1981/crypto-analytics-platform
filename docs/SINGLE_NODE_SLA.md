# Single-node / Compose: честный SLA

Для деплоя **один хост + Docker Compose** (без K8s HA) нельзя обещать 99.9% из ТЗ без оговорок. Этот документ фиксирует **реалистичные** ожидания и меры.

## Что реально обеспечивает текущая схема

| Риск | Митигация в репозитории |
|------|-------------------------|
| Два воркера выполняют одну и ту же периодическую задачу | Redis lock в `app/celery_worker.py` (`celery_task_lock`), ключи `celery:lock:collect_all_signals`, `celery:lock:check_signal_outcomes` |
| SPOF PostgreSQL / Redis / один backend | Репликации нет — планируйте бэкапы, `restart: unless-stopped`, мониторинг `monitoring/alert_rules.yml` |
| Потеря машины | RTO/RPO задаются вами: частота бэкапа БД, время восстановления на новый VM |

## Переменные окружения (lock)

- `CELERY_COLLECT_LOCK_TTL` — секунды TTL lock сбора (по умолчанию 1800).
- `CELERY_CHECK_SIGNALS_LOCK_TTL` — TTL проверки исходов (по умолчанию 1700).

При **недоступном Redis** lock не блокирует выполнение (fallback), чтобы dev/single-process не ломался.

## Когда нужен «настоящий» прод-SLA

- Managed PostgreSQL + Redis (или кластеры).
- Несколько реплик stateless backend за балансировщиком.
- Явные SLO в мониторинге + Alertmanager.

См. также: [PROD_REMEDIATION_PLAN.md](./PROD_REMEDIATION_PLAN.md) (фазы B–D).

**Версия:** 2026-04-04.
