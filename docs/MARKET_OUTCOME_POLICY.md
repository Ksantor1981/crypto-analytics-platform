# Политика market outcome (черновик v0)

**Статус:** черновик для согласования до фазы 11 (outcome engine).  
**Дата:** 2026-04-04  
**Связано:** `docs/DATA_PLANE_MIGRATION.md`, `docs/ADR_PRICE_DATA_SOURCES.md`

## 1. Зачем документ

Без фиксированных правил **нельзя сравнивать** каналы, execution models и A/B legacy vs canonical. Этот файл — единственный источник семантики для кода расчёта `SignalOutcome`.

## 2. Источник рыночных данных (v0)

| Решение | Статус |
|---------|--------|
| Primary API для котировок на старте | **TBD** (сейчас в продукте активно используется CoinGecko — см. ADR) |
| Резервные источники | TBD |
| Частота обновления свечей / тиков | TBD |

*Заполнить до первого прод-расчёта outcome в canonical контуре.*

## 3. Время и таймзона

| Параметр | Решение |
|----------|---------|
| Все метки времени в БД | UTC (как сейчас в моделях с `timezone=True`) |
| «Момент публикации сигнала» | TBD: время raw_event vs время normalized |
| Выходные дни / maintenance бирж | TBD |

## 4. Price at publish

| Вопрос | Решение |
|--------|---------|
| Какая цена считается «на публикации» | **v0.2 в коде:** свеча, содержащая `first_seen_at` raw_event; опорное поле задаётся `OUTCOME_MOP_REFERENCE` (`close` по умолчанию, также `open`, `hl2`, `ohlc4`) |
| Округление | TBD |

## 5. Свечи и разрешение

| Параметр | Решение |
|----------|---------|
| Таймфрейм по умолчанию | TBD (например 1h) |
| Где хранятся свечи до ClickHouse | PostgreSQL / отдельные таблицы (фаза 11) |
| Gap в данных | TBD: помечать outcome как `DATA_INCOMPLETE` vs интерполяция (избегать молчаливой) |

## 6. Execution models (имена и смысл)

| Модель | Кратко |
|--------|--------|
| `market_on_publish` | Вход по цене на момент публикации (определение см. §4) |
| `first_touch_limit` | Первое касание зоны входа по свечам |
| `midpoint_entry` | Вход по середине зоны entry_min/entry_max |

Для **каждой** пары (signal, model) считается **отдельный** `SignalOutcome`.

В БД канонического контура строка хранится в таблице **`signal_outcomes`** (`normalized_signal_id`, `execution_model_id`, статус и поля результата после расчёта). Слоты `PENDING` — `POST /api/v1/admin/signal-outcomes/ensure/{normalized_signal_id}`. Пересчёт по свечам при `OUTCOME_RECALC_ENABLED` — `POST .../signal-outcomes/{id}/recalculate`, пакет — `POST .../process-pending-recalc`, Celery `recalculate_canonical_signal_outcomes`. Заглушка без свечей — `POST .../stub-recalculate` → `DATA_INCOMPLETE` + `error_detail`. Ручные правки — `PATCH .../signal-outcomes/{id}`.

**Несколько TP (v0.2):** уровни собираются из `take_profit` нормализованного сигнала и `extractions.extracted_fields` (массивы `take_profits` / `tp_levels` / `targets`, скаляры `tp2` / `tp2_price` и аналоги). На свечах — последовательное касание (LONG: цели по возрастанию цены). На одной свече при конфликте SL и TP порядок задаётся `OUTCOME_INTRABAR_SL_BEFORE_TP` (`true` = консервативно: сначала SL).

**Review / UI:** для отображения лестницы TP в карточке review приоритет у `normalized_signals.provenance["take_profits"]` (если ≥2 уровней после материализации); иначе — тот же массив из `extractions.extracted_fields` (см. `docs/DATA_PLANE_MIGRATION.md`, раздел «Лестница TP»).

## 7. Fill semantics (черновик)

- Проскальзывание: TBD (% от спреда или фикс).
- Комиссии: TBD (включать в PnL или отдельная колонка).
- Частичное исполнение TP: **v0.2** — полная фиксация цепочки в `tp_hits` при проходе цены по уровням на свечах; доли позиции на TP не моделируются.

## 8. Процесс утверждения

1. Заполнить таблицы TBD для v0.
2. Review архитектором + владельцем продукта.
3. Версия документа в git; в коде outcome — ссылка на `policy_version` (строка/semver).

## 9. Согласованность с legacy

До switch-over legacy-метрики продолжают использовать текущие правила (`definitions.md`, `signal_checker`). Canonical outcome **не** обязан совпадать с legacy; сравнение только через явный A/B отчёт.
