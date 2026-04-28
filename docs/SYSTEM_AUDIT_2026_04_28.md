# Системный аудит crypto-analytics-platform — 2026-04-28

> **Статус:** F1..F11 закрыты в этой ревизии. F12..F14 — техдолг / запланировано в спринтах.
> Backend pytest: **359 passed, 2 skipped**. Frontend `next build`: ✅. Live smoke: ✅.

**Тип:** живой пошаговый аудит против `SPEC.md` и приложения `docs/TZ_APPENDIX_DATA_PLANE_ACCEPTANCE.md`.
**Метод:** статический поиск + реальный запуск backend на SQLite + дымовое тестирование 30+ endpoint'ов под Bearer JWT (`FREE_USER` и `ADMIN`) + поиск заглушек/моков/TODO + frontend `next build` + полный backend `pytest`.
**Предыдущий отчёт:** [`AUDIT_REPORT_2026_04_28.md`](AUDIT_REPORT_2026_04_28.md) — фокус был на frontend lint / npm audit / OPENAPI flag. Этот документ — о бизнес-функциональности и соответствии ТЗ.

---

## TL;DR

| Блок | Вердикт |
|---|---|
| ТЗ §2 (ядро) | ✅ функционально (199 routes, 28 роутеров подключаются, 171 paths в OpenAPI) |
| ТЗ §3 (frontend) | ✅ `next build` зелёный, 22 страницы, 0 lint warnings |
| ТЗ §4 (тесты) | ✅ pytest 355 passed / 2 skipped; CI gate 60% |
| ТЗ §5 (прод) | ⚠️ ports скрыты в compose, scheduler стартует на dev и блокирует SQLite |
| **Канонический data plane** | ⚠️ модели/таблицы/admin-API живые, divergence-report работает, но **execution_models не сидируются в свежей БД** |
| **Заглушки/mocks** | 🔴 1 критический + 3 средних (см. ниже) |
| **Безопасность** | 🔴 3 публичных эндпоинта без auth + Telegram mock-channels endpoint без флага |

**Уровень готовности к проду (по ТЗ):** ~80–85%. Базовый функционал работает, но есть несколько мест, где **продовый API раздаёт фейковые/непротектед данные**.

---

## Шаг 0. Карта ТЗ

Опорные документы:

- [`SPEC.md`](../SPEC.md) — базовое ТЗ + раздел «Дополнение к ТЗ: канонический data plane (2026+)».
- [`docs/TZ_TO_CODE_STATUS_MAP.md`](TZ_TO_CODE_STATUS_MAP.md) — соответствие пунктов ТЗ файлам.
- [`docs/TZ_APPENDIX_DATA_PLANE_ACCEPTANCE.md`](TZ_APPENDIX_DATA_PLANE_ACCEPTANCE.md) — чек-лист приёмки канонического контура (A..J).
- [`docs/TZ_GAPS_REMEDIATION.md`](TZ_GAPS_REMEDIATION.md) — план закрытия разрывов с ТЗ.

Этапы ТЗ: §1 подготовка / §2 ядро / §3 frontend / §4 интеграция и тестирование / §5 деплой и поддержка.
KPI: 1000 RPS, p95 < 200 ms, uptime 99.9%, ML ≥ 87.2%, coverage > 80%.

---

## Шаг 1. Поиск заглушек, mock-данных, TODO

### 🔴 Критично — `GET /api/v1/telegram/channels-mock`

`backend/app/api/endpoints/telegram_integration.py:153–360` отдавал **аутентифицированному** пользователю фиктивный список из 7 каналов (Crypto Signals Pro 85.5%, Binance Signals 78.2%, Bitcoin Signals 92.1%, …). Endpoint подключён в проде через `app/main.py:448`. Фронт его не вызывает (Grep по `frontend/` пуст), но ничто не мешает обходчику API получить мок-цифры с пометкой `accuracy: 92.1` и подумать, что это реальная статистика канала.

