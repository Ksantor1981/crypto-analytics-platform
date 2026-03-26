# Crypto Analytics Platform

Платформа анализа криптовалютных торговых сигналов из Telegram-каналов и Reddit с ML-предсказаниями и Stripe-подписками.

**Статус:** MVP. Локальная разработка и демо — готовы. Production требует настройки секретов и подключения реальных источников данных.

**Документация:**
- [ТЗ (Техническое задание)](./ТЗ.md) — полные требования, этапы, критерии успеха
- [Соответствие ТЗ](./СООТВЕТСТВИЕ_ТЗ_2026_02_25.md) — актуальный статус реализации
- [План ~99% готовности](./docs/PLAN_99_READINESS.md) — фазы A–D, регрессия
- [Stripe test checkout (smoke)](./docs/STRIPE_TEST_CHECKOUT.md) — проверка оплаты в test mode
- [Закрытие разрывов с ТЗ](./docs/TZ_GAPS_REMEDIATION.md) — ML, coverage, RPS, GA, алерты Pro
- [Аудит архитектора](./docs/ARCHITECT_READINESS_AUDIT.md) — готовность к production  
- [Оценка статуса](./docs/ARCHITECT_STATUS_EVALUATION.md) — технический архитектор (текущее состояние)
- [ML Pipeline](./ml-service/README.md) — train-скрипт, feature engineering, воспроизводимость

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
5. **ML-предсказания**: XGBoost; заявленная CV accuracy ~96% — **не** out-of-sample метрика; возможны temporal leakage и расхождение с реальной точностью (см. `docs/ML_ACCURACY_DISCREPANCY.md`)
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
- `GET /metrics` — Prometheus metrics (для scraping)
- `GET /api/v1/channels/` — список каналов с accuracy
- `GET /api/v1/signals/` — сигналы с фильтрацией
- `POST /api/v1/collect/deep-collect` — глубокий сбор из всех каналов
- `POST /api/v1/collect/validate-history` — валидация по историческим ценам
- `POST /api/v1/stripe/create-checkout` — Stripe checkout session
- `GET /api/v1/export/signals.csv` — экспорт в CSV
- `POST /api/v1/predictions/ml-predict` — ML предсказание

Swagger: http://localhost:8000/docs

### Какой `docker-compose` использовать

| Файл | Когда |
|------|--------|
| `docker-compose.yml` | Основной локальный полный стек (разработка; bind-mount кода). |
| `docker-compose.simple.yml` | Только Postgres + Redis на `127.0.0.1`; backend/ml на хосте. Нужен `.env` с паролями. |
| `docker-compose.deploy.yml` | Упрощённый стек + nginx; БД/Redis только на localhost портах; секреты из `.env`. |
| `docker-compose.production.yml` | Лимиты ресурсов, отдельный `celery-beat`, без bind-mount исходников в примере. |

Дублирующие Helm-деревья: `helm/` и `infrastructure/helm/crypto-analytics/` — разные сценарии упаковки; перед релизом выберите один канон и обновите CI.

### Docker Compose (полный стек)

- Сбор сигналов **непрерывно** в процессе `backend`: asyncio-планировщик (интервалы задаются `COLLECTION_INTERVAL_SECONDS` / `REDDIT_COLLECTION_INTERVAL_SECONDS`, в `docker-compose.yml` по умолчанию **180** с).
- **`AUTO_SEED_DEMO_CHANNELS=false`** в compose — при пустой БД не создаётся длинный список демо-каналов; добавьте каналы через API или `scripts/seed_data.py`.
- **Celery beat** для сбора (`celery-collect`) вынесен в профиль **`celery-beat`**, чтобы не дублировать опрос вместе с планировщиком в backend:  
  `docker compose --profile celery-beat up -d`
- Проверка с хоста после `up`:  
  `python backend/scripts/smoke_real_services.py --base-url http://127.0.0.1:8000`

## Тесты

```bash
cd backend && python -m pytest tests/ -v                    # 85 тестов
cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing  # + coverage
```

## Текущие метрики

- 27 Telegram каналов + 20 Reddit сабреддитов (конфиг в `workers/real_data_config.py`)
- ~150 сигналов (seed data; для реальных — нужны Telegram API ключи в `.env`)
- Accuracy каналов: 41.7% (по seed)
- ML CV accuracy: 96.0% ±2.4% (валидация в train-скрипте; для OOS/leakage см. `docs/ML_ACCURACY_DISCREPANCY.md`)
- 0 hardcoded secrets в коде
- 85 тестов (pytest), pytest-cov в CI

## Структура репозитория (tree -L 2)

```
├── backend/           # FastAPI, REST API, JWT auth
│   ├── app/            # routers, models, services, schemas
│   ├── tests/          # 85 pytest тестов
│   ├── requirements.txt
│   └── alembic/        # миграции БД
├── frontend/           # Next.js 14, TypeScript, React Query
│   ├── src/            # pages, components, hooks
│   ├── package.json
│   └── package-lock.json
├── ml-service/         # XGBoost/scikit-learn, изолированный сервис
│   ├── models/         # trained_predictor, ensemble
│   ├── train_from_db.py # reproducible train скрипт
│   └── requirements.txt
├── workers/            # Celery, сбор из Telegram/Reddit
│   ├── telegram/       # парсеры, коллекторы
│   ├── real_data_config.py
│   └── requirements.txt
├── helm/               # Kubernetes манифесты
├── infrastructure/helm/crypto-analytics/
├── monitoring/         # Prometheus, Grafana
├── nginx/
├── scripts/
├── security/
├── docs/               # Документация, отчёты
├── .github/workflows/   # CI (ci.yml, ci-cd.yml)
├── backend/alembic.ini  # миграции БД (каталог backend/alembic/versions/)
├── docker-compose*.yml
├── env.example
└── ТЗ.md
```

## Зависимости

| Сервис   | Файл |
|----------|------|
| Backend  | `backend/requirements.txt` (+ `requirements-pinned.txt` via script) |
| ML       | `ml-service/requirements.txt` |
| Workers  | `workers/requirements.txt` |
| Frontend | `frontend/package.json` + `package-lock.json` |

## Переменные окружения

См. `env.example` в корне. Копировать в `.env` и заполнить:
- `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`
- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` — для реального сбора
- `STRIPE_*` — для подписок

## Deploy

```bash
cp env.example .env   # заполнить секреты (POSTGRES_*, REDIS_*, STRIPE_*, GRAFANA_* и т.д.)
docker compose up -d  # основной стек: docker-compose.yml
```

Production-вариант (отдельные сервисы и настройки): `docker-compose.production.yml` — поднимать с заполненным `.env` и по необходимости `--env-file`. Альтернативный сценарий: `docker-compose.deploy.yml`.

## Лицензия

MIT
