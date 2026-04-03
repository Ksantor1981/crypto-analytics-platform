.PHONY: up down build rebuild logs ps backend-shell db-shell frontend-shell test ml-data-pipeline

# Docker Compose v2 (Plugin). Старая команда docker-compose (v1) снята с поддержки.
DOCKER_COMPOSE ?= docker compose

# Запуск всех сервисов
up:
	$(DOCKER_COMPOSE) up -d

# Остановка всех сервисов
down:
	$(DOCKER_COMPOSE) down

# Сборка всех сервисов
build:
	$(DOCKER_COMPOSE) build

# Пересборка и запуск всех сервисов
rebuild: down build up

# Просмотр логов
logs:
	$(DOCKER_COMPOSE) logs -f

# Просмотр запущенных контейнеров
ps:
	$(DOCKER_COMPOSE) ps

# Запуск shell в контейнере backend
backend-shell:
	$(DOCKER_COMPOSE) exec backend bash

# Shell в Postgres (пользователь/БД из переменных образа — совпадают с docker-compose.yml по умолчанию)
db-shell:
	$(DOCKER_COMPOSE) exec postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

# Запуск shell в контейнере frontend
frontend-shell:
	$(DOCKER_COMPOSE) exec frontend sh

# Запуск тестов
test:
	$(DOCKER_COMPOSE) exec backend pytest

# Миграции базы данных
db-migrate:
	$(DOCKER_COMPOSE) exec backend alembic upgrade head

# Создание новой миграции
db-revision:
	$(DOCKER_COMPOSE) exec backend alembic revision --autogenerate -m "$(message)"

# Запуск только бэкенда для разработки
backend-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Запуск только фронтенда для разработки
frontend-dev:
	cd frontend && npm run dev

# Фаза C: свечи → индикаторы → real_signals → train (нужен DATABASE_URL в env)
ml-data-pipeline:
	cd backend && python scripts/run_ml_data_pipeline.py
