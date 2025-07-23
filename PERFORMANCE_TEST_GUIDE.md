# Performance Testing Guide (k6)

## 1. Установка k6
- [Официальная инструкция](https://k6.io/docs/getting-started/installation/)
- Пример для Windows:
  ```bash
  choco install k6
  ```
- Пример для Linux/macOS:
  ```bash
  brew install k6
  # или
  sudo apt install k6
  ```

## 2. Запуск теста
- В корне проекта:
  ```bash
  k6 run performance_test_k6.js
  ```
- По умолчанию тестируется:
  - POST /api/v1/users/login
  - GET /api/v1/channels/
  - 20 виртуальных пользователей, 30 секунд

## 3. Интерпретация результатов
- В консоли появятся метрики: RPS, latency, ошибки, процент успешных запросов.
- Если есть ошибки (status != 200) — проверьте backend и тестовые данные.

## 4. Как адаптировать
- Измените VUs/duration в options для других нагрузок.
- Добавьте другие endpoints по аналогии.

## 5. Рекомендации
- Запускайте тесты на staging/dev окружении, чтобы не перегружать production.
- Используйте результаты для оптимизации производительности backend. 