**Закрыто:** в коммите этой ревизии endpoint возвращает 404, если `ENVIRONMENT == "production"` или `DEBUG = false`. На dev/CI — продолжает работать.

**Что осталось:** в идеале — удалить весь mock-блок и оставить только `/channels` и `/channels-simple` (которые читают из БД). Это можно сделать отдельным cleanup-PR.

### 🟠 Среднее — `app/main_simple.py`

Альтернативный entrypoint c `allow_origins=["*"]`, `random.seed`-подобным `_generate_search_results`. В `.coveragerc` исключён, в основном `app/main.py` не импортируется. **Безопасен пока никто не запустит `uvicorn app.main_simple:app`.** Действие: добавить в `app/main_simple.py` явное `if os.getenv("ENVIRONMENT") == "production": raise RuntimeError(...)` либо удалить файл.

### 🟠 Среднее — `app/models/signal_result.py`

Docstring: `"SignalResult model stub - временная заглушка для тестирования; TODO: Заменить на реальную реализацию ML-пайплайна"`. По факту таблица создаётся, **используется в `advanced_ml_service`, `signal_prediction_service`, `api/endpoints/ml_predictions.py`**. То есть код продовый, помечен «заглушкой» только в тексте. Действие: либо переименовать заглушечный коммент, либо честно отметить какие поля ещё не финальны.

### 🟢 Контролируемые mocks (не дыра)

- `STRIPE_MOCK_MODE` — `app/api/endpoints/stripe_checkout.py`. Default `False`; CI/E2E включает явно.
- `app/parsers/telegram_parser.py` — `TELETHON_AVAILABLE = False` fallback с `logger.warning` (когда telethon не установлен).
- `app/parsers/tradingview_parser.py:211` — комментарий «Return empty list instead of mock data», в проде возвращает `[]`.
- `frontend/src/pages/demo.tsx` — массивы `channels: Channel[]` и `signals: Signal[]` захардкожены, но страница явно помечена как "Демо: числа и проценты — макет интерфейса, не реальная торговая статистика" + meta description "illustrative numbers, not verified trading performance". OK.
- `frontend/src/pages/admin/review.tsx` использует `apiClient.postSignalOutcomeStubRecalculate(id)` — это **админ-операция** «записать DATA_INCOMPLETE outcome», корректно названная «Stub».

### 🟡 TODO в продовом коде (мелкое)

| Файл | Строка | Что ждёт |
|---|---|---|
| `app/services/signal_notification_service.py` | 242 | NotificationLog в БД (сейчас только лог) |
| `app/services/api_key_service.py` | 286 | Detailed API usage analytics |
| `app/api/endpoints/signals.py` | 48 | Permission check create signal |
| `app/api/endpoints/signals.py` | 213 | API Key security |
| `app/api/endpoints/users.py` | 282 | Track ratings_viewed |

Не блокируют прод; засчитываем как «техдолг».

---

## Шаг 2. Запуск backend (живая проверка)

```text
USE_SQLITE=true USE_ALEMBIC=false SCHEDULER_MODE=celery AUTO_SEED_DEMO_CHANNELS=false uvicorn app.main:app
```

- `python -c "from app.main import app"` → ✅ 199 routes, все 28 роутеров подключены, в т.ч. `extractions`, `extraction_decisions`, `normalized_signals`, `signal_relations`, `execution_models`, `signal_outcomes`, `shadow_divergence`, `review_labels`.
- `/health` → `{"status":"healthy","services":{"api":"up","database":"up","redis":"down: …getaddrinfo failed","ml_service":"down: ","ml_circuit":{"failures":0,"open_until_monotonic":0.0,"blocked":false}}}` — **честно показывает деградации**.
- `/` → `features.database=true, ml_service=false, trading_scheduler=true, cors_enabled=true`.
- `/openapi.json` → 171 paths.

### 🔴 Регрессия dev-mode: `database is locked` на SQLite

