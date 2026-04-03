# ТЗ → код: карта соответствия и статусов

**Назначение:** единая привязка пунктов `SPEC.md` к файлам/модулям репозитория и честный статус (без смешения «код есть» и «критерий ТЗ доказан»).

**Связанные документы:** [SPEC.md](../SPEC.md), [SPEC_COMPLIANCE_2026_02_25.md](../SPEC_COMPLIANCE_2026_02_25.md), [TZ_GAPS_REMEDIATION.md](./TZ_GAPS_REMEDIATION.md), [ADR_PRICE_DATA_SOURCES.md](./ADR_PRICE_DATA_SOURCES.md), [SIGNAL_LIFECYCLE_ROADMAP.md](./SIGNAL_LIFECYCLE_ROADMAP.md).

**Дата карты:** 2026-04-03.

**CI (факт репозитория):** в `.github/workflows/ci.yml` для backend указано `--cov-fail-under=30` (не путать с целевым 80% из ТЗ).

---

## Критерии успеха ТЗ (`SPEC.md` — раздел «Критерии успеха»)

| Требование ТЗ | Где в репозитории | Статус | Комментарий |
|---------------|-------------------|--------|-------------|
| **1000 RPS** | `scripts/load-test/k6-load.js`, `k6-stress.js`, `scripts/load-test/README.md` | ❌ не доказано | Скрипты есть; критерий ТЗ закрывается отчётом прогона на стенде. |
| **p95 &lt; 200 ms** | k6 + API под нагрузкой | ⚠️ частично | В compliance фигурирует оценка без нагрузки; под целевой RPS не подтверждено. |
| **99.9% uptime** | `docker-compose*`, `helm/`, `monitoring/`, `docs/DISASTER_RECOVERY.md` | ❌ не доказано | Нужны прод/стейджинг и SLO; репо содержит заготовки. |
| **ML ≥ 87.2%** (out-of-sample, без синтетики) | `ml-service/train_from_db.py`, `ml-service/models/`, `docs/ML_ACCURACY_DISCREPANCY.md`, `docs/ML_DATA_INTEGRITY_ROADMAP.md` | ⚠️ цель не достигнута | Фактические метрики и разрыв с CV — в compliance и ML-доках; закрытие через данные и методику. |
| **Покрытие тестами &gt; 80%** | `backend/tests/`, `.github/workflows/ci.yml` | ⚠️ далеко от ТЗ | Порог CI: **30%**; отчёт coverage ~29% в compliance — наращивать по `TZ_GAPS_REMEDIATION.md`. |
| **OpenAPI** | FastAPI `/docs`, `backend/app/main.py` и роутеры | ✅ | Swagger доступен. |
| **Stripe** | `backend/app/api/endpoints/payments.py`, webhooks, frontend checkout | ✅ | Боевой режим зависит от секретов и окружения. |

---

## Этап 2: Ядро системы (`SPEC.md` §2)

| Подпункт ТЗ | Где в репо | Статус |
|-------------|------------|--------|
| **2.1 БД PostgreSQL + Alembic** | `backend/app/models/`, `backend/alembic/versions/` | ✅ / ⚠️ | Схема и миграции в репо; «зелёность» на чистой БД — проверять `alembic upgrade head`. |
| **2.2 Backend API** | `backend/app/api/endpoints/`, `backend/app/services/` | ✅ функционально | NFR (coverage, нагрузка) — отдельно. |
| **2.3 ML-сервис** | `ml-service/` | ⚠️ | Сервис и обучение есть; KPI 87.2% и A/B — не закрыты. |
| **2.4 Workers** | `workers/`, `backend/app/tasks/`, профили в `docker-compose*.yml` | ⚠️ | Код и compose есть; зрелость в проде — эксплуатация. |

---

## Этап 3: Frontend (`SPEC.md` §3)

| Подпункт | Где | Статус |
|----------|-----|--------|
| **3.1–3.2 UI, страницы, Stripe** | `frontend/src/` | ✅ MVP+ |
| **3.3 Lighthouse &gt; 90, offline** | `frontend/` | ⚠️ / ❓ | Закрывается замерами, не зафиксировано в compliance как выполненное. |

---

## Этап 4: Интеграция и тестирование (`SPEC.md` §4)

| Подпункт | Где | Статус |
|----------|-----|--------|
| **4.1 Интеграционные + E2E** | `backend/tests/`, `e2e/`, `.github/workflows/ci.yml` | ⚠️ | Job `e2e` с `continue-on-error: true` — не блокирует merge. |
| **4.2 Нагрузочное** | `scripts/load-test/` | ⚠️ | Нужен зафиксированный отчёт под критерии ТЗ. |
| **4.3 Безопасность** | `docs/SECURITY_PUBLIC_REPO.md`, `.pre-commit-config.yaml`, job `security` в CI | ⚠️ | Сканирование зависимостей и паттерны; полный pen-test как в ТЗ — отдельный этап. |

---

## Этап 5: Развёртывание (`SPEC.md` §5)

| Подпункт | Где | Статус |
|----------|-----|--------|
| **5.1–5.3 Prod, мониторинг, бэкапы** | `helm/`, `docker-compose.production.yml`, `monitoring/` | ⚠️ | Артефакты есть; работающий прод и SLO — вне репозитория. |

---

## Интеграции и фичи (SPEC + `TZ_GAPS_REMEDIATION`)

| Требование | Где в репо | Статус |
|------------|------------|--------|
| **Binance / Bybit** (формулировка ТЗ) | Факт: `backend/app/services/price_validator.py` (**CoinGecko**) | ⚠️ | Либо клиенты бирж, либо правка ТЗ (см. `TZ_GAPS_REMEDIATION` §5). |
| **Telegram + Reddit** | `collection_pipeline`, `reddit_scraper`, `workers/telegram/` | ✅ код | Риски ToS/лимитов — эксплуатация. |
| **Кастомные алерты Pro** | `models/custom_alert.py`, `services/custom_alerts_service.py`, `api/endpoints/custom_alerts.py`, хук в `collection_pipeline.py` | ✅ API + миграция; на PostgreSQL выполнить `alembic upgrade head` |
| **Google Analytics** | `frontend/src/components/analytics/GoogleAnalytics.tsx` | ✅ по env | `NEXT_PUBLIC_GA_MEASUREMENT_ID`. |

---

## Бизнес-KPI ТЗ

Не закрываются кодом (маркетинг, продукт, аналитика) — см. `TZ_GAPS_REMEDIATION` §8.

---

*Обновляйте таблицу при закрытии пунктов: дата + кратко что изменилось.*
