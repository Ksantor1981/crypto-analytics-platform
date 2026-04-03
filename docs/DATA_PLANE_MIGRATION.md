# Миграция data plane: legacy → канонический контур

**Статус:** в работе (фазы 1–10 по мере готовности; см. таблицу)  
**Дата:** 2026-04-04  
**Связано:** `docs/DOMAIN_GLOSSARY_CANONICAL.md`, `docs/MARKET_OUTCOME_POLICY.md`, `docs/REVIEW_GUIDELINES.md`, `docs/PROD_REMEDIATION_PLAN.md` (ремедиация API/CI — отдельный трек).

## Цель

Построить **параллельный канонический контур** без остановки MVP:

```text
Raw ingestion → MessageVersion → Extraction → ExtractionDecision → NormalizedSignal
  → SignalRelation → ExecutionModel → Outcome → SourceScore → ML
```

Legacy остаётся:

```text
Legacy parser → Signal (текущая модель) → текущие метрики
```

Переключение UI/scoring — только после критериев в разделе «Готовность к switch-over».

## Принципы

1. **Истина:** сырой контент (`raw_events` + версии) и формально зафиксированный market outcome по **execution model** (см. policy).
2. **`NormalizedSignal` — не истина**, а лучшая интерпретация; допускается пересчёт при смене версии экстрактора.
3. **`Unresolved` — норма**, лучше чем ложная нормализация.
4. **Оси состояния не смешивать** — см. глоссарий (`classification_status`, `relation_status`, `trading_lifecycle_status`, `author_action_status`).
5. **Производные слои версионируются** (extractor, relation rules, execution).

## Лестница TP: provenance, extraction, Review

- **Материализация** (`POST /api/v1/admin/normalized-signals/materialize/{extraction_id}`): если в `extractions.extracted_fields` есть `take_profits` с **≥2** валидными числами, они копируются в `normalized_signals.provenance["take_profits"]` (плюс базовые поля `extractor_*`, `extraction_id`). Условия материализации: `EXTRACTION_PIPELINE_ENABLED`, `ExtractionDecision.decision_type == "signal"`, `classification_status == "PARSED"`, в полях есть `asset`, `direction`, `entry_price`.
- **Review Console (admin raw-event detail):** при сборке краткого брифа сигнала сначала берётся `provenance["take_profits"]`; если отсутствует или уровней **меньше двух**, используется запасной вариант — `take_profits` из той же цепочки **`Extraction.extracted_fields`** (дополнительного запроса к БД нет).
- **SQLite** (локально / pytest): у `normalized_signals.id` тип `BigInteger` не даёт автоинкремент как у `INTEGER PRIMARY KEY`; сервис материализации выставляет следующий `id` вручную. На **PostgreSQL** поведение прежнее (идентификатор выдаёт СУБД).

## Фазы и прогресс

