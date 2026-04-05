# План спринта: довести data plane до измеримого feedback loop

**Статус:** в работе  
**Связано:** `docs/DATA_PLANE_MIGRATION.md`, `docs/TZ_APPENDIX_DATA_PLANE_ACCEPTANCE.md` (п. C5), `docs/WORK_READINESS_CHECKLIST.md`

## Цель спринта

Замкнуть **измеримый контур** «legacy vs канонический слой», чтобы dual-write и материализация не собирали данные «в пустоту».

## Фазы (порядок)

| # | Задача | Критерий готовности |
|---|--------|---------------------|
| 1 | **Отчёт расхождений** legacy `Signal` ↔ `NormalizedSignal` (где задан `legacy_signal_id`) | Admin API + опционально скрипт; агрегаты + выборка примеров |
| 2 | **Метрики Prometheus** по результатам сравнения (счётчик/гистограмма score) | Видно на `/metrics` после вызова отчёта или батча |
| 3 | **Ассоциация (следующий спринт)** | Авто-кандидаты `SignalRelation` + пороги — по `DATA_PLANE_MIGRATION` фаза 7 |
| 4 | **Outcomes / execution models** | Стабильный пересчёт + тест различимости моделей — по G4 приёмки |

## Текущая реализация (фаза 1)

- Сервис: `backend/app/services/shadow_divergence.py`
- API: `GET /api/v1/admin/shadow/divergence-report` (только admin)
- Метрики: `shadow_legacy_divergence_*` в `app/core/metrics.py`

## Как проверить

1. Включить `EXTRACTION_PIPELINE_ENABLED`, пройти материализацию с заполненным `legacy_signal_id` (или тестовые данные).
2. Вызвать отчёт с admin-токеном; убедиться, что `mean_match_score` и `samples` осмысленны.
3. `curl -s localhost:8000/metrics | findstr shadow_legacy` (Windows) или `grep`.

После закрытия приёмки по C5 этот файл можно сократить до одной строки-ссылки в `DATA_PLANE_MIGRATION.md` или удалить по политике команды.
