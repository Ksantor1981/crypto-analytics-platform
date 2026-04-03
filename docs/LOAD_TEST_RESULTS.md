# Load Test Results

## Test Date

- 2026-03-26 (шаблон метрик ниже — обновлять после каждого прогона)
- 2026-04-03 — добавлена таблица метрик; **автоматический прогон k6 в CI пока не подключён** (запуск вручную на стенде).

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
| RPS (устойчивый) | до 1000 (проверка) | _заполнить_ | `k6 run --vus 50 --duration 30s scripts/load-test/k6-load.js` |
| p95 latency | &lt; 200 ms (read) | _заполнить_ | из блока `http_req_duration` в summary k6 |
| Error rate | &lt; 1% | _заполнить_ | `http_req_failed` в summary |
| Дата/коммит | | | |

**Стенд (2026-04-03):** автоматический прогон в этой среде не выполнен: Docker Engine недоступен (EOF при `docker run`), локально `k6` не в PATH. На машине со стендом: установить [k6](https://k6.io/docs/get-started/installation/) или `docker run` образа `grafana/k6`, задать `BASE_URL` (например `https://staging.example.com`), выполнить команды из колонки «Команда / env» и перенести цифры в таблицу.

Подставьте сюда вывод k6 после прогона на **реальном** стенде (staging/production-like); без этого требования ТЗ по RPS/latency остаются **недоказанными**.

## Notes

- This document is intentionally versioned so each run can append measured metrics.
