# План доведения соответствия ТЗ до 85–90%

**Архитектор.** Цель: стабильный CI + соответствие ТЗ ≥85%. Приоритет: сначала зелёный pipeline, затем функциональные задачи.

---

## Фаза 0: Исправление CI (блокер)

| # | Задача | Статус | Ответственный |
|---|--------|--------|---------------|
| 0.1 | Frontend: создать lib/utils, lib/i18n, lib/performance, lib/api | ✅ | Разработчик |
| 0.2 | Backend: проверить/исправить тесты в CI | ⏸ | CI ставит requirements.txt — должно проходить |
| 0.3 | Прогон CI (ci.yml + ci-cd.yml) | ⏳ | QA |

---

## Фаза 1: Критичные для ТЗ (→75%→85%)

| # | Задача из СООТВЕТСТВИЕ_ТЗ | Влияние | Метрика |
|---|---------------------------|---------|---------|
| 1.1 | Антирейтинг из API (не хардкод) | Аналитика +15% | ✅ GET /channels?sort=accuracy_asc, ratings использует apiChannels |
| 1.2 | Авторасчёт accuracy/ROI каналов | Аналитика +15% | ✅ metrics_calculator, POST /collect/recalculate-metrics |
| 1.3 | Stripe checkout flow (тест-ключи) | Backend +15% | /stripe/create-checkout, webhook |
| 1.4 | Тесты: 50+ backend тестов, coverage 40%+ | Backend +10% | pytest, pytest-cov |

---

## Фаза 2: Высокий приоритет (→90%)

| # | Задача | Влияние |
|---|--------|---------|
| 2.1 | Responsive: dashboard, channels, ratings | Frontend +10% |
| 2.2 | Excel export для Premium | Backend +5% |
| 2.3 | CI/CD: убедиться workflow полный | Инфраструктура +10% |

---

## Критерии приёмки (QA)

- [ ] `ci.yml`: backend-tests, frontend-build, ml-service, security — PASS
- [ ] `ci-cd.yml`: test job — PASS (если выполняется)
- [ ] Соответствие ТЗ по блокам: ≥85% по расчёту

---

*Создано: архитектор. Обновляется по мере выполнения.*
