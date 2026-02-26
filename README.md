# Crypto Analytics Platform

Платформа анализа криптовалютных торговых сигналов из Telegram-каналов и Reddit с ML-предсказаниями и Stripe-подписками.

**Статус:** MVP. Локальная разработка и демо — готовы. Production требует настройки секретов и подключения реальных источников данных.

**Документация:**
- [ТЗ (Техническое задание)](./ТЗ.md) — полные требования, этапы, критерии успеха
- [Соответствие ТЗ](./СООТВЕТСТВИЕ_ТЗ_2026_02_25.md) — актуальный статус реализации (~55%)
- [Аудит архитектора](./docs/ARCHITECT_READINESS_AUDIT.md) — готовность к production

---

## Стек

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, React Query
- **Backend**: FastAPI, SQLAlchemy, Pydantic, PostgreSQL
- **ML**: XGBoost, scikit-learn (trained model `.pkl`)
- **Infra**: Docker, Redis, Celery, Nginx, GitHub Actions CI
- **Payments**: Stripe Checkout + Webhooks
- **Monitoring**: Sentry

## Архитектура

```
Frontend (3000)  ←→  Backend API (8000)  ←→  ML Service (8001)
                          ↓
              PostgreSQL + Redis + Celery
```

## Что делает

1. **Собирает сигналы** из 27 Telegram-каналов и 20 Reddit-сабреддитов (автоматически каждые 15 мин)
2. **Парсит** asset, direction (LONG/SHORT), entry price, TP, SL из текста постов
3. **Валидирует** цены через CoinGecko API (текущие + исторические OHLC)
4. **Рассчитывает accuracy** каналов: TP hit / SL hit за 7 дней
5. **ML-предсказания**: XGBoost модель (CV accuracy 96% ±2.4%)
6. **Рейтинг + антирейтинг** каналов по реальным данным
7. **Stripe подписки**: Free / Premium ($19) / Pro ($49)

## Быстрый старт

```bash
# 1. Инфраструктура
docker compose -f docker-compose.simple.yml up -d  # PostgreSQL + Redis

# 2. Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install bcrypt==4.0.1
SECRET_KEY="your-32-char-key" python -m uvicorn app.main:app --reload --port 8000

# 3. ML Service
cd ml-service && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8001

# 4. Frontend
cd frontend && npm install --legacy-peer-deps && npm run dev
```

## API

- `GET /health` — liveness probe
- `GET /ready` — readiness probe (checks DB)
- `GET /api/v1/channels/` — список каналов с accuracy
- `GET /api/v1/signals/` — сигналы с фильтрацией
- `POST /api/v1/collect/deep-collect` — глубокий сбор из всех каналов
- `POST /api/v1/collect/validate-history` — валидация по историческим ценам
- `POST /api/v1/stripe/create-checkout` — Stripe checkout session
- `GET /api/v1/export/signals.csv` — экспорт в CSV
- `POST /api/v1/predictions/ml-predict` — ML предсказание

Swagger: http://localhost:8000/docs

## Тесты

```bash
cd backend && python -m pytest tests/ -v  # 82 tests
```

## Текущие метрики

- 27 Telegram каналов + 20 Reddit сабреддитов (конфиг в `workers/real_data_config.py`)
- ~150 сигналов (seed data; для реальных — нужны Telegram API ключи в `.env`)
- Accuracy каналов: 41.7% (по seed)
- ML CV accuracy: 96.0% ±2.4% (на валидационном наборе)
- 0 hardcoded secrets в коде
- 82 теста, 0 mock/fake данных

## Структура репозитория

```
backend/          # FastAPI, REST API, JWT auth
frontend/         # Next.js 14, TypeScript, React Query
ml-service/        # XGBoost/scikit-learn, изолированный сервис
workers/           # Celery, сбор из Telegram/Reddit
helm/              # Kubernetes манифесты
monitoring/        # Prometheus, Grafana
docs/              # Документация, отчёты
ТЗ.md              # Техническое задание
```

## Переменные окружения

См. `env.example` в корне. Копировать в `.env` и заполнить:
- `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`
- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` — для реального сбора
- `STRIPE_*` — для подписок

## Deploy

```bash
cp env.example .env  # заполнить секреты
docker compose -f docker-compose.deploy.yml up -d
```

## Лицензия

MIT
