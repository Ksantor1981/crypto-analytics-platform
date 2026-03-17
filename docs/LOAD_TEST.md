# Load Test (k6)

**Цель:** проверить RPS и p95 latency по ТЗ (API <200ms, до 1000 RPS).

## Установка k6

**Windows (Chocolatey):**
```bash
choco install k6
```

**Windows (winget):**
```bash
winget install k6 --source winget
```

**Или:** скачать с https://k6.io/docs/getting-started/installation/

## Запуск

1. Запусти backend: `cd backend && uvicorn app.main:app --port 8000`
2. В другом терминале:
```bash
k6 run scripts/load-test/k6-load.js
```

**Опции:**
```bash
k6 run --vus 50 --duration 30s scripts/load-test/k6-load.js
k6 run --vus 100 --duration 60s scripts/load-test/k6-stress.js
```

**Переменные:**
```bash
BASE_URL=http://localhost:8000 k6 run scripts/load-test/k6-load.js
```

## Пороги (thresholds)

- `http_req_duration`: p(95) < 200ms
- `http_req_failed`: rate < 0.01 (1%)

## Эндпоинты в тесте

- `/` — главная
- `/health` — health check
- `/metrics` — Prometheus
- `/api/v1/channels/`
- `/api/v1/dashboard/`
