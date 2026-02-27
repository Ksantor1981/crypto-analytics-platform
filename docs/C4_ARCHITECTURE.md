# C4 Architecture — Crypto Analytics Platform

## Context (C1)

```
+------------------+     +------------------------+     +------------------+
| Пользователь     |     | Crypto Analytics       |     | Внешние сервисы  |
| (Web/Mobile)     |---->| Platform               |<--->| (Stripe, TG,     |
+------------------+     +------------------------+     |  Reddit, CG)      |
                                                       +------------------+
```

## Container (C2)

```
+----------------------------------+
| Frontend (Next.js)               |
| - Dashboard, Channels, Signals   |
| - Auth, Stripe Checkout          |
+--------+-------------------------+
         |
         v
+----------------------------------+
| Backend API (FastAPI)             |
| - REST endpoints, JWT auth       |
| - Channels, Signals, Users       |
| - Stripe webhook, Export         |
+--------+--------+----------------+
         |        |
         v        v
+----------------+  +------------------+
| ML Service     |  | Workers (Celery) |
| XGBoost predict|  | collect, check   |
+----------------+  +------------------+
         |        |
         v        v
+----------------------------------+
| PostgreSQL | Redis               |
+----------------------------------+
```

## Component (C3) — Backend API

```
/api/v1/
├── auth/          — register, login, JWT
├── channels/      — CRUD, ranking, discover
├── signals/       — list, filter, export
├── users/         — profile, stats
├── subscriptions/  — plans, Stripe
├── collect/       — telethon, recalculate
├── dashboard/     — aggregations
├── feedback/      — user feedback
└── /metrics       — Prometheus
```

## Deployment

```
Docker Compose:
- postgres, redis
- backend (uvicorn)
- frontend (Next.js)
- ml-service
- celery-collect, signal-worker, trading-worker
- prometheus, grafana (monitoring)
```
