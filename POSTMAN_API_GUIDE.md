# Crypto Analytics Platform - API Testing Guide

## 📋 Обзор

Этот проект содержит полную коллекцию Postman для тестирования всех API эндпоинтов Crypto Analytics Platform.

## 📁 Файлы коллекций

1. **`Crypto_Analytics_Platform_API.postman_collection.json`** - Основные эндпоинты:
   - Health & System checks
   - Authentication (Register, Login, Refresh Token)
   - Users (Profile, Settings, Admin functions)

2. **`Crypto_Analytics_Platform_API_Extended.postman_collection.json`** - Расширенные эндпоинты:
   - Channels (Get, Statistics, Signals)
   - Signals (Analytics, Stats, Telegram integration)
   - Subscriptions (Plans, Management, Premium features)
   - ML Integration (Predictions, Model info)
   - Telegram Integration

3. **`Crypto_Analytics_Platform_Payments.postman_collection.json`** - Платежи:
   - Payments (Create, Confirm, History, Refunds)
   - Stripe Webhooks
   - Admin payment functions

## 🚀 Быстрый старт

### 1. Импорт коллекций в Postman

1. Откройте Postman
2. Нажмите **Import** в левом верхнем углу
3. Выберите **File** и загрузите все 3 JSON файла
4. Коллекции появятся в вашем workspace

### 2. Настройка переменных окружения

Создайте новое окружение в Postman с переменными:

```
baseUrl: http://localhost:8000
accessToken: (будет заполнен автоматически после логина)
```

### 3. Аутентификация

1. **Регистрация пользователя**: `Authentication > Register User`
2. **Вход в систему**: `Authentication > Login User` 
   - После успешного входа `accessToken` автоматически сохранится
3. **Обновление токена**: `Authentication > Refresh Token`

## 📊 Структура API

### Health & System
- `GET /` - Корневой эндпоинт
- `GET /health` - Проверка состояния API
- `GET /api/v1/health` - Проверка ML сервиса

### Authentication & Users
- `POST /api/v1/users/register` - Регистрация
- `POST /api/v1/users/login` - Вход
- `POST /api/v1/users/refresh` - Обновление токена
- `GET /api/v1/users/me` - Профиль пользователя
- `PUT /api/v1/users/me` - Обновление профиля
- `POST /api/v1/users/me/password` - Смена пароля

### Channels
- `GET /api/v1/channels` - Список каналов
- `GET /api/v1/channels/{id}` - Канал по ID
- `GET /api/v1/channels/{id}/signals` - Сигналы канала
- `GET /api/v1/channels/{id}/statistics` - Статистика канала

### Signals
- `GET /api/v1/signals` - Список сигналов
- `GET /api/v1/signals/{id}` - Сигнал по ID
- `GET /api/v1/signals/stats/overview` - Общая статистика
- `GET /api/v1/signals/analytics/top-performing` - Топ сигналы
- `GET /api/v1/signals/telegram` - Telegram сигналы
- `POST /api/v1/signals/telegram/batch` - Создание сигналов

### Subscriptions
- `GET /api/v1/subscriptions/plans` - Тарифные планы
- `GET /api/v1/subscriptions/me` - Моя подписка
- `POST /api/v1/subscriptions` - Создание подписки
- `PUT /api/v1/subscriptions/me` - Обновление подписки
- `GET /api/v1/subscriptions/premium/features` - Premium функции

### Payments (Stripe)
- `POST /api/v1/payments/create-payment-intent` - Создание платежа
- `POST /api/v1/payments/confirm-payment` - Подтверждение платежа
- `GET /api/v1/payments/history` - История платежей
- `POST /api/v1/payments/{id}/refund` - Возврат средств
- `POST /api/v1/payments/stripe/webhook` - Stripe webhook

### ML Integration
- `GET /api/v1/model/info` - Информация о модели
- `POST /api/v1/predict/signal` - Предсказание для сигнала
- `POST /api/v1/predict/batch` - Пакетное предсказание
- `POST /api/v1/predict` - Прямое предсказание

### Telegram Integration
- `POST /channels/{id}/toggle` - Переключение статуса канала

## 🔐 Авторизация

Большинство эндпоинтов требуют авторизации через Bearer Token:

```
Authorization: Bearer {{accessToken}}
```

Токен автоматически добавляется после успешного входа в систему.

## 📝 Примеры использования

### 1. Полный цикл тестирования

1. **Health Check**: Проверьте, что API работает
2. **Register**: Создайте нового пользователя
3. **Login**: Войдите в систему (токен сохранится автоматически)
4. **Get Channels**: Получите список каналов
5. **Get Signals**: Получите сигналы
6. **Get Subscription Plans**: Посмотрите тарифы
7. **Create Payment Intent**: Создайте платеж

### 2. Тестирование ML функций

1. **ML Model Info**: Получите информацию о модели
2. **Direct ML Predict**: Сделайте прямое предсказание
3. **Predict Signal**: Предскажите результат для существующего сигнала

### 3. Админ функции

1. **Get All Users**: Список всех пользователей (требует admin права)
2. **Get Payment Stats**: Статистика платежей
3. **Subscription Stats**: Статистика подписок

## ⚠️ Важные замечания

1. **Переменные окружения**: Убедитесь, что `baseUrl` указывает на правильный адрес API
2. **Токены**: После логина токен сохраняется автоматически
3. **Admin эндпоинты**: Требуют специальных прав доступа
4. **Rate Limiting**: API может ограничивать количество запросов
5. **Webhook тестирование**: Stripe webhooks требуют правильной подписи

## 🛠️ Разработка

При добавлении новых эндпоинтов:

1. Добавьте запрос в соответствующую коллекцию
2. Настройте правильные headers и body
3. Добавьте тесты для автоматической проверки ответов
4. Обновите эту документацию

## 📞 Поддержка

При возникновении проблем с API:

1. Проверьте статус сервисов через Health Check эндпоинты
2. Убедитесь в правильности токена авторизации
3. Проверьте логи backend сервиса
4. Обратитесь к документации API в Swagger UI: `http://localhost:8000/docs`

---

**Версия**: 1.0.0  
**Последнее обновление**: $(date)  
**Общее количество эндпоинтов**: 50+
