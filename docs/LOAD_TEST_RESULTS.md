# Load Test Results

## Test Date

- 2026-03-26 (шаблон метрик ниже — обновлять после каждого прогона)
- 2026-04-03 — добавлена таблица метрик; запуск вручную на стенде.
- 2026-04-28 — добавлен staging proof сценарий `k6-staging-proof.js` и ручной GitHub Actions job `k6-staging-proof` (`workflow_dispatch`) с artifact summary.

## Script

- `scripts/load-test/k6-load.js`
- `scripts/load-test/k6-staging-proof.js`
- `scripts/load-test/k6-stress.js`

## Environment

- Local docker stack
- Backend: FastAPI
- DB: PostgreSQL
- Cache: Redis

## Summary

- Baseline smoke load profile is configured and documented.
- For production sign-off, run:
  - `BASE_URL=https://staging.example.com TARGET_RPS=100 DURATION=2m k6 run scripts/load-test/k6-staging-proof.js`
  - `BASE_URL=https://staging.example.com TARGET_RPS=1000 DURATION=5m k6 run scripts/load-test/k6-staging-proof.js`

## Acceptance Criteria

- `p95 < 200ms` for core read endpoints
- `error rate < 1%`
- no OOM/restart in backend containers

## Measured metrics (заполнять после каждого прогона)

| Метрика | Цель ТЗ / ориентир | Значение | Команда / env |
|---------|-------------------|----------|----------------|
| RPS (устойчивый) | до 1000 (проверка) | _заполнить_ | `TARGET_RPS=1000 DURATION=5m k6 run scripts/load-test/k6-staging-proof.js` |
| p95 latency | &lt; 200 ms (read) | _заполнить_ | из блока `http_req_duration` в summary k6 |
| Error rate | &lt; 1% | _заполнить_ | `http_req_failed` в summary |
| Дата/коммит | | | |

**Стенд (2026-04-28):** кодовый контур для proof готов: локально через `make k6-staging`, в GitHub Actions через ручной запуск `CI → Run workflow` с `staging_url`. Фактические цифры RPS/p95 всё ещё нужно получить на реальном staging/production-like URL и занести в таблицу.

Подставьте сюда вывод k6 после прогона на **реальном** стенде (staging/production-like); без этого требования ТЗ по RPS/latency остаются **недоказанными**.

## Notes

- This document is intentionally versioned so each run can append measured metrics.
