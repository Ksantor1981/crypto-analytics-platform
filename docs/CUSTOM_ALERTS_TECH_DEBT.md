# Custom Alerts (Pro): техдолг перед REST-слоем

**Статус:** публичный API для CRUD алертов **не подключён** к `main.py` намеренно до выравнивания слоёв.

## Проблема

- Модель `app/models/custom_alert.py` описывает поля `name`, `symbol`, `condition` (JSON), `status`, …
- Сервис `app/services/custom_alerts_service.py` ожидает другую схему: `conditions`, `notification_methods`, `webhook_url`, `triggered_count`, … и создаёт `CustomAlert(...)` с несуществующими колонками относительно текущей модели.
- В `_execute_alert_actions` используются `db` и `CustomAlert` без гарантированного импорта/скоупа — риск ошибок времени выполнения.

## Рекомендуемый порядок исправления

1. **Один источник правды:** либо привести SQLAlchemy-модель к схеме сервиса (миграция Alembic), либо переписать сервис под актуальную модель.
2. **Тесты** на создание/триггер алерта с SQLite/Postgres в CI.
3. **Роутер** `GET/POST/PUT/DELETE /api/v1/alerts/custom` + RBAC Pro — после п.1–2.

До этого REST для Pro-алертов в документации не позиционировать как готовый.
