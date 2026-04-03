# Custom Alerts (Pro): статус реализации

**Обновлено:** 2026-04-03

## Сделано

- Модель `CustomAlert` расширена: `conditions`, `notification_methods`, `webhook_url`, `triggered_count`; `symbol` и `condition` допускают `NULL` для новых записей.
- Alembic: `e5f6a7b8c9d0_custom_alerts_pro_columns.py` (PostgreSQL).
- Сервис `custom_alerts_service.py` согласован с моделью; исправлены импорты, `db` в `_execute_alert_actions`, сопоставление символов и сравнение confidence.
- REST: `GET/POST/PATCH/DELETE /api/v1/alerts/custom/...`, шаблоны `GET /api/v1/alerts/custom/templates`; роутер подключён в `main.py`.
- RBAC: в `feature_map` добавлен префикс `/api/v1/alerts/custom` **до** общего `/api/`, чтобы не требовать `api_access` вместо `custom_alerts`.
- Тесты: `backend/tests/test_custom_alerts_api.py`.

## Остаётся (эксплуатация)

- Прогнать `alembic upgrade head` на **боевой** PostgreSQL.
- Вызов `trigger_alert_check` при сохранении нового сигнала (если ещё не подключён в пайплайне).
- UI страницы настроек алертов под новые эндпоинты.
