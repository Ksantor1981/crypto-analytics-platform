# Чеклист: окружение готово к работе

**Назначение:** быстро проверить, что разработчик или оператор может **собрать стек, применить миграции и убедиться в работоспособности** без сюрпризов.  
**Не заменяет** полную приёмку по ТЗ — для неё используйте [`TZ_APPENDIX_DATA_PLANE_ACCEPTANCE.md`](./TZ_APPENDIX_DATA_PLANE_ACCEPTANCE.md).

---

## 1. Инфраструктура

| Шаг | Действие | Ожидание |
|-----|----------|----------|
| 1.1 | Поднять Postgres + Redis | `docker compose -f docker-compose.simple.yml up -d` (или полный `docker compose up -d`) |
| 1.2 | Переменные окружения | Скопировать из `.env.example` в корень и в `backend/` при необходимости; задать `SECRET_KEY` (≥32 символа), `DATABASE_URL` / креды как в compose |
| 1.3 | Миграции | `cd backend && alembic upgrade head` (или `make db-migrate` из корня при запущенном `backend` в compose) |

---

## 2. Backend

| Шаг | Действие | Ожидание |
|-----|----------|----------|
| 2.1 | Зависимости | `pip install -r backend/requirements.txt` (+ `bcrypt==4.0.1` при необходимости) |
| 2.2 | Тесты (как в CI) | `USE_SQLITE=true` … `pytest tests/ --ignore=tests/test_z_production_integration.py --cov=app --cov-fail-under=60` |
| 2.3 | Smoke API | С запущенным API: `python backend/scripts/smoke_real_services.py --base-url http://127.0.0.1:8000` → все пробы OK |

---

## 3. Frontend

| Шаг | Действие | Ожидание |
|-----|----------|----------|
| 3.1 | Зависимости | `cd frontend && npm install --legacy-peer-deps` |
| 3.2 | Качество | `npm run type-check && npm test && npx next build` |

---

## 4. ML-сервис (опционально)

| Шаг | Действие | Ожидание |
|-----|----------|----------|
| 4.1 | Зависимости | `pip install -r ml-service/requirements.txt` |
| 4.2 | Проверка | `python -c "from models.trained_predictor import predict_signal_success"` (как в CI) |

---

## 5. Регрессия одной командой (после правок)

См. [`PLAN_99_READINESS.md`](./PLAN_99_READINESS.md) — блок «Регрессия после изменений».

---

## 6. Соответствие ТЗ и data plane

- Карта требований: [`TZ_TO_CODE_STATUS_MAP.md`](./TZ_TO_CODE_STATUS_MAP.md)  
- Закрытие канонического контура: [`DATA_PLANE_MIGRATION.md`](./DATA_PLANE_MIGRATION.md) + чек-лист приёмки выше.

Когда приёмка закрыта — временный `TZ_APPENDIX_*` удаляют по политике из самого файла приёмки.