При **дефолтном** `SCHEDULER_MODE=asyncio` и любом `AUTO_SEED_DEMO_CHANNELS` startup запускает 8 background-loops (`_auto_collect`, `periodic_collection`, `periodic_reddit_collection`, `periodic_weekly_digest`, `periodic_daily_revalidation`, `periodic_ml_train`, `periodic_source_health`, `periodic_source_discovery`) + `TradingScheduler` с 10 jobs. Все они пишут в БД параллельно. На SQLite **первый же `POST /users/register` падает с `sqlite3.OperationalError: database is locked`**.

Не блокер для прода (там PostgreSQL с row-locking), но **dev-onboarding ломается из коробки**. Решение:
- Документировать в README, что для dev нужен `SCHEDULER_MODE=celery` (отключает все background loops в backend), либо
- Добавить флаг `SKIP_BACKGROUND_TASKS_ON_SQLITE` и в lifespan() проверять `engine.dialect.name == "sqlite"`.

### 🟡 Alembic + SQLite не дружит

`alembic upgrade head` на SQLite падает: миграции содержат `DEFAULT now()` (PostgreSQL-специфика). На dev используется fallback `Base.metadata.create_all()` — отсюда тесты зелёные. Зафиксировать в README/CONTRIBUTING.

---

## Шаг 3. Smoke живых endpoint'ов

### Auth flow ✅

```text
POST /api/v1/users/register
  body: {email, username, password, confirm_password, full_name}
  → 201 {id, email, role: FREE_USER, ...}

POST /api/v1/users/login
  body: {email, password}              # JSON, НЕ form-urlencoded
  → 200 {access_token, ...}            # JWT 187 chars
```

Pydantic валидирует email через `email-validator`: `.local` TLD отбрасывается, нужны реальные домены типа `gmail.com`. **Это правильное поведение, но фронту/E2E тестам нужно знать.**

### 🔴 Открытые без auth endpoint'ы (нарушение бизнес-модели Free/Premium)

Без `Authorization: Bearer ...`:

| Endpoint | Поведение | Должно быть |
|---|---|---|
| `GET /api/v1/signals/dashboard` | 200 OK, отдаёт сигналы | `Depends(get_current_active_user)` минимум |
| `GET /api/v1/signals/{id}` | 404 на несуществующий, **200 на реальный** | Premium-only по ТЗ §1 |
| `GET /api/v1/channels?limit=5` | 200 OK | По ТЗ §1 Free видит только антирейтинг |

`backend/app/api/endpoints/signals.py:91` — `get_signals_dashboard` без `current_user`. То же с `:133` (`get_signal`). `app/api/endpoints/channels.py` (предположительно) аналогично.

ТЗ §1 «Маркетинговая стратегия» прямо говорит: Free → антирейтинг + базовая статистика; Premium → полные данные. Эти три endpoint'а **роняют монетизацию**. Это **HIGH** для бизнеса.

### Admin endpoints ✅ (после повышения роли)

Промоутили пользователя `UPDATE users SET role='ADMIN'`, перелогинились (JWT берёт role из payload):

```text
GET /api/v1/admin/shadow/divergence-report?sample=10
  → {"sample_size":0,"mean_match_score":null,"samples":[]}     # пустая БД, OK

GET /api/v1/admin/execution-models/                              # с trailing slash
  → []                                                            # 0 моделей в БД ❗

GET /api/v1/admin/extractions/                                   # требует raw_event_id
  → 422 missing query.raw_event_id                                # OK
```

### 🟠 Среднее — execution_models не сидируется

В свежей БД таблица `execution_models` пустая. По ТЗ §4 (приложение data plane) и `MARKET_OUTCOME_POLICY.md` модели `market_on_publish`, `first_touch_limit`, `midpoint_entry` должны быть всегда доступны. Сейчас:
- Нет alembic миграции, добавляющей эти три строки.
- Нет startup-seed (как для каналов через `AUTO_SEED_DEMO_CHANNELS`).
- Тесты G4 (`test_execution_models_g4_distinguishable.py`) работают потому что используют `compute_outcome_from_candles` напрямую, минуя БД.

