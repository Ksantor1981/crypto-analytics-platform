# Review Console: руководство v0.1

**Статус:** спецификация до реализации UI/API.  
**Дата:** 2026-04-04  
**Связано:** `docs/DATA_PLANE_MIGRATION.md` (фаза 4)

## Цель

Дать внутренним ревьюерам инструмент **до** масштабирования нового ML: разметка спорных сообщений, золотой датасет, обратная связь в extraction/association.

## Объём v0.1 (MVP)

- Просмотр **RawEvent** + текущих **MessageVersion** + соседних сообщений канала (контекст).
- Кнопки классификации (маппинг на `ExtractionDecision` / `ReviewLabel.label_type`):
  - `signal`, `update`, `close`, `commentary`, `duplicate`, `noise`, `unresolved`
- Сохранение **ReviewLabel** с опциональными `corrected_fields` (JSON), `notes`, `linked_signal_id` (legacy или будущий normalized id).

## Таблица `review_labels` (план)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | PK | |
| `raw_event_id` | FK | На `raw_events` |
| `reviewer` | string / user_id | Кто разметил |
| `label_type` | enum/string | Одно из значений кнопок |
| `corrected_fields` | JSONB | Исправленные поля extraction |
| `linked_signal_id` | int nullable | Связь с legacy `signals.id` при необходимости |
| `notes` | text | Свободный комментарий |
| `created_at` | timestamptz | |

*Реализация Alembic — в фазе 4.*

## Очередь ревью (приоритет)

1. Низкая уверенность extraction / пустой тикер / пустой side.
2. Только изображение без текста (после базового OCR — в очередь).
3. Сообщение отредактировано (`MessageVersion.version_no > 1`).
4. Relation confidence в «серой зоне» (например 0.5–0.9) — когда появится association engine.

## Правила качества разметки

- При сомнении — **`unresolved`**, не угадывать.
- `duplicate` только при явном совпадении контента/ссылки на тот же trade idea.
- `update` / `close` — по возможности указать связанный сигнал в `linked_signal_id` или в поле для canonical id позже.

## Acceptance (фаза 4)

- 300–500 размеченных событий вручную на пилотных каналах.
- Экспорт выборки для обучения/метрик precision/recall extraction.
- Аудит: кто и когда менял метку (минимум `reviewer` + `created_at`).

## Безопасность

- Доступ только ролям internal/admin; raw payload может содержать PII — не логировать в открытые каналы.