| # | Фаза | Срок (ориентир) | Статус |
|---|------|-----------------|--------|
| 1 | Документы + глоссарий + policy + review guidelines | 2–4 д | **Done** (документы); код — флаг + таблицы v0 |
| 2 | Таблицы `raw_events`, `message_versions`, индексы | 4–6 d | **Done** (Alembic `f8e9a0b1c2d3` + модели + `raw_ingestion_service`) |
| 3 | Shadow ingestion (`SHADOW_PIPELINE_ENABLED`), dual-write, метрики | 3–5 d | **In progress** — Telegram web + **Reddit** (RSS + JSON backfill); Telethon — позже |
| 4 | Review console v0.1 + `review_labels` | 4–7 d | **Done (baseline)** — таблица, admin API, UI очереди + карточка (в т.ч. extractions / normalized / relations) |
| 5 | Extraction слой | 5–8 d | **Done (baseline)** — `extractions`, сервис, admin API, `EXTRACTION_PIPELINE_ENABLED` |
| 6 | ExtractionDecision | 2–4 d | **Done (baseline)** — таблица + override/admin |
| 7 | Association engine + `signal_relations` | 6–10 d | **In progress** — таблица + admin + `relation_status`; автоскоринг/очередь кандидатов — далее |
| 8 | `normalized_signals` + `legacy_signal_id` | 4–6 d | **Done (baseline)** — материализация, admin, PATCH legacy-link |
| 9 | State machine ЖЦ сигнала | 3–5 d | **In progress** — `trading_lifecycle_status` + граф переходов + PATCH lifecycle; отдельная ось `author_action_status` — позже |
| 10 | Execution models | 5–7 d | **In progress (v0)** — таблица `execution_models`, сид 3 моделей (`MARKET_OUTCOME_POLICY` §6), admin read-only API `GET /api/v1/admin/execution-models`; связка со строками `signal_outcomes` — фаза 11 |
| 11 | Market outcome engine + `signal_outcomes` | 6–10 d | **In progress (v0)** — таблица `signal_outcomes` (Alembic `m7b8c9d0e1f2`), уникальность (normalized, execution_model), admin `GET/POST ensure`, сервис слотов `PENDING`; расчёт по свечам **v0.2** (multi-TP из `extracted_fields`, `OUTCOME_MOP_REFERENCE`, `OUTCOME_INTRABAR_SL_BEFORE_TP`, `OUTCOME_RECALC_*`, `POST .../recalculate`, `process-pending-recalc`, Celery hourly) |
| 12 | Новый scoring контур | 5–8 d | Planned |
| 13 | A/B legacy vs new | 3–5 d | Planned |
| 14 | ML на canonical данных | 1–2 wk | Planned |
| 15 | Prod hardening (секреты, сеть compose, k6, алерты) | параллельно | Частично (см. `PROD_REMEDIATION_PLAN`, CI 60%, E2E gate) |

## Ближайшие задачи (backlog)

1. [x] Зафиксировать этот документ и спутники (policy, review, glossary).
2. [x] Добавить `SHADOW_PIPELINE_ENABLED` в настройки + `env.example`.
3. [x] Миграция + модели `raw_events`, `message_versions`.
4. [x] Dual-write **Telegram web**: `collect_signals_from_channel` → `ChannelScrapeResult.posts` → `persist_shadow_telegram_posts_if_enabled` (scheduler, Celery, `POST /collect/...`). Включать `SHADOW_PIPELINE_ENABLED=true` только после `alembic upgrade head`.
5. [x] Dual-write **Reddit** (`run_reddit_collection_cycle` + `backfill_reddit_window` JSON).
6. [ ] Dual-write **Telethon** (полный MTProto payload).
7. [x] Базовые метрики Prometheus: `shadow_raw_events_written_total`, `shadow_raw_events_dedup_total`; edits / lag — далее.
8. [x] Таблица `review_labels` + **admin** API + UI Review Console (`/admin/review`).
9. [x] Каталог **`execution_models`** (Alembic `l6f7a8b9c0d1`) + сид `market_on_publish` / `first_touch_limit` / `midpoint_entry` + **admin** `GET /api/v1/admin/execution-models` (и `/by-key/{model_key}`).
10. [x] **`signal_outcomes`** (`m7b8c9d0e1f2`) + `ensure_pending_outcomes_for_normalized` + admin `GET/PATCH /api/v1/admin/signal-outcomes`, `POST .../ensure/{id}`, `POST .../ensure-for-raw-event/{raw_event_id}`, `POST .../{id}/stub-recalculate`; Review карточка отдаёт `signal_outcomes`; опционально `OUTCOME_SLOTS_AUTO_ENSURE` при materialize; опционально `OUTCOME_SLOTS_AUTO_ENSURE_ON_REVIEW_DETAIL` при `GET` карточки review.

## Критерии switch-over (все обязательны)

- 100% новых сообщений в raw-слое (при включённом shadow).
- Очередь review не растёт бесконтрольно (SLO по backlog).
- ≥ ~1000 размеченных событий (gold), политика версий зафиксирована.
- `unresolved` стабилен и объясним; linkage update/close — высокая точность на выборке.
- Новый scoring честнее и устойчивее legacy на A/B.
- `MARKET_OUTCOME_POLICY.md` утверждён; CI и деплой без критичных дыр (секреты, порты БД/Redis).

## Не делать на ранних фазах

- ClickHouse, отдельный брокер, «идеальный» OCR, универсальный LLM без review, big bang удаления legacy.
