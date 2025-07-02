FROM node:16-alpine

WORKDIR /app

# Установка зависимостей
COPY package.json package-lock.json* ./
RUN npm ci

# Копирование кода приложения
COPY . .

# Сборка приложения
RUN npm run build

# Запуск приложения
CMD ["npm", "run", "start"] 