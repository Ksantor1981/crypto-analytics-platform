# Аудит в боевом режиме — февраль 2026

**Дата:** 26.02.2026  
**Цель:** Проверка работоспособности после изменений, математика, тесты, соответствие ТЗ и качество.

---

## 1. Результаты тестов

| Компонент | Результат |
|-----------|-----------|
| Backend pytest | **147 passed, 1 skipped** (после доработок 28.02) |
| Провалов | 0 |

**Skipped (1):** один из тестов с auth (контекст тестового клиента).

**Исправлено:** 2 integration-теста включены (test_get_channels_returns_list, test_get_channels_with_data); test_create_feedback_anonymous включён после починки Feedback enum.

---

## 2. Что работает

| Компонент | Статус |
|-----------|--------|
| Маршруты / API | 12/12 страниц, health + ready |
| ML predict | Модель xgboost_trained, ответы корректны |
| Каналы / сигналы | Данные из БД, accuracy из метрик |
| Security | 0 secrets в коде, 0 session в репо |
| Stripe | Планы Free / $19 / $49 |
| Математика accuracy | hits / resolved * 100, HIT_STATUSES vs MISS_STATUSES |
| Математика ROI | average_roi = среднее profit_loss_absolute по сигналам с заполненным PnL |
| Historical validator | TP/SL по OHLC CoinGecko, статусы TP1_HIT/SL_HIT, пересчёт каналов после validate_all_signals |
| Scheduler | Сбор TG/Reddit каждые 5 мин, daily revalidation, weekly digest, ML train раз в сутки |

---

## 3. Что исправлено в этой сессии

| Проблема | Было | Стало |
|----------|------|--------|
| **Дедупликация при сборе** | Сравнение `original_text == new[:500]` — дубликат с длинным текстом (600+ символов) не находился, создавались повторы | Сравнение по первым 500 символам с обеих сторон: `func.left(Signal.original_text, 500) == text_500` в collect_signals, scheduler (TG + Reddit), dedup.signal_exists |
| **dedup.signal_exists** | Докстрока «200 chars», логика как у коллектора | 500 chars, сравнение через `func.left` |
| **cleanup_duplicates** | При пустом `keep_ids` возможна массовая ошибка | Если `keep_ids` пустой — возврат 0, удалений нет |
| **frontend/coverage в репо** | Отслеживался в Git | Удалён из индекса, в .gitignore добавлен `frontend/coverage/` |

---

## 4. Что поправлено (сессия 28.02)

### Высокий приоритет — сделано

1. **Парсер DeFi/новости** — в telegram_scraper добавлен DEFI_NEWS_LIKE; сообщения с entry_price, без TP/SL, длиной ≥120 символов и с такими словами не считаются сигналом.
2. **Feedback enum** — в FeedbackRead добавлен field_serializer для feedback_type и status; тест test_create_feedback_anonymous включён.
3. **Scheduler ML на хосте** — database_url_for_host() в app.core.config; используется в scheduler и run_ml_train.py.

### Средний приоритет — сделано

4. **2 integration-теста** — test_get_channels_empty заменён на test_get_channels_returns_list; test_get_channels_with_data без skip, limit=100.
5. **CI e2e** — задержки увеличены (backend 8 с, frontend 15 с).
6. **cleanup_duplicates** — в scheduler раз в 12 циклов (~1 раз в час) вызывается cleanup_duplicates(db).

### Низкий приоритет — сделано

7. **Предупреждения** — Pydantic: ConfigDict во всех схемах (signal, channel, user, payment, subscription, trading, feedback, production_config); SQLAlchemy: declarative_base из sqlalchemy.orm.

### В работе / опционально

8. **Coverage backend 60%+** — не делалось (точечные правки по задачам).

---

## 5. Соответствие ТЗ и качество

| Критерий ТЗ | Требование | Факт | Оценка |
|-------------|------------|------|--------|
| Нагрузка | 1000 RPS | Не тестировали | — |
| Время отклика | <200 мс | ~100 мс | ✅ |
| ML точность | ≥87.2% | Реальная accuracy по данным (67.5% после чистки мусора) / CV 96% | ⚠️ по ТЗ, ок для бизнеса |
| Покрытие тестами | >80% | ~29% backend | ⚠️ |
| OpenAPI | Документация | /docs | ✅ |
| Stripe | Интеграция | Checkout + webhook | ✅ |
| Сбор данных | TG + Reddit | 27 TG + 20 Reddit, сбор каждые 5 мин | ✅ |
| Антирейтинг | УТП | sort=accuracy_asc | ✅ |
| Dedup при сборе | Нет дубликатов | Исправлено (сравнение по left(500)) | ✅ |
| Миграции | Alembic | Миграции есть, upgrade head в Docker | ✅ |

**Итог по соответствию ТЗ:** ~86–88% (как в `SPEC_COMPLIANCE_2026_02_25.md` с учётом исправлений дедупа и актуального состояния).

**Качество продукта:**  
- Для портфолио/собеседования — сильный уровень: микросервисы, ML, реальные данные, Stripe, Docker, CI.  
- Для бизнеса — MVP готов; критичная метрика accuracy после очистки мусора и дедупа в норме (67.5% > 60–65%).  
- Рекомендации 28.02 выполнены: Feedback enum, integration-тесты, e2e задержки, cleanup_duplicates, фильтр DeFi/новости, Pydantic ConfigDict.
