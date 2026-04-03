# Глоссарий канонического контура (data plane)

**Назначение:** единая терминология до массового кода таблиц и API.  
**Дата:** 2026-04-04

## Сущности

| Термин | Смысл |
|--------|--------|
| **RawEvent** | Неизменяемый (логически write-once) факт доставки сообщения из источника; сырой payload и идентификаторы платформы. |
| **MessageVersion** | Снимок текста/медиа на момент наблюдения; правки канала = новая версия, не overwrite. |
| **Extraction** | Результат парсинга (rules/LLM/hybrid) с версией экстрактора и confidence. |
| **ExtractionDecision** | Итог классификации контура: signal / update / close / commentary / duplicate / noise / unresolved. |
| **NormalizedSignal** | Каноническое представление торгового намерения; связь с `raw_event_id`, опционально `legacy_signal_id`. |
| **SignalRelation** | Связь между сигналами: duplicate_of, update_to, close_of (расширяемо). |
| **ExecutionModel** | Правила входа, проскальзывания, комиссий, экспирации для расчёта outcome. |
| **SignalOutcome** | Результат по рынку для пары (normalized_signal, execution_model). |
| **SourceScore** | Агрегат качества источника из канонических данных + relations + outcomes. |
| **ReviewLabel** | Ручная разметка ревьюера для обучения и контроля качества. |

## Оси статусов (не смешивать в одном поле)

### `classification_status` (пример значений)

| Значение | Описание |
|----------|----------|
| `PARSED` | Есть структурированный extraction |
| `AMBIGUOUS` | Несколько трактовок |
| `NOISE` | Не торговое сообщение |
| `UNRESOLVED` | Недостаточно данных для классификации |

### `relation_status`

| Значение | Описание |
|----------|----------|
| `UNLINKED` | Нет привязки к другому сигналу |
| `CANDIDATE` | Кандидаты на связь, нужен review или правило |
| `LINKED` | Подтверждённая связь |
| `CONFLICT` | Противоречивые кандидаты |

### `trading_lifecycle_status` (канон, ориентир)

`PENDING_ENTRY`, `ACTIVE`, `PARTIALLY_CLOSED`, `COMPLETED_TP`, `COMPLETED_SL`, `CANCELED`, `EXPIRED`, `DELETED_BY_AUTHOR` (уточняется в state machine фазы 9).

### `author_action_status`

`ORIGINAL`, `EDITED`, `DELETED`, `FORWARDED` (и др. по мере необходимости).

## Типы связей `SignalRelation` (MVP)

| `relation_type` | Назначение |
|-----------------|------------|
| `duplicate_of` | Дубликат того же события/контента |
| `update_to` | Обновление уровней/контекста исходного сигнала |
| `close_of` | Закрытие / выход по исходному сигналу |

## Версионирование

- Каждый **Extraction** несёт `extractor_version` (semver или monotonic string).
- Пересчёт downstream при смене версии — отдельный job; старые строки сохраняются для аудита.

## Связь с legacy

- Таблица `signals` и текущий парсер остаются до switch-over.
- Поле `legacy_signal_id` в `normalized_signals` (когда появится таблица) — для склейки истории и A/B.
