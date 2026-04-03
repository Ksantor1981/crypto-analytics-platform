# Чеклист: данные и ML (исполнение roadmap)

Краткий порядок работ к целевым KPI из `SPEC.md` и `ML_DATA_INTEGRITY_ROADMAP.md`.

## 0. Оркестрация (одна команда)

Из каталога `backend` при настроенном `DATABASE_URL` (PostgreSQL):

```bash
python scripts/run_ml_data_pipeline.py
python scripts/run_ml_data_pipeline.py --dry-run
```

Порядок шагов: `fetch_market_data` → `calculate_indicators` → `generate_real_signals` → `ml-service/train_from_db.py`.  
Опции: `--skip-fetch`, `--skip-indicators`, `--skip-signals`, `--skip-train`, `--symbols`, `--days`, `--interval`.

В корне репозитория: `make ml-data-pipeline` (см. `Makefile`).

## 1. Данные сигналов

- [ ] Минимум **N** закрытых сигналов (TP/SL/EXPIRED) с корректными `entry_price`, горизонтами и без «вечных» PENDING без политики — см. `SIGNAL_LIFECYCLE_ROADMAP.md`.
- [ ] Заполнение `market_candles` / `technical_indicators` для используемых пар и таймфреймов перед обучением.
- [ ] Разделение train/validation по **времени** (без утечки будущего в фичи).

## 2. Обучение и фиксация

- [ ] `ml-service/train_from_db.py` (или актуальный train-скрипт) с логом в `ml-service/models/evaluation_report*.json`.
- [ ] Версия модели + `manifest.json` после успешного прогона.
- [ ] Обновить `docs/ML_METRIC_LATEST.md` (или аналог) одной строкой: дата, выборка, метрика hold-out.

## 3. Согласование с ТЗ

- [ ] Если hold-out **ниже** 87.2% — зафиксировать в `SPEC_COMPLIANCE` и `TZ_GAPS_REMEDIATION` (цель vs факт).
- [ ] При смене источника цен — `ADR_PRICE_DATA_SOURCES.md`.
