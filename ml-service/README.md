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

**Что делает `train_from_db.py`:**
- Читает сигналы напрямую из БД (signals + channels.accuracy, channels.signals_count)
- Fallback: API `GET /api/v1/signals/` при недоступности БД (нужен TRAIN_API_TOKEN при auth)
- Обучает только при достаточном числе «закрытых» сигналов (TP/SL/EXPIRED), иначе предупреждение
- XGBoost Classifier, сохраняет в `models/signal_model_v{N}_{timestamp}.pkl` и `models/signal_model.pkl`
- Выводит CV accuracy и отчёт в `models/evaluation_report_v{N}.json`

**Признаки:** confidence, risk_reward, price_dev, direction (LONG=1), rsi (placeholder), macd (placeholder), ch_accuracy (из канала), ch_signals (из канала)

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
