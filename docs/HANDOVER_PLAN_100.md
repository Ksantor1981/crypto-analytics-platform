# План работ до сдачи проекта пользователям

**Цель:** проект должен работать целиком и соответствовать изначальному ТЗ, чтобы его можно было сдать пользователям.

**Дата ревизии:** март 2026

**Статус (последнее обновление):**
- Фаза 1: 1.1–1.5 ✅
- Фаза 2: 2.1 Prometheus-метрики ✅, 2.2 HANDOVER_CHECKLIST ✅, 2.3 E2E — зафиксирован skip (continue-on-error)
- Фаза 3: 3.1 k6 — скрипт + docs/LOAD_TEST.md ✅, 3.2 Coverage 61% ✅, 3.3 ML accuracy — docs/ML_ACCURACY_DISCREPANCY.md ✅
- PostgreSQL: `alembic upgrade head` + `seed_data.py` — при наличии PostgreSQL

---

## 1. Ревизия: текущее состояние vs ТЗ

### 1.1 Критерии успеха из ТЗ (сводка)

| Критерий | ТЗ | Факт | Статус |
|----------|-----|------|--------|
| Сбор сигналов | TG + Reddit, автоматически | TG (t.me/s) + Reddit, каждые 5 мин | ✅ |
| Парсинг | asset, direction, entry, TP, SL | telegram_scraper + parse_signal_from_text | ✅ |
| Валидация цен | CoinGecko / биржи | price_validator, historical_validator | ✅ |
| Точность каналов | Win rate, Average ROI | metrics_calculator, accuracy, average_roi | ⚠️ ROI/PNL несогласованы |
| Рейтинг + антирейтинг | УТП продукта | GET /channels?sort=accuracy_asc/desc | ✅ |
| ML предсказания | ≥87.2% | XGBoost .pkl, CV 96%, real ~41–67% | ⚠️ |
| Stripe | Checkout + webhook | Реализовано | ✅ |
| Auth | JWT, роли | Реализовано | ✅ |
| Frontend | 9 страниц, responsive | Реализовано, px-3 sm:px-6 | ✅ |
| API время отклика | <200мс | ~100мс | ✅ |
| Coverage тестов | >80% | ~55–59% | ⚠️ |
| Нагрузка | 1000 RPS | Не тестировали | ❌ |
| Доступность | 99.9% | Нет VPS | ❌ |

### 1.2 Что уже сделано (последние сессии)

- Документация пайплайна: `docs/PIPELINE_SIGNALS.md`
- Метрики качества сбора: логи в `collect_signals.run_collection` (raw_posts, parsed_signals, skipped)
- Корпус и тесты парсинга: `tests/data/sample_telegram_messages.json`, `test_scraper.py`
- Авто-добавление источников: `source_discovery.py`, Reddit + Telegram (tgstat), `periodic_source_discovery`
- Авто-деактивация мёртвых каналов: `deactivate_stale_sources` (14 дней без сигналов)
- Health check источников: `periodic_source_health` (раз в сутки)
- Responsive: px-3 sm:px-6 на dashboard, channels, signals, ratings
- CI: backend 55% coverage, frontend build, ml-service, security, E2E (continue-on-error)
- Alembic: миграции в порядке, добавлены поля discovery/health в channels

### 1.3 Пробелы (что мешает сдать пользователям)

1. **Данные и метрики**
   - ROI/PNL: `profit_loss_percentage` vs `profit_loss_absolute` vs `average_roi` — семантика разъезжается
   - Analytics API: при отсутствии подсервисов — неявные 500 вместо 503
   - Seed-скрипт: поля устарели относительно модели `Signal`

2. **Работоспособность «из коробки»**
   - Миграция `c7d8e9f0a1b2` (discovery fields) — нужно применить `alembic upgrade head`
   - Source discovery: Reddit search RSS URL может требовать правки (формат query)
   - При первом запуске без каналов — дашборд пустой; нужен seed или явная подсказка

3. **Наблюдаемость**
   - Нет Prometheus-метрик по пайплайну (входящие → распознанные → записанные → отброшенные)
   - Сложно понять, «сыпется» ли парсер, без просмотра логов

