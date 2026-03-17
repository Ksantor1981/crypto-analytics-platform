# Чек-лист готовности к сдаче пользователям

Проверь перед передачей проекта.

---

## Быстрый старт (PowerShell)

```powershell
# 1. Backend (из корня workspace)
cd c:\project\crypto-analytics-platform\backend
pip install email-validator   # если pydantic[email] не подтянул
pip install -r requirements.txt
# Если падает на pandas/numpy (нет C-компилятора): pip install numpy pandas --only-binary :all: && pip install -r requirements.txt

$env:USE_SQLITE="true"; $env:SECRET_KEY="dev-secret-key-32-chars-minimum"
python scripts/seed_data.py   # останови backend, если db занят
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. Frontend (новый терминал)
cd c:\project\crypto-analytics-platform\frontend
npm install --legacy-peer-deps && npm run dev
```

---

## 1. Запуск

- [x] `docker compose -f docker-compose.simple.yml up -d` — PostgreSQL + Redis подняты (или локально)
- [x] `cd backend && USE_SQLITE=true SECRET_KEY=... uvicorn app.main:app --port 8000` — backend стартует
- [x] `cd frontend && npm install --legacy-peer-deps && npm run dev` — frontend на :3000
- [ ] `cd ml-service && pip install -r requirements.txt && uvicorn main:app --port 8001` — ML-сервис (опционально)

## 2. База данных

- [x] **PostgreSQL:** `cd backend && alembic upgrade head` — миграции применены без ошибок
- [x] **PostgreSQL:** `python scripts/seed_data.py` — seed создаёт пользователей, каналы, сигналы (если БД пустая)
- [x] **SQLite (dev):** при `USE_SQLITE=true` create_all создаёт схему; seed работает

## 3. Основные страницы

- [x] Главная (`/`) — открывается
- [x] Дашборд (`/dashboard`) — данные есть (каналы, сигналы или пусто с подсказкой)
- [x] Каналы (`/channels`) — список
- [x] Рейтинг (`/ratings`) — топ/антирейтинг
- [x] Сигналы (`/signals`) — список с фильтрами

## 4. Авторизация

- [ ] Регистрация — работает
- [ ] Вход — работает
- [ ] Профиль — отображается

## 5. API

- [x] `GET /health` — 200 (основной health, не /api/v1/health/)
- [x] `GET /api/v1/channels/` — 200, список
- [x] `GET /api/v1/signals/dashboard` — 200 (публичный; `/signals/` требует auth)
- [x] `GET /docs` — Swagger открывается
- [x] `GET /metrics` — Prometheus-метрики

## 6. Stripe (test mode)

- [ ] Checkout создаёт сессию
- [ ] Webhook обрабатывается (если настроен)

## 7. CI

- [x] `backend`: pytest — зелёный (161 passed)
- [x] `frontend`: npm run build — зелёный
- [ ] `ml-service`: проверка загрузки модели — зелёный

## 8. Безопасность

- [ ] Нет хардкодных секретов в коде
- [ ] `.env.example` заполнен и актуален

## 9. Достоверность данных

- [x] Сигналы и метрики каналов — из БД, не хардкод (см. `docs/DATA_SOURCES.md`)
- [x] Seed вызывает `recalculate_all_channels` — accuracy/ROI считаются из Signal

---

## Фаза 4 (после VPS)

- [ ] k6 load test: 1000 RPS
- [ ] Uptime 99.9% (мониторинг)

---

**Последняя проверка:** 2026-03-17. Backend (SQLite), frontend, seed — OK.

---

## Windows: типичные ошибки

| Ошибка | Решение |
|--------|---------|
| `email-validator is not installed` | `pip install email-validator` или `pip install "pydantic[email]"` |
| `Failed to build pandas` / нет C-компилятора | `pip install numpy pandas --only-binary :all:` затем `pip install -r requirements.txt` |
| `PermissionError: crypto_analytics.db занят` | Остановить backend перед seed. Если данные уже есть — seed пропустит вставку |
| `UNIQUE constraint failed: users.username` | Данные уже в БД (backend держит db). Seed теперь пропускает при db locked |
| Порт 8000 занят | `Get-NetTCPConnection -LocalPort 8000 \| % { Stop-Process -Id $_.OwningProcess -Force }` |
| `cd crypto-analytics-platform\frontend` из backend | Использовать `cd ..\frontend` или `cd c:\project\crypto-analytics-platform\frontend` |
