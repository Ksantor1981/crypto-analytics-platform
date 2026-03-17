# Источники данных

## Сигналы и каналы — откуда берутся

| Режим | Источник | Описание |
|-------|----------|----------|
| **Dev (seed)** | `scripts/seed_data.py` | 5 каналов, 5 сигналов с реальными TP/SL/ROI. Метрики пересчитываются из записей Signal. |
| **Production** | Telegram + Reddit | Сбор каждые 5 мин (`collect_signals`), парсинг, валидация цен. |

## Проверка достоверности

- **Сигналы** — из таблицы `signals` (БД). Нет хардкода на фронте.
- **Метрики каналов** (точность, ROI, signals_count) — считаются в `metrics_calculator.py` из реальных Signal.
- **API** — `GET /api/v1/channels/`, `GET /api/v1/signals/` возвращают данные из БД.

Проверка: `curl http://localhost:8000/api/v1/signals/dashboard` — JSON с id, asset, entry_price, status и т.д. из БД.