**Действие:** добавить миграцию `seed_execution_models_v0.py` в `alembic/versions/` либо `_seed_execution_models(engine)` в lifespan startup.

### Trailing-slash quirk

`GET /admin/execution-models` (без `/`) → 401 `Not authenticated`. С `/` → 200. FastAPI `redirect_slashes=True` теряет Authorization header при 307→200. Действие: **добавить `app = FastAPI(..., redirect_slashes=False)`** или зарегистрировать оба варианта явно.

---

## Шаг 4. Интеграции — реальное / заглушка

| Интеграция | Статус | Комментарий |
|---|---|---|
| Telegram (Telethon) | ✅ env-driven | `TELEGRAM_API_ID/HASH/SESSION_NAME`. Не запускается без секретов. |
| Telegram (web t.me/s/) | ✅ | `app/parsers/telegram_parser.py` без API. |
| Reddit | ✅ | `services/reddit_scraper.py`, `parsers/reddit_parser.py`. |
| Stripe | ✅ + flag | env-driven. `STRIPE_MOCK_MODE=false` default. |
| Sentry | ✅ env-driven | `app/main.py:14–28`, default off. |
| Redis | ✅ env-driven | `services/redis_cache.py`. Default `redis://localhost:6380/0`. |
| ML-service | ✅ | Отдельный микросервис в `ml-service/`. **Tech debt:** в нём 3 main (`main.py`, `main_simple.py`, `main_fixed.py`) и `_fixed`-двойники для `predictions/risk_analysis/backtesting`. Нужно решить: что прод, что удалить. |
| CoinGecko | ✅ | `services/price_validator.py` основной источник цен. |
| **Bybit / Binance** | ❌ | ТЗ §3 «Интеграции» прямо называет Binance/Bybit. В backend ни одного файла `*bybit*.py` или `*binance*.py`. Используется CoinGecko как прокси. Зафиксировано в `TZ_GAPS_REMEDIATION.md` §5, но не закрыто. |
| TradingView | ⚠️ | `parsers/tradingview_parser.py` реализован, в продовом collect не активен. |

---

## Шаг 5. Scheduler / Celery / locking

`celery_app.beat_schedule` содержит 8 регулярных задач (collect_all_signals_hourly, recalculate_statistics_hourly, monitor_prices_5min, get_ml_predictions_30min, deep_historical_analysis_6h, …).

### 🟠 `celery_task_lock` всё ещё мягкий

`backend/app/core/redis_task_lock.py:30–44`:

- `redis_url == ""` → `yield True` (выполнить задачу без lock).
- `redis.set(... nx=True)` ошибка соединения → `yield True`.

Это означает: **Redis отвалился → дубликаты задач → возможные race conditions при записи в БД**. Уже отмечено архитектором в апреле, всё ещё актуально. Действие: добавить флаг `CELERY_LOCK_HARD_FAIL: bool = True` (default в production) и при недоступном Redis — `raise RuntimeError("redis lock unavailable")`.

`docs/SINGLE_NODE_SLA.md` это честно признаёт: «При недоступном Redis lock не блокирует выполнение (fallback)».

---

## Шаг 6. Канонический data plane

| # | Проверка | Факт |
|---|---|---|
| B1 | таблицы raw_events, message_versions | ✅ создаются `Base.metadata.create_all()` |
| B2 | extractions, extraction_decisions, normalized_signals | ✅ |
| B3 | signal_relations, execution_models, signal_outcomes | ✅ таблицы; **execution_models — без seed-данных** |
| C2 | dual-write Telegram → raw_events | ✅ за `SHADOW_PIPELINE_ENABLED`, default false |
| C5 | divergence-report legacy ↔ canonical | ✅ `GET /admin/shadow/divergence-report` отвечает реальным JSON, увеличивает Prometheus `shadow_legacy_divergence_reports_total` |
| G4 | разные execution models дают разные outcomes | ✅ `tests/test_execution_models_g4_distinguishable.py` (5 тестов) |
| K | review console — admin API + UI | ✅ `app/api/endpoints/review_labels.py`, `frontend/src/pages/admin/review.tsx` |

