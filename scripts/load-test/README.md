# Load testing (k6)

Тесты нагрузки по ТЗ: 1000 RPS, API <200ms.

**Запуск:**
```bash
# Стандартный тест (20 VU, 30s)
k6 run scripts/load-test/k6-load.js

# Stress test (ramp до 1000 RPS)
k6 run scripts/load-test/k6-stress.js

# С указанием URL
k6 run -e BASE_URL=http://prod.example.com scripts/load-test/k6-load.js
```

**Требование:** [k6](https://k6.io/) установлен (`choco install k6` или скачать с k6.io).
