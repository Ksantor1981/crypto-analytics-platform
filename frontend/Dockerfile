FROM node:18-alpine

WORKDIR /app

# Установка зависимостей
COPY package*.json ./
RUN npm ci --only=production --legacy-peer-deps --ignore-scripts

# Копирование кода приложения
COPY . .

# Сборка приложения
RUN npm run build

# Экспонируем порт
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Запуск приложения
CMD ["npm", "start"] 