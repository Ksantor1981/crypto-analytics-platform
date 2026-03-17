# Нагрузочное тестирование (k6)

Скрипты для проверки API на нагрузку. Цель по ТЗ: 1000 RPS, p95 < 200 ms.

## Установка k6

- **Windows:** `choco install k6` или скачать с https://k6.io/docs/get-started/installation/
- **Linux:** `sudo gpg -k && sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkeyserver.ubuntu.com --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69` и установка по инструкции с k6.io
- **Docker:** `docker run --rm -i grafana/k6 run - < scripts/load-test/k6-load.js` (из корня репо)

## Запуск

1. Запустите backend: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. В другом терминале:

```bash
# Базовый нагрузочный тест (20 VU, 30s), порог p95 < 200 ms
k6 run scripts/load-test/k6-load.js

# Стресс-тест с ростом до 1000 VU (целевой RPS по ТЗ)
k6 run scripts/load-test/k6-stress.js
```

Опционально: `BASE_URL=http://your-api:8000 k6 run scripts/load-test/k6-load.js`

## Результаты

После прогона зафиксировать в отчёте или в `docs/PLAN_100_TZ_2026.md`:
- **http_reqs** (RPS = http_reqs / duration)
- **http_req_duration** p95, avg
- Успешность порогов (pass/fail)
