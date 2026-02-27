#!/bin/bash
# Генерация Alembic миграции при поднятой БД.
# Запуск: ./scripts/alembic_autogenerate.sh [message]
# Или из корня: docker compose exec backend alembic revision --autogenerate -m "sync_models"

cd "$(dirname "$0")/.." || exit 1
MSG="${1:-sync_models}"
alembic revision --autogenerate -m "$MSG"