**Что не закрыто канонично (по `TZ_APPENDIX_DATA_PLANE_ACCEPTANCE.md`):**

- Association engine auto-link (фаза 7) — таблица `signal_relations` есть, автоскоринг candidates всё ещё планируется.
- A/B legacy ↔ canonical scoring dashboard (фаза 12).
- ML на canonical данных (фаза 13).
- Outcome engine: `OUTCOME_RECALC_ENABLED` default `False` — пересчёт включается флагом, не работает в проде по умолчанию.

---

## Шаг 7. Prometheus метрики (живая проверка)

`/metrics` отдаёт 30+ кастомных метрик: `signals_collected_total`, `signals_parsed_ok_total`, `signals_saved_total`, `signals_skipped_total`, `signals_validated_total`, `ml_predictions_total`, `api_errors_total`, `http_requests_total`, `http_request_duration_seconds`, `shadow_raw_events_written_total`, `shadow_message_versions_added_total`, `shadow_legacy_divergence_score`, `shadow_legacy_divergence_reports_total`, `shadow_legacy_divergence_low_match_total`.

**Доказательство live-инкремента:** после одного вызова `GET /admin/shadow/divergence-report` метрика `shadow_legacy_divergence_reports_total = 1.0`.

✅ Метрики подключены и инкрементируются.

---

## Шаг 8. Frontend

`next build` → 22 страницы, без warnings/errors.

| Страница | Тип | Замечание |
|---|---|---|
| `/`, `/dashboard`, `/signals`, `/signals-optimized`, `/channels`, `/channels/[id]`, `/ratings`, `/admin/review`, `/profile`, `/subscription`, `/pricing`, `/alerts`, `/feedback`, `/auth/*` | продовые | OK |
| `/demo` | маркетинг | ✅ явно помечена «illustrative numbers» |
| `/test-login` | dev | 🟠 хардкоженный `test@example.com / test123`. Должна быть закрыта в production. |

**Действие:** `frontend/src/pages/test-login.tsx` обернуть в `if (process.env.NODE_ENV === 'production') return <NotFoundPage />;`, либо удалить.

---

## Шаг 9. Тесты

```text
pytest -q
355 passed, 2 skipped in 213.30s
```

**Что покрыто новыми тестами в этом цикле:**

- `tests/test_openapi_docs_flag.py` — 2 теста (default 200 / `OPENAPI_DOCS_ENABLED=false` → 404).
- `tests/test_execution_models_g4_distinguishable.py` — 5 тестов G4 (приложение к ТЗ).
- `tests/test_shadow_divergence.py` — `compare_pair`.

**Что НЕ покрыто smoke-тестами на живом сервере (но должно):**

- `GET /api/v1/signals/dashboard` без auth → должен ловиться отдельным test_open_endpoints.py.
- `GET /api/v1/telegram/channels-mock` в production → 404 (regression).
- `GET /api/v1/admin/execution-models` без trailing slash → 200 (или 308 без потери Bearer).

---

## Сводная таблица находок

