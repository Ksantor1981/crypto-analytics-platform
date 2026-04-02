# Ревизия: статус и оставшиеся задачи

**Последнее обновление:** апрель 2026

Документ заменяет прежний список «что сломано»: критичные пункты ревизии марта 2026 закрыты в коде. Ниже — что сделано, что ещё имеет смысл сделать.

---

## Сделано (закрыто в коде)

| Тема | Детали |
|------|--------|
| **API-клиент** | Один источник: `frontend/src/lib/api.ts` (axios). Удалены дубли `frontend/src/lib/api/index.ts` (fetch) и неиспользуемый `frontend/src/lib/api/channels.ts`. |
| **Методы API** | В `apiClient` есть `getSubscriptionPlans()`, `getSignalsWithTotal()`; `getSignals()` передаёт в backend `skip` и `limit` из `page`/`limit`. |
| **База URL фронта** | `frontend/src/config/env.ts` — `normalizePublicApiUrl()`: при `NEXT_PUBLIC_API_URL=http://localhost:8000` добавляется `/api/v1`. Страницы подписки, forgot/reset и согласованные вызовы не бьют в неверный путь. |
| **Axios origin** | `api.ts` берёт origin из `env` (без дублирования `/api/v1` в baseURL). |
| **Dashboard** | Кнопки «Обновить план», «Добавить канал», «Детали» ведут на `/subscription`, `/channels`, `/channels/[id]`. |
| **Восстановление пароля** | Используется `env.NEXT_PUBLIC_API_URL`, не «голый» `process.env` без fallback. |
| **`<title>` / Head** | Главная и страница канала: один текстовый узел в `<title>` (без лишних children для React). |
| **Rate limit / Redis** | `RateLimitMiddleware`: при недоступном Redis лимит пропускается, без 500. В `main.py` также slowapi. |
| **E2E** | `e2e/full-user-flow.spec.ts` — Stripe mock; `e2e/smoke.spec.ts`; таймауты и сценарий с уникальным пользователем. См. `e2e/playwright.config.ts`. |

---

## Актуальные оставшиеся задачи (по приоритету)

### Средний

- **Пустые списки UX:** явные подсказки на `signals` / `ratings` при нуле данных (dashboard уже поясняет пустые каналы/сигналы).
- **AlertSystem:** в коде нет `mockAlerts`; price alerts ходят в API (`getAnalyticsCurrentPrice`). «Системные алерты» — локальный state; при появлении бэкенда правил — подключить сохранение/список с сервера.
- **READINESS_IMPROVEMENTS.md:** обновить таблицы сценариев (E2E покрывает часть auth/Stripe mock; убрать устаревшее про mockAlerts, если правите файл).

### Низкий / инфраструктура

- Stripe: реальный ключ, webhook (ngrok / публичный URL).
- ML-сервис `:8001` — явный fallback в UI при недоступности.
- Нагрузочное тестирование (k6), целевой uptime.

---

## Архив: что было в ревизии марта 2026

Ранее отмечалось как критичное:

1. Отсутствие `getSubscriptionPlans` / `getSignalsWithTotal` — **исправлено**.
2. Пагинация signals (`skip`) — **исправлено**.
3. Два клиента `lib/api.ts` и `lib/api/index.ts` — **устранено** (оставлен axios).
4. Fallback URL в forgot/reset — **исправлено** через `env`.

---

## Быстрый чек-лист

- [x] Один API-клиент, методы подписки/сигналов
- [x] Нормализация `NEXT_PUBLIC_API_URL`
- [x] Кнопки dashboard
- [x] E2E smoke + full-user-flow (Stripe mock)
- [x] Redis graceful degradation в rate-limit middleware
- [ ] Обновить `READINESS_IMPROVEMENTS.md` под текущие E2E и AlertSystem (по желанию)
- [ ] Прод-Stripe + webhook (после деплоя)
