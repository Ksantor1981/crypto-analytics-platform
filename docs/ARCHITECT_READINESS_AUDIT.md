# Аудит готовности — Архитектор системы
**Дата:** 26 февраля 2026  
**Роль:** System Architect (paranoid mode, failure modes, production-readiness)

---

## Executive Summary

Платформа — **MVP с хорошим фундаментом**, готовый для локальной разработки и демо.  
Production-deploy требует доработок. Соответствие ТЗ: **~55%** (см. `СООТВЕТСТВИЕ_ТЗ_2026_02_25.md`).

---

## 1. Архитектура — ✅ Соответствует ТЗ

| Компонент | Статус | Комментарий |
|-----------|--------|-------------|
| Frontend (Next.js 14, TS) | ✅ | Структура, маршруты, React Query |
| Backend (FastAPI) | ✅ | REST API, Swagger, 133 эндпоинта |
| ML Service | ✅ | Изолированный сервис на порту 8001 |
| Workers (Celery) | ⚠️ | Код есть, сбор — fallback на моки без env |
| PostgreSQL + Redis | ✅ | Docker Compose |
| Docker / docker-compose | ✅ | simple, deploy, production варианты |

**Структура репозитория:**
```
backend/      frontend/     ml-service/   workers/
helm/         monitoring/   infrastructure/  nginx/
```

---

## 2. Failure Modes и риски

| Риск | Severity | Митигация |
|------|----------|-----------|
| Нет реального сбора Telegram | HIGH | Подключить Telethon + env keys; Celery beat |
| ML модель | MEDIUM | train_from_db.py есть; CV 96%; OOS не подтверждён |
| Stripe не подключен | MEDIUM | Тест-ключи Stripe в .env |
| CI/CD отсутствует | MEDIUM | GitHub Actions: lint, test, build |
| Секреты в env.example | FIXED | Placeholders только; real_keys убран из истории |

---

## 3. Production Readiness

| Критерий ТЗ | Текущее состояние | Готовность |
|-------------|-------------------|------------|
| 1000 RPS | Не тестировалось | ❌ |
| API <200ms | Частично | ⚠️ |
| 99.9% uptime | Нет оркестрации | ❌ |
| ML ≥87.2% | Rule-based, CV 96% на тестах | ⚠️ |
| Тесты >80% | 85 тестов, pytest-cov в CI (30% min) | ⚠️ |
| 0 hardcoded secrets | ✅ | ✅ |

---

## 4. Production features (реализовано)

- **Prometheus** — `GET /metrics`, prometheus-client
- **Structured logging** — structlog в main.py (JSON при LOG_JSON=true)
- **Graceful shutdown** — lifespan: cancel tasks, stop scheduler, engine.dispose()
- **Pinned deps** — скрипты `scripts/generate_requirements_pinned.sh|.ps1`

## 5. Рекомендации (приоритет)

1. **Реальный сбор** — TELEGRAM_API_ID/HASH в .env, список каналов в `workers/real_data_config.py`
2. **ML pipeline** — train_from_db.py готов; добавить feature_importance, backtest
3. **CI/CD** — `.github/workflows/ci.yml`: pytest, build frontend
4. **Секреты** — Ротировать все ключи из старой папки (уже скомпрометированы)

---

## 6. Вердикт

**Для резюме/портфолио:** Подходит с честной формулировкой:  
*«Full-stack pet-project: FastAPI + Next.js + ML service. MVP реализован, доработка до production в процессе.»*

**Для production:** Требуется реализовать п.1–3 из рекомендаций.
