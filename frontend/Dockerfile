FROM node:16-alpine

WORKDIR /app

# Установка зависимостей
COPY package*.json ./
RUN npm ci --only=production

# Копирование кода приложения
COPY . .

# Сборка приложения
RUN npm run build

# Экспонируем порт
EXPOSE 3000

# Запуск приложения
CMD ["npm", "start"] 