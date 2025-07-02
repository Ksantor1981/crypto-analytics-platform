FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Запуск Celery worker
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"] 