# Crypto Analytics Platform

Платформа анализа криптовалютных торговых сигналов из Telegram-каналов и Reddit с ML-предсказаниями и Stripe-подписками.

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

- 27 Telegram каналов + 20 Reddit сабреддитов
- ~150 реальных сигналов
- Accuracy: 41.7% (5 TP / 7 SL из 12 resolved)
- ML CV accuracy: 96.0% ±2.4%
- 0 hardcoded secrets в коде
- 82 теста, 0 mock/fake данных

## Переменные окружения

См. `.env.example`

## Deploy

```bash
cp .env.example .env  # заполнить секреты
docker compose -f docker-compose.deploy.yml up -d
```

## Лицензия

MIT
