FROM python:3.9-slim

WORKDIR /app

# Копируем только requirements.txt сначала для кэширования
COPY requirements.txt .

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

# Команда запуска Celery worker
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"] 