4. **Тесты и CI**
   - E2E: continue-on-error, возможны флаки
   - Load test: k6 не прогнан, RPS не зафиксирован

5. **Документация для пользователя**
   - Нет краткого «как запустить» / «что проверить перед сдачей»
   - Нет чек-листа «готовность к handover»

---

## 2. План работ (по приоритету)

### Фаза 1: Критично для работы (без этого не сдать)

| # | Задача | Результат | Оценка |
|---|--------|-----------|--------|
| 1.1 | Применить миграцию discovery | `alembic upgrade head` выполнен, поля в channels | 5 мин |
| 1.2 | Выровнять ROI/PNL | profit_loss_percentage = %, profit_loss_absolute = abs; average_roi считает одно и то же; тест | 2–3 ч |
| 1.3 | Analytics API: явные 503 | Если channel_metrics_service и др. None — 503 + лог, не 500 | 1 ч |
| 1.4 | Проверить source_discovery | Reddit RSS URL, tgstat — работают или graceful skip; логи | 1 ч |
| 1.5 | Seed/демо-данные | Скрипт создаёт 3–5 каналов + 10–20 сигналов для пустого старта | 1 ч |

### Фаза 2: Стабильность и наблюдаемость

| # | Задача | Результат | Оценка |
|---|--------|-----------|--------|
| 2.1 | Prometheus-метрики пайплайна | Счётчики: signals_collected_raw, signals_parsed_ok, signals_saved, signals_skipped_* | 2 ч |
| 2.2 | Документ «Готовность к сдаче» | docs/HANDOVER_CHECKLIST.md: что проверить, как запустить, что должно работать | 1 ч |
| 2.3 | E2E: стабилизировать или зафиксировать | Либо зелёный CI, либо явный skip с причиной | 0.5 ч |

### Фаза 3: Соответствие ТЗ (желательно)

| # | Задача | Результат | Оценка |
|---|--------|-----------|--------|
| 3.1 | Прогнать k6 load test | Зафиксировать RPS, p95; обновить README/план | 0.5 ч |
| 3.2 | Coverage 60%+ | Добавить тесты или точечно расширить omit; CI 60% | 2–3 ч |
| 3.3 | ML accuracy: документировать расхождение | ТЗ 87.2% vs real 41–67%: причина, план (D1–D4) | 0.5 ч |

### Фаза 4: После VPS (вне текущего scope)

| # | Задача |
|---|--------|
| 4.1 | VPS + домен + SSL |
| 4.2 | Нагрузка 1000 RPS (k6) |
| 4.3 | Мониторинг uptime 99.9% |

---

## 3. Порядок выполнения (рекомендуемый)

1. **1.1** — миграция (сразу)
2. **1.2** — ROI/PNL (критично для корректной аналитики)
3. **1.3** — Analytics 503 (предсказуемость API)
4. **1.4** — проверить discovery (чтобы авто-источники работали)
5. **1.5** — seed для пустого старта
6. **2.1** — метрики пайплайна
7. **2.2** — HANDOVER_CHECKLIST.md
8. **2.3** — E2E
9. **3.1–3.3** — по возможности

---

## 4. Чек-лист «готов к сдаче» (черновик)

Перед передачей пользователям проверить:

- [ ] `docker compose up` или `uvicorn + next dev` — всё поднимается
- [ ] `alembic upgrade head` — без ошибок
- [ ] Главная, дашборд, каналы, рейтинг, сигналы — открываются, данные есть (seed или реальный сбор)
- [ ] Регистрация / вход — работают
- [ ] Stripe checkout (test mode) — создаёт сессию, webhook обрабатывается
- [ ] API /docs — открывается, основные эндпоинты отвечают 200
- [ ] CI — backend tests, frontend build, ml-service — зелёные
- [ ] Нет хардкодных секретов, .env.example заполнен

---

## 5. Итог

**Минимум для сдачи:** фаза 1 (1.1–1.5) + 2.2 (чек-лист).  
**Рекомендуется:** + фаза 2 (метрики, E2E).  
**После VPS:** фаза 4.

**Оценка времени до «можно сдать»:** 6–8 часов работы.
