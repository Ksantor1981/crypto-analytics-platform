# Ревизия проекта Crypto Analytics Platform

## Общая оценка

Проект представляет собой **прототип/MVP** платформы анализа крипто-сигналов. Базовая архитектура (Frontend + Backend API + ML Service + Workers) корректна, но большая часть функционала — это заглушки, моки и хардкод. Проект **не готов к продакшену** в текущем состоянии.

---

## Критические проблемы (P0 — исправить первыми)

### 1. Frontend: Конфликт директорий `pages/` и `src/pages/`

**Суть**: Next.js видит ДВЕ директории со страницами и использует только root `pages/`. Из-за этого 14 маршрутов возвращают 404:
- `/signals`, `/channels`, `/profile`, `/subscription`, `/pricing`
- `/alerts`, `/ratings`, `/auth/forgot-password`, `/auth/reset-password`
- `/channels/[id]`, `/signals-optimized`, `/test-login`

**Решение**: Консолидировать все страницы в ОДНУ директорию. Рекомендуется перенести все из `src/pages/` в root `pages/`, поскольку root pages уже активны и используют рабочие компоненты.

**Задачи**:
- [ ] Перенести уникальные страницы из `src/pages/` в `pages/`
- [ ] Адаптировать импорты (заменить ссылки на `@/src/contexts/` и `@/src/components/`)
- [ ] Создать re-export файлы для контекстов (`contexts/AuthContext.tsx` → `src/contexts/AuthContext.tsx`)
- [ ] Удалить дубликаты из `src/pages/`
- [ ] Проверить, что все маршруты отдают 200

### 2. Безопасность: Хардкод секретов

**Суть**: В коде захардкожены реальные API ключи и пароли:

| Файл | Что захардкожено |
|------|-----------------|
| `workers/real_data_config.py` | Telegram API ID/Hash, Reddit Client ID/Secret, Bybit API keys |
| `backend/app/core/config.py` | SECRET_KEY, TRADING_ENCRYPTION_KEY, DATABASE_URL с паролем |
| `backend/app/core/production_config.py` | Пароль Postgres, пароль Redis |

**Решение**:
- [ ] Удалить все дефолтные значения секретов из кода
- [ ] Использовать ТОЛЬКО переменные окружения (без fallback значений для секретов)
- [ ] Добавить `.env.example` с placeholder-ами
- [ ] Добавить проверку на запуске — если секрет не задан, выбрасывать ошибку

### 3. Backend: Сломанные импорты

| Файл | Проблема |
|------|----------|
| `app/api/endpoints/feedback.py` | Использует `backend.app.*` вместо `app.*` |
| `app/api/endpoints/export.py` | `...database` вместо `...core.database` |
| `app/api/endpoints/stripe_webhooks.py` | `settings` вместо `get_settings()` |
| `app/core/auth.py` | `get_current_user_optional` не существует (есть `get_optional_current_user`) |

**Решение**:
- [ ] Исправить все импорты
- [ ] Добавить проверку импортов в CI/CD (или pre-commit hook)

---

## Высокий приоритет (P1)

### 4. Отключённая аутентификация на эндпоинтах

**Суть**: На нескольких эндпоинтах аутентификация закомментирована:
- `channels.py:72` — `# current_user = Depends(auth.get_current_active_user)`
- `user_sources.py:52` — закомментирован auth
- `user_sources.py:93` — `owner_id=1` хардкод

**Решение**:
- [ ] Раскомментировать аутентификацию на всех эндпоинтах
- [ ] Убрать хардкод `owner_id=1`

### 5. Незарегистрированные роутеры в `main.py`

8 эндпоинтов существуют, но не подключены:
- `feedback`, `export`, `analytics`, `api_keys`
- `ocr_integration`, `reddit_integration`, `stripe_webhooks`, `ml_prediction`

**Решение**:
- [ ] Добавить регистрацию всех роутеров в `main.py`
- [ ] Или удалить неиспользуемые эндпоинты

### 6. ML модели — нет обученных моделей

**Суть**: ML Service заявляет "87.2% accuracy", но:
- Нет ни одного файла модели (`.pkl`, `.joblib`, `.h5`)
- `EnsemblePredictor` — пустой: `self.rf_model = None`, `fit()` пустой
- `SimplePredictor` — rule-based, не ML
- Технические индикаторы (RSI, MACD) генерируются через `random.uniform()`
- Бэктестинг генерирует фейковые сделки через `random`

**Решение**:
- [ ] Собрать датасет исторических сигналов
- [ ] Обучить модель (хотя бы RandomForest/XGBoost)
- [ ] Сохранить модель в `.pkl`/`.joblib`
- [ ] Загружать и использовать модель в `predict()`
- [ ] Или честно указать "rule-based system" вместо "ML"

### 7. Дубликат маршрута GET `/api/v1/signals/`

В `signals.py` два обработчика на один путь `GET /` (строки 51 и 207). Второй перезаписывает первый.

**Решение**:
- [ ] Удалить дубликат
- [ ] Объединить логику в один обработчик

---

## Средний приоритет (P2) — Заглушки и моки

### 8. Frontend: Моковые данные вместо API

