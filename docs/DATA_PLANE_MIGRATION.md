# Миграция data plane: legacy → канонический контур

**Статус:** в работе (фаза 1–2)  
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

## Фазы и прогресс

| # | Фаза | Срок (ориентир) | Статус |
|---|------|-----------------|--------|
| 1 | Документы + глоссарий + policy + review guidelines | 2–4 д | **Done** (документы); код — флаг + таблицы v0 |
| 2 | Таблицы `raw_events`, `message_versions`, индексы | 4–6 d | **Done** (Alembic `f8e9a0b1c2d3` + модели + `raw_ingestion_service`) |
| 3 | Shadow ingestion (`SHADOW_PIPELINE_ENABLED`), dual-write, метрики | 3–5 d | **In progress** — dual-write для **Telegram web** (`t.me/s`) в `raw_events`; Reddit / Telethon — позже |
| 4 | Review console v0.1 + `review_labels` | 4–7 d | Planned |
| 5 | Extraction слой | 5–8 d | Planned |
| 6 | ExtractionDecision | 2–4 d | Planned |
| 7 | Association engine + `signal_relations` | 6–10 d | Planned |
| 8 | `normalized_signals` + `legacy_signal_id` | 4–6 d | Planned |
| 9 | State machine ЖЦ сигнала | 3–5 d | Planned |
| 10 | Execution models | 5–7 d | Planned |
| 11 | Market outcome engine + `signal_outcomes` | 6–10 d | Planned |
| 12 | Новый scoring контур | 5–8 d | Planned |
| 13 | A/B legacy vs new | 3–5 d | Planned |
| 14 | ML на canonical данных | 1–2 wk | Planned |
| 15 | Prod hardening (секреты, сеть compose, k6, алерты) | параллельно | Частично (см. `PROD_REMEDIATION_PLAN`, CI 60%, E2E gate) |

## Ближайшие задачи (backlog)

1. [x] Зафиксировать этот документ и спутники (policy, review, glossary).
2. [x] Добавить `SHADOW_PIPELINE_ENABLED` в настройки + `env.example`.
3. [x] Миграция + модели `raw_events`, `message_versions`.
4. [x] Dual-write **Telegram web**: `collect_signals_from_channel` → `ChannelScrapeResult.posts` → `persist_shadow_telegram_posts_if_enabled` (scheduler, Celery, `POST /collect/...`). Включать `SHADOW_PIPELINE_ENABLED=true` только после `alembic upgrade head`.
5. [ ] Dual-write Reddit / Telethon (отдельные payload-политики).
6. [x] Базовые метрики Prometheus: `shadow_raw_events_written_total`, `shadow_raw_events_dedup_total`; edits / lag — далее.
7. [ ] Таблица `review_labels` + минимальный internal API.

## Критерии switch-over (все обязательны)

- 100% новых сообщений в raw-слое (при включённом shadow).
- Очередь review не растёт бесконтрольно (SLO по backlog).
- ≥ ~1000 размеченных событий (gold), политика версий зафиксирована.
- `unresolved` стабилен и объясним; linkage update/close — высокая точность на выборке.
- Новый scoring честнее и устойчивее legacy на A/B.
- `MARKET_OUTCOME_POLICY.md` утверждён; CI и деплой без критичных дыр (секреты, порты БД/Redis).

## Не делать на ранних фазах

- ClickHouse, отдельный брокер, «идеальный» OCR, универсальный LLM без review, big bang удаления legacy.
