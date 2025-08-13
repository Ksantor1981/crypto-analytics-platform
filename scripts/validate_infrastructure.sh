#!/bin/bash

set -e

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Логирование
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка переменных окружения
check_env_vars() {
    echo "🔍 Проверка переменных окружения..."
    
    required_vars=(
        "POSTGRES_DB"
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "REDIS_URL"
        "SECRET_KEY"
        "DATABASE_URL"
    )

    missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_warning "Отсутствуют переменные окружения:"
        for missing_var in "${missing_vars[@]}"; do
            echo "   - $missing_var"
        done
        log_warning "Рекомендуется создать .env файл с этими переменными"
    else
        log_success "Все обязательные переменные присутствуют"
    fi
}

# Проверка Docker-конфигурации
check_docker_config() {
    echo "🐳 Проверка Docker-конфигурации..."
    
    docker-compose config > /dev/null
    
    if [ $? -eq 0 ]; then
        log_success "Docker-композ валиден"
    else
        log_error "Ошибка в Docker-композ конфигурации"
        exit 1
    fi
}

# Проверка типизации Frontend
check_frontend_types() {
    echo "🖥️ Проверка типизации Frontend..."
    
    cd frontend
    npm run type-check
    
    if [ $? -eq 0 ]; then
        log_success "Типизация Frontend корректна"
    else
        log_error "Ошибки в типизации Frontend"
        exit 1
    fi
    cd ..
}

# Проверка миграций базы данных
check_database_migrations() {
    echo "💾 Проверка миграций базы данных..."
    
    cd backend
    alembic check
    
    if [ $? -eq 0 ]; then
        log_success "Миграции базы данных корректны"
    else
        log_error "Ошибки в миграциях базы данных"
        exit 1
    fi
    cd ..
}

# Проверка Docker-образов
check_docker_images() {
    echo "🖼️ Проверка Docker-образов..."
    
    docker-compose build --dry-run
    
    if [ $? -eq 0 ]; then
        log_success "Все Docker-образы могут быть собраны корректно"
    else
        log_error "Ошибки при сборке Docker-образов"
        exit 1
    fi
}

# Основная функция
main() {
    echo "🚀 Начало валидации инфраструктуры..."
    
    check_env_vars
    check_docker_config
    check_frontend_types
    check_database_migrations
    check_docker_images
    
    echo -e "\n${GREEN}🎉 Инфраструктура полностью валидна!${NC}"
}

main
