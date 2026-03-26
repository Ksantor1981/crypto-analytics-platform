# Helm chart: crypto-analytics-platform

Канонический chart для Kubernetes — только каталог `helm/`. Дубликат `infrastructure/helm/` удалён как небезопасный (в нём были захардкоженные креды в шаблонах).

## Установка

1. Скопируйте `values.yaml` в свой файл (не коммитьте в git), заполните пустые поля:

   - `backend.env.DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`
   - `mlService.env.DATABASE_URL`
   - `workers.env.*`
   - `postgres.env.POSTGRES_PASSWORD`
   - `redis.password` (и тот же пароль внутри `REDIS_URL`)

2. Проверка рендера:

   ```bash
   helm template crypto-analytics . -f your-values.yaml
   ```

3. Для проверки в CI используется только `values.ci.yaml` (фиктивные значения).

## Redis

В `deployment-redis.yaml` включён `--requirepass`; без `redis.password` в values установка завершится ошибкой `required`.