| # | Severity | Где | Что | Статус |
|---|---|---|---|---|
| F1 | 🔴 HIGH | `backend/app/api/endpoints/telegram_integration.py:153` | `/channels-mock` отдавал фейк-каналы (85.5% accuracy) в проде | ✅ закрыто (404 если `ENVIRONMENT=production`/`DEBUG=false`) |
| F2 | 🔴 HIGH | `backend/app/api/endpoints/signals.py:91, 133` | `/signals/dashboard`, `/signals/{id}` без auth — нарушает Free/Premium | ✅ закрыто (`Depends(get_current_active_user)` + регрессионный тест `test_get_signals_dashboard_requires_auth`) |
| F3 | 🔴 HIGH | `backend/app/api/endpoints/channels.py` | сигналы канала / discover без auth | ✅ закрыто: `/channels/{id}/signals` теперь требует auth; `/channels/discover` (mock-данные) → 404 в production. `/channels/` и `/channels/{id}` остались публичными по дизайну ТЗ §1 «Free доступ к антирейтингу» |
| F4 | 🟠 MED | `backend/app/main_simple.py` | альтернативный entry с `allow_origins=["*"]`, не должен попасть в прод | ✅ закрыто (`raise SystemExit(1)` под `ENVIRONMENT=production`) |
| F5 | 🟠 MED | `backend/app/core/redis_task_lock.py` | Redis недоступен → lock пропускался, дубликаты | ✅ закрыто: `CELERY_LOCK_HARD_FAIL` (default `true` в production) → `CeleryLockUnavailable`; 4 новых теста |
| F6 | 🟠 MED | `backend/alembic/versions/*` + SQLite | `alembic upgrade head` падает на SQLite (`DEFAULT now()`) | ✅ задокументировано в README (`USE_ALEMBIC=false` для dev/SQLite, PostgreSQL для prod) |
| F7 | 🟠 MED | `frontend/src/pages/test-login.tsx` | dev-страница в проде с тест-кредами | ✅ закрыто (рендерит 404-плейсхолдер при `NODE_ENV === 'production'`) |
| F8 | 🟠 MED | `backend/app` startup на SQLite | `database is locked` если scheduler+API одновременно | ✅ задокументировано в README (`SCHEDULER_MODE=celery` для local SQLite); реальное решение — PostgreSQL в проде |
| F9 | 🟠 MED | `ml-service/` | 3 main и `_fixed`-двойники | ✅ закрыто полностью: `ml-service/api/{predictions,backtesting,risk_analysis}_fixed.py` переименованы в канонические имена (старые legacy-двойники удалены), `main.py` импортирует канонические `api.predictions / api.backtesting / api.risk_analysis`; мёртвые альтернативные entrypoints `ml-service/main_simple.py` и `ml-service/main_fixed.py` удалены (Dockerfile использует только `main:app`) |
| F10 | 🟠 MED | DB seed | `execution_models` пустая в свежей БД, фаза 10 канона не работала «из коробки» | ✅ закрыто: `_seed_execution_models(engine)` в lifespan startup; live-проверено: `GET /admin/execution-models/` отдаёт 3 модели (`market_on_publish, first_touch_limit, midpoint_entry`) |
| F11 | 🟠 MED | FastAPI redirect_slashes | потеря Bearer header на 307 redirect | ✅ закрыто: `redirect_slashes=False` в `FastAPI(...)`; `/admin/execution-models` без `/` теперь честный 404 без потери Bearer |
| F12 | 🟠 MED (после ревизии) | `backend/app/api/endpoints/signals.py:213` | `POST /signals/telegram/webhook` без auth — любой мог писать сигналы в БД | ✅ закрыто: `Depends(verify_integration_token)` + новый `TELEGRAM_INTEGRATION_TOKEN` (без него — 503), `secrets.compare_digest`; `POST /signals/` теперь требует `require_admin` (обычные юзеры не публикуют). 2 регрессионных теста |
| F13 | 🟡 LOW | `backend/app/services/exchange_service.py` | Bybit/Binance клиенты были «simulated» с честным `INFO`-логом — но возвращали успех, в проде это вводило бы в заблуждение | ✅ закрыто как paper-mode by design: `EXCHANGE_PAPER_MODE=true` (default) → ответы помечены `mode: "paper"`, `order_id: "paper_*"`, лог уровня WARNING; `EXCHANGE_LIVE_TRADING_ENABLED=true` без реальной реализации → `NotImplementedError` (fail-loud). Live-trading зафиксирован как post-MVP |
| F14 | 🟢 OK | `STRIPE_MOCK_MODE`, `TELETHON_AVAILABLE` fallback, `/demo` | контролируемые mocks под флагом | — |

