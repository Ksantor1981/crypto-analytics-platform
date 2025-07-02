.PHONY: up down build rebuild logs ps backend-shell db-shell frontend-shell test

# Запуск всех сервисов
up:
	docker-compose up -d

# Остановка всех сервисов
down:
	docker-compose down

# Сборка всех сервисов
build:
	docker-compose build

# Пересборка и запуск всех сервисов
rebuild: down build up

# Просмотр логов
logs:
	docker-compose logs -f

# Просмотр запущенных контейнеров
ps:
	docker-compose ps

# Запуск shell в контейнере backend
backend-shell:
	docker-compose exec backend bash

# Запуск shell в контейнере базы данных
db-shell:
	docker-compose exec postgres psql -U postgres -d crypto_analytics

# Запуск shell в контейнере frontend
frontend-shell:
	docker-compose exec frontend sh

# Запуск тестов
test:
	docker-compose exec backend pytest

# Миграции базы данных
db-migrate:
	docker-compose exec backend alembic upgrade head

# Создание новой миграции
db-revision:
	docker-compose exec backend alembic revision --autogenerate -m "$(message)"

# Запуск только бэкенда для разработки
backend-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Запуск только фронтенда для разработки
frontend-dev:
	cd frontend && npm run dev
