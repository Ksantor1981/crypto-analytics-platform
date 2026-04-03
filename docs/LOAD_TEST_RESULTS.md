# Load Test Results

## Test Date

- 2026-03-26

## Script

- `scripts/load-test/k6-load.js`

## Environment

- Local docker stack
- Backend: FastAPI
- DB: PostgreSQL
- Cache: Redis

## Summary

- Baseline smoke load profile is configured and documented.
- For production sign-off, run:
  - `k6 run --vus 50 --duration 30s scripts/load-test/k6-load.js`
  - `k6 run --vus 100 --duration 60s scripts/load-test/k6-stress.js`

## Acceptance Criteria

- `p95 < 200ms` for core read endpoints
- `error rate < 1%`
- no OOM/restart in backend containers

## Measured metrics (заполнять после каждого прогона)

| Метрика | Цель ТЗ / ориентир | Значение | Команда / env |
|---------|-------------------|----------|----------------|
| RPS (устойчивый) | до 1000 (проверка) | _заполнить_ | |
| p95 latency | &lt; 200 ms (read) | _заполнить_ | |
| Error rate | &lt; 1% | _заполнить_ | |
| Дата/коммит | | | |

Подставьте сюда вывод k6 после прогона на **реальном** стенде (staging/production-like); без этого требования ТЗ по RPS/latency остаются **недоказанными**.

## Notes

- This document is intentionally versioned so each run can append measured metrics.
