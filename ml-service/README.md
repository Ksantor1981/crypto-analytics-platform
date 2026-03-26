# ML Service

Изолированный микросервис для ML-предсказаний успешности торговых сигналов.

## Стек

- XGBoost, scikit-learn
- NumPy, Pandas
- FastAPI (inference API)

## Воспроизводимость: train-скрипт

Обучение по данным из БД (без API и токена).

### Вариант 1: из корня проекта (рекомендуется)

**Важно:** команды выполняйте из папки **crypto-analytics-platform** (корень проекта). Не из `c:\project` и не из `ml-service`.

```powershell
cd c:\project\crypto-analytics-platform

# Зависимости ML (один из вариантов):
pip install -r ml-service/requirements-train.txt
# Если нужен полный ml-service (FastAPI и т.д.): pip install -r ml-service/requirements.txt

# Запуск обучения (DATABASE_URL из backend)
python backend/scripts/run_ml_train.py
```

На Windows, если `pip install -r ml-service/requirements.txt` падает с ошибкой компиляции (numpy/pandas), используйте только зависимости для обучения: **`pip install -r ml-service/requirements-train.txt`** — все пакеты с готовыми колёсами.

Если вы сейчас в `ml-service`:
```powershell
cd ..
pip install -r ml-service/requirements-train.txt
python backend/scripts/run_ml_train.py
```

### Вариант 2: только из папки ml-service

Пароль и пользователь должны совпадать с теми, что в docker-compose или в backend `.env`. Не подставляйте буквально фразу «ВАШ_ПАРОЛЬ» — укажите реальный пароль.

Пример для `docker-compose.simple.yml` или любого compose — возьмите `POSTGRES_USER` / `POSTGRES_PASSWORD` из корневого `.env` и подставьте в URL (на хосте хост = `localhost`):
```powershell
cd ml-service
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql://ИМЯ:ПАРОЛЬ@localhost:5432/crypto_analytics"
python train_from_db.py
```

Если используете основной `docker-compose.yml`, те же переменные из `.env`:
```powershell
$env:DATABASE_URL = "postgresql://ИМЯ_ПОЛЬЗОВАТЕЛЯ:ПАРОЛЬ@localhost:5432/crypto_analytics"
```

**Важно:** при запуске скрипта **на хосте** (не в контейнере) всегда указывайте хост **`localhost`**, а не `postgres`. Имя `postgres` работает только внутри Docker-сети.

### Вариант 3: отдельный venv для ml-service

Скрипт `run_ml_train.py` сам подхватит `ml-service/.venv`, если он есть:

```powershell
cd ml-service
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
cd ..
python backend/scripts/run_ml_train.py
```

**Что делает `train_from_db.py`:** см. также `docs/ML_DATA_INTEGRITY_ROADMAP.md`.
- Читает `signals` + `channels`; при PostgreSQL и наличии таблицы **`technical_indicators`** подтягивает **RSI/MACD** (JOIN по символу и времени сигнала, таймфрейм `ML_INDICATOR_TIMEFRAME`, по умолчанию `1d`).
- Сортировка **`created_at ASC`** для осмысленного `TimeSeriesSplit`.
- При **≥15 закрытых** сигналах обучение **только** на TP/SL/EXPIRED; иначе — слабые прокси-метки для PENDING (с предупреждением в отчёте).
- **Аугментация выключена** по умолчанию (`ML_AUGMENT_TARGET=0`). Синтетический fallback только при `ML_SYNTHETIC_FALLBACK=1`.
- Отчёт: `indicator_coverage_percent`, `warnings`, дисклеймер про CV.

**Альтернатива с `real_signals`:** `python train_from_real_signals.py` (после заполнения `real_signals` и индикаторов).

**Признаки:** confidence, risk_reward, price_dev, direction, **rsi, macd** (из БД или плейсхолдер), ch_accuracy, ch_signals

## Inference

```bash
python -m uvicorn main:app --reload --port 8001
```

- `POST /predict` — предсказание по признакам
- Интеграция с backend через `POST /api/v1/predictions/ml-predict`

## Структура

```
ml-service/
├── main.py           # FastAPI app
├── train_from_db.py  # Reproducible train script
├── models/
│   ├── trained_predictor.py  # Загрузка .pkl, predict()
│   └── ensemble_model.py     # EnsemblePredictor (опционально)
└── requirements.txt
```
