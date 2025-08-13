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

# Создаем необходимые директории
RUN mkdir -p /app/logs

# Экспонируем порт
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"] 