| Файл | Что замокано |
|------|-------------|
| `src/pages/dashboard.tsx` | `mockChannels`, `mockRecentSignals`, хардкод user |
| `src/pages/profile.tsx` | `mockUser` — полностью фейковый профиль |
| `src/pages/channels.tsx` | `fallbackChannels` — захардкоженные каналы |
| `src/pages/ratings.tsx` | `topChannels`, `worstChannels` — фейковый рейтинг |
| `src/pages/subscription.tsx` | Хардкод подписок и тарифных планов |
| `src/pages/signals-optimized.tsx` | `initialSignals` — хардкод в `getServerSideProps` |
| `src/hooks/useUserLimits.ts` | `mockUser` — фейковые лимиты |
| `src/components/notifications/AlertSystem.tsx` | `mockAlerts` + `Math.random()` |
| `pages/demo.tsx` | Полностью хардкод каналов и сигналов |

**Решение**:
- [ ] Заменить все моки на вызовы реального API
- [ ] Добавить loading states и error handling
- [ ] Оставить `demo.tsx` как демо-страницу (это нормально)

### 9. Backend: Моковые данные в эндпоинтах

| Файл | Что замокано |
|------|-------------|
| `channels.py` (194, 220) | Хардкод статистики каналов |
| `telegram_integration.py` (122-355) | Моковые Telegram каналы |
| `user_sources.py` (447-489) | Заглушки Discord, Reddit, Twitter анализаторов |
| `services/telegram_service.py` | Моковый поиск и сообщения |
| `services/data_quality_monitor.py` | 5 моковых методов |
| `main.py` (373-382) | Тестовый эндпоинт predictions/test |
| `models/signal_result.py` | Полная заглушка модели |

### 10. ML Service: Фейковые предсказания

| Файл | Что фейковое |
|------|-------------|
| `api/predictions_fixed.py` | RSI, MACD, Bollinger — `random.uniform()` |
| `api/risk_analysis.py` | Хардкод метрик риска |
| `api/risk_analysis_fixed.py` | `np.random.normal()` для returns |
| `api/backtesting_fixed.py` | Фейковые сделки через `random` |
| `models/backtesting.py` | Моковые исторические данные |

### 11. Workers: Моковые коллекторы

| Файл | Что фейковое |
|------|-------------|
| `telegram/telegram_client.py` | `collect_signals_mock()` — 3 хардкод сигнала |
| `simple_reddit_parser.py` | Хардкод демо-постов |
| `demo_latest_signals.py` | `random.random()` для success rate |
| `tasks.py:257` | Хардкод статистики |

---

## Низкий приоритет (P3) — Улучшения

### 12. Тесты

**Текущее состояние**: 10 тест-файлов на 106 Python файлов (~9% покрытие)

**Что нужно**:
- [ ] Unit тесты для моделей (User, Channel, Signal)
- [ ] API тесты для всех эндпоинтов
- [ ] Integration тесты для auth flow
- [ ] Тесты для ML предсказаний
- [ ] Frontend тесты (сейчас 4/4 failing)

### 13. Frontend конфигурация

- [ ] Исправить case-sensitivity импортов: `@/components/ui/input` vs `@/components/ui/Input`
- [ ] Выровнять path mapping: `tsconfig.json` (`@/*` → `./*`) vs `jest.config.js` (`@/*` → `src/*`)
- [ ] Релаксировать ESLint правила или исправить все ошибки (200+ ошибок)
- [ ] Починить `next build` (сейчас падает из-за ESLint errors)

### 14. Database модели

- [ ] Добавить поля `Channel.url`, `Channel.signals_count`, `Channel.accuracy` в SQLAlchemy модель
- [ ] Исправить `SignalResult` (сейчас заглушка)
- [ ] Настроить Alembic миграции

### 15. CORS и безопасность

- [ ] Убрать `BACKEND_CORS_ORIGINS = ["*"]` в продакшене
- [ ] Настроить rate limiting
- [ ] Добавить security headers middleware

---

## Рекомендуемый порядок работ

### Фаза 1: Стабилизация (1-2 недели)
1. Консолидировать `pages/` и `src/pages/` — решает 14 маршрутов 404
2. Убрать хардкод секретов
3. Исправить сломанные импорты
4. Подключить незарегистрированные роутеры
5. Починить `next build`

### Фаза 2: Реальные данные (2-4 недели)
1. Заменить моки на API вызовы во фронтенде
2. Реализовать реальные Telegram/Reddit коллекторы
3. Обучить хотя бы простую ML модель
4. Заменить `random.uniform()` на реальные технические индикаторы
5. Раскомментировать аутентификацию

### Фаза 3: Качество (2-3 недели)
1. Написать тесты (цель: 60%+ покрытие)
2. Настроить CI/CD
3. Добавить мониторинг и логирование
4. Провести security audit
5. Документация API

---

## Статистика ревизии

| Метрика | Значение |
|---------|----------|
| Файлов с заглушками | 30+ |
| 404 маршрутов | 14 |
| Сломанных импортов | 5 |
| Незарегистрированных роутеров | 8 |
| Файлов с `random.*` в ML/Workers | 15+ |
| Хардкод API ключей | 6+ |
| Тестовое покрытие | ~9% |
| Обученных ML моделей | 0 |

---

*Дата ревизии: 25 февраля 2026*
*Версия: 1.0.0*
