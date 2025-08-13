#!/bin/bash

# Остановить все существующие контейнеры
docker-compose down

# Очистить старые volumes
docker volume prune -f

# Собрать образы
docker-compose build

# Запустить базу данных и создать структуру
docker-compose up -d postgres

# Подождать инициализацию базы данных
sleep 10

# Применить миграции
docker-compose run --rm backend alembic upgrade head

# Запустить все сервисы
docker-compose up -d

# Показать статус
docker-compose ps
