# Нагрузочные сценарии (k6)

Порядок из [PROD_REMEDIATION_PLAN.md](../../docs/PROD_REMEDIATION_PLAN.md), фаза A (артефакт нагрузки).

## Подготовка

1. Поднять стек (backend доступен по URL).
2. Установить [k6](https://k6.io/docs/get-started/installation/) **или** Docker:
   ```bash
   docker run --rm -e BASE_URL=https://your-staging.example.com -v "%CD%:/scripts" grafana/k6 run /scripts/k6-load.js
   ```
   (на Windows путь к скриптам подставьте свой.)

## Команды

```bash
set BASE_URL=http://localhost:8000
k6 run --vus 50 --duration 30s scripts/load-test/k6-load.js
k6 run --vus 100 --duration 60s scripts/load-test/k6-stress.js
```

Результаты занести в [docs/LOAD_TEST_RESULTS.md](../../docs/LOAD_TEST_RESULTS.md).
