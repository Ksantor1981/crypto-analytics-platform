# Backend Scripts

## Alembic autogenerate

Для создания новой миграции при изменении моделей:

```bash
# Локально (требуется PostgreSQL и DATABASE_URL в .env):
cd backend && alembic revision --autogenerate -m "описание_изменений"

# Через Docker (когда стек поднят):
docker compose exec backend alembic revision --autogenerate -m "sync_models"
```

Миграции лежат в `backend/alembic/versions/`.