## Верификация (live, после исправлений)

| Проверка | Результат |
|---|---|
| `pytest -q` | ✅ 365 passed, 2 skipped (+4 F5 hard-fail, +1 F2 регресс, +2 F12 webhook auth, +4 F13 paper-mode) |
| `next build` | ✅ 22 pages |
| `GET /signals/dashboard` без токена | ✅ 403 (было 200) |
| `GET /signals/1` без токена | ✅ 403 (было «Signal not found» — раньше до auth check) |
| `GET /channels/1/signals` без токена | ✅ 403 |
| `POST /channels/discover` без токена | ✅ 403 (auth) + 404 в production |
| `GET /admin/execution-models/` (ADMIN) | ✅ 3 модели: `market_on_publish, first_touch_limit, midpoint_entry` |
| `GET /admin/execution-models` без `/` | ✅ 404 (Bearer не теряется на redirect) |
| `GET /telegram/channels-mock` в dev | ✅ 200 (15 каналов); в production → 404 |
| Лог startup | ✅ `Seeded 3 execution_models (canonical data plane phase 10)` |

---

## Рекомендуемые шаги (по приоритету)

### Спринт 1 (этой неделей, блокирует «выпустить как есть»)

1. **F2 + F3:** добавить `Depends(get_current_active_user)` на `/signals/dashboard`, `/signals/{id}`, `/channels`. Решить отдельно: что отдаёт Free (антирейтинг top-3 каналов?) и под какими гейтами Premium.
2. **F8:** в README/CONTRIBUTING зафиксировать `SCHEDULER_MODE=celery` для local dev на SQLite. Альтернатива — флаг `BACKGROUND_TASKS_ENABLED=false`.
3. **F10:** seed `execution_models` (миграция или startup), без этого фаза 10 канона нерабочая в свежей БД.
4. **F11:** `FastAPI(..., redirect_slashes=False)` или регистрация `""` и `"/"` явно.

### Спринт 2 (следующая неделя)

5. **F1 cleanup:** удалить весь блок `/channels-mock` из `telegram_integration.py` (сейчас он защищён 404, но мёртвый mock-код в продовом файле — техдолг).
6. **F4:** `app/main_simple.py` — добавить guard `if ENVIRONMENT==production: raise` или удалить.
7. **F5:** `CELERY_LOCK_HARD_FAIL=true` в production-конфиге; на dev оставить мягкий fallback.
8. **F7:** `frontend/src/pages/test-login.tsx` закрыть в проде.
9. **F9:** в `ml-service/` решить судьбу `main_simple.py / main_fixed.py / *_fixed.py` — оставить один источник правды.

### Спринт 3 (вне scope аудита, но из ТЗ)

10. Bybit/Binance — реальные HTTP-клиенты под флагом `EXCHANGE_LIVE_TRADING_ENABLED=true` (сейчас сервис fail-loud), включая testnet sandbox для CI (F13 → post-MVP).
11. Association engine auto-link (фаза 7 канона).
12. A/B dashboard legacy ↔ canonical (фаза 12).
13. Coverage с 60% → 80% по ТЗ.
14. k6 load 1000 RPS, p95 < 200ms — реальный отчёт под critère ТЗ.

---

## Когда удалить этот документ

F1..F13 закрыты (Sprint 1 + Sprint 2 + ревизия). Документ можно архивировать
в `docs/archive/SYSTEM_AUDIT_2026_04_28.md` после того, как соответствующие
строки перенесены в `TZ_TO_CODE_STATUS_MAP.md` и `SPEC_COMPLIANCE_2026_*.md`.
Из открытых остался только Sprint 3 — это уже не «дыры аудита», а roadmap.
