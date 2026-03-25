# Ревизия: что поправить

**Дата:** март 2026

---

## 1. Критичные (ломают работу)

### 1.1 API-клиент: отсутствующие методы

**Файл:** `frontend/lib/api.ts`

| Метод | Используется в | Статус |
|-------|----------------|--------|
| `getSubscriptionPlans()` | pricing.tsx | ❌ Нет — страница падает или использует только defaults |
| `getSignalsWithTotal()` | profile.tsx | ❌ Нет — профиль может падать при загрузке статистики |

**Решение:** Добавить в `lib/api.ts`:
```ts
async getSubscriptionPlans() {
  const { data } = await api.get('/api/v1/subscriptions/plans');
  return data;
},
async getSignalsWithTotal(channelId?: string, limit = 1000) {
  const params: Record<string, string> = { limit: String(limit) };
  if (channelId) params.channel_id = channelId;
  const { data } = await api.get('/api/v1/signals/', { params });
  return { signals: data?.signals ?? [], total: data?.total ?? 0 };
},
```

**Примечание:** Backend `/api/v1/signals/` требует auth. Profile вызывается после входа — ок. Subscriptions/plans — публичный или auth?

---

### 1.2 API signals: неверные параметры

**Файл:** `frontend/lib/api.ts` — `getSignals()`

- Frontend передаёт `page`, backend ожидает `skip` и `limit`.
- Нужно: `skip: (page - 1) * limit` при пагинации.

---

## 2. Важные (UX / консистентность)

### 2.1 Кнопки без обработчиков

| Страница | Кнопка | Действие |
|----------|--------|----------|
| dashboard | «Обновить план» | Добавить `onClick={() => router.push('/subscription')}` |
| dashboard | «Добавить канал» | Добавить `onClick={() => router.push('/channels')}` или открыть модалку |
| dashboard | «Детали» у канала | Добавить `onClick` → `/channels/{id}` |

### 2.2 Страница «Пусто»

- Dashboard уже показывает «Нет отслеживаемых каналов. Добавьте первый канал!» и «Пока нет сигналов.» — ок.
- Проверить signals, ratings при 0 данных — есть ли понятная подсказка.

---

### 2.3 Восстановление пароля: fallback для API URL

**Файлы:** `auth/forgot-password.tsx`, `auth/reset-password.tsx`

- Используют `process.env.NEXT_PUBLIC_API_URL` без fallback.
- При отсутствии переменной URL будет `undefined/...`.
- Добавить: `|| 'http://localhost:8000'`.

---

## 3. Средний приоритет

### 3.1 AlertSystem — mock

**Файл:** `components/notifications/AlertSystem.tsx`

- Использует `mockAlerts` вместо API.
- Варианты: подключить к API уведомлений или временно скрыть/заглушить.

### 3.2 Два API-клиента

- `lib/api.ts` — основной (axios)
- `lib/api/index.ts` — альтернативный (fetch)

Импорты идут из `@/lib/api` → обычно резолвится в `lib/api.ts`. Имеет смысл оставить один источник правды и перенести недостающие методы в `lib/api.ts`.

### 3.3 Документация

- `READINESS_IMPROVEMENTS.md` — устарела (useUserLimits уже через API).
- Обновить чек-листы и статусы.

---

## 4. Низкий приоритет / после VPS

- Stripe checkout — ручная проверка с `STRIPE_SECRET_KEY`.
- Webhook — нужен ngrok/публичный URL.
- ML-сервис на 8001 — fallback при недоступности.
- k6 load test, uptime 99.9%.

---

## 5. Чек-лист для быстрого фикса

- [x] Добавить `getSubscriptionPlans` и `getSignalsWithTotal` в `lib/api.ts`
- [x] Исправить пагинацию signals (skip вместо page)
- [x] Кнопки dashboard: «Обновить план», «Добавить канал», «Детали»
- [x] Fallback API URL в forgot-password, reset-password
- [x] Обновить READINESS_IMPROVEMENTS.md
- [x] HANDOVER_CHECKLIST: отметить auth как проверенный
