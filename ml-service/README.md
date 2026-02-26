# ML Service

Изолированный микросервис для ML-предсказаний успешности торговых сигналов.

## Стек

- XGBoost, scikit-learn
- NumPy, Pandas
- FastAPI (inference API)

## Воспроизводимость: train-скрипт

```bash
# 1. Запустить backend (для доступа к API сигналов)
# 2. Обучить модель
python train_from_db.py
```

**Что делает `train_from_db.py`:**
- Загружает сигналы из `GET /api/v1/signals/`
- Feature engineering: rr_ratio, direction, confidence, channel_accuracy
- XGBoost Classifier
- Сохраняет модель в `models/trained_model.pkl`
- Выводит CV accuracy (cross-validation)

**Признаки:** confidence, rr_ratio, price_dev, direction (LONG=1), rsi, macd, channel_acc, channel_sigs

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
