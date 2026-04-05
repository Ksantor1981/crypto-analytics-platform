# План доведения продукта до ~99% готовности

**Роль:** PO + разработка + архитектура + QA + UX.  
**Исключено из плана:** уже закрытые вами темы (демо-маскировка, выравнивание тарифов главная/subscription, кнопки лендинга и т.п.).

---

## Целевое состояние «99%»

| Критерий | Что значит |
|----------|------------|
| **Сборка** | `next build` без ошибок компиляции |
| **Backend** | `pytest` зелёный, критичные API покрыты тестами |
| **UX** | Гость может зарегистрироваться; платные планы ведут в login/checkout; нет «мёртвых» кнопок на ключевых страницах |
| **Консистентность** | Один API-клиент (`lib/api.ts`), единые цены с Stripe |
| **Документация** | Чек-лист запуска, план доработок, актуальный статус ТЗ |

То, что **вне контроля кода** (VPS, 99.9% uptime, 1000 RPS без прогона k6 на стенде), в 99% не входит — только подготовка артефактов.

---

## Фазы работ

### Фаза A — Стабильность и тесты (сделано в этой сессии)

- [x] Тесты `GET /api/v1/users/me/limits` (403 без токена, 200 + поля после регистрации/логина)
- [x] Исправление регистра имени файла `input.tsx` vs `Input.tsx` (Windows + `forceConsistentCasingInFileNames`)
- [x] `tsconfig`: исключить `tests/e2e` и `.next` из общей проверки типов
- [x] `jest`: `modulePathIgnorePatterns` для `.next` (коллизия с standalone)
- [x] `frontend/.gitignore`: `.next`, `standalone`
- [x] Подписки: гость не считается на тарифе Free; кнопка «Начать бесплатно» → `/auth/register`

### Фаза B — TypeScript strict (технический долг)

**Статус (2026-02-26):** `npx tsc --noEmit` в `frontend/` — **0 ошибок**.

**Сделано:**

1. **Резолв `@/types`:** в `tsconfig.json` путь `@/*` → сначала `./src/*`, затем `./*` (раньше подтягивался урезанный `frontend/types/` вместо `src/types/`).
2. **`frontend/types/index.ts`** — реэкспорт из `../src/types` (без дублирования моделей).
3. **UI casing:** `Button.tsx`/`Card.tsx` → `button.tsx`/`card.tsx` под импорты из `index.ts`.
4. **Типы:** `APIUser` расширен полями ответа `/users/me`; у `Signal` частично опциональны поля API; `ChannelSignal.exit_price`; типы рейтинга `RatingChannelTop` / `RatingChannelAnti` в `ratings.tsx`.
5. **Компоненты:** фолбэки `asset`/`pair`/`entry_price`; `ChannelsFilter` без `any`; `getChannels(params?)` в `lib/api.ts`.
6. **Тесты:** `test_smoke.py` — корректная обработка awaitable `ping`; Jest — non-null для `querySelector`.
7. **CI frontend:** перед `next build` выполняются `npm run type-check` и `npm test` (`.github/workflows/ci.yml`).

**Дальше (по желанию):** постепенное ужесточение `strict` в `tsconfig`.

### Фаза C — Продукт и UX

- [x] Пустое состояние `/signals` — подсказка + CTA «Войти» / «Каналы» / «Панель»
- [x] Пустое состояние `/ratings` (топ) — подсказка + ссылки на каналы/сигналы
- [x] **AlertSystem / `/alerts`:** явный баннер: данные из API сигналов; push-центр по ТЗ (Pro) — не реализован, ожидания зафиксированы в UI
- [x] **Stripe:** документ smoke-теста test checkout — [`docs/STRIPE_TEST_CHECKOUT.md`](./STRIPE_TEST_CHECKOUT.md)
- [x] **E2E:** job `e2e` в [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (Playwright в `e2e/`, `continue-on-error: false` — gate для main)

**Разрывы с формальным ТЗ (ML 87.2%, 80% coverage, 1000 RPS, 99.9%):** пошагово — [`TZ_GAPS_REMEDIATION.md`](./TZ_GAPS_REMEDIATION.md).

### Фаза D — Production

- Развёртывание по `SPEC.md` / Docker / Helm
- Секреты только в env
- Мониторинг (Prometheus/Grafana) на стенде

---

## Регрессия после изменений

```powershell
cd backend && python -m pytest -q
cd frontend && npm run type-check && npm test && npm run build
```

---

## Метрика готовности (субъективно)

| Область | До плана | После фазы A | После B + C |
|---------|----------|----------------|-------------|
| API + тесты критичных путей | ~92% | ~93% | ~93% (CI cov ≥60%) |
| Frontend сборка + типы + unit | OK | OK | **type-check + jest в CI** |
| UX подписки (гость) | Сломан Free | OK | OK |
| Прозрачность `/alerts` + Stripe smoke-док | — | — | **OK** |
| **Итого оценка «готовность» (код)** | ~86–88% | **~90–92%** | **~94–96%** |

По коду **фазы A–C закрыты** в пределах репозитория. До **~99% «в бою»** остаётся **фаза D** (VPS, SSL, секреты, приёмка нагрузки k6 при необходимости) — без сервера не автоматизируется.

---

*Документ обновляется по мере закрытия фаз.*
