# Аудит готовности к 100%: 2026-04-28

**Связано:** [`PROD_LAUNCH_SECURITY_CHECKLIST.md`](./PROD_LAUNCH_SECURITY_CHECKLIST.md) · [`PROD_REMEDIATION_PLAN.md`](./PROD_REMEDIATION_PLAN.md) · [`TZ_TO_CODE_STATUS_MAP.md`](./TZ_TO_CODE_STATUS_MAP.md)

## TL;DR

| Область | Статус | Действие |
|---|---|---|
| Backend pytest (341/2skip) | ✅ | — |
| Frontend type-check | ✅ | — |
| Frontend lint (`--max-warnings 0`) | ⚠️ → ✅ | Исправлено в этом коммите |
| npm audit | ⚠️ 19 → ⚠️ 6 | Дальше — Next.js 14→16 (breaking) |
| Дубликаты конфигов | ⚠️ | Решить, какой держать |
| Production hardening | ⚠️ | Оставшиеся пункты ниже |

## Что было сломано на момент аудита

### 1. Frontend lint падал на CI gate (CRLF + Prettier)

`npx next lint --max-warnings 0` (job `frontend-build` в `.github/workflows/ci.yml`):

- `eslint-plugin-prettier` интерпретировал файлы как CRLF и рапортовал `Delete ␍`.
- В `demo.tsx`, `channels.tsx`, `admin/review.tsx`, `auth/forgot-password.tsx`, `auth/reset-password.tsx`, `lib/api.ts`, `components/channels/StatusBadge.tsx` были реальные prettier-несоответствия.
- В `pages/channels.tsx` и `pages/admin/review.tsx` были warnings `@typescript-eslint/no-unnecessary-condition` на защитном коде (`?? []`, `!= null`), валидном для runtime-данных.

**Исправлено:**
- `.eslintrc.js`: `'prettier/prettier': ['error', { endOfLine: 'auto' }]` — кросс-платформенно.
- То же — в `.eslintrc.json` (который Next.js всё ещё может подхватывать в подпроцессах).
- В `overrides` для `src/pages/**` отключён `@typescript-eslint/no-unnecessary-condition` — чтобы защитный код не падал в CI с `--max-warnings 0`.
- Прогон `prettier --write src/**/*.{ts,tsx,js,jsx}` нормализовал форматирование.
- Финальный прогон: `✔ No ESLint warnings or errors`, `tsc --noEmit` чистый.

### 2. npm audit: 19 уязвимостей

После `npm audit fix --legacy-peer-deps` осталось **6** (4 low + 1 moderate + 1 high). Остаток требует мажорного апдейта Next.js (14 → 16) — breaking change, отдельная задача (см. ниже).

## Оставшиеся гэпы и план фиксов

### A. Frontend (приоритет 2)

1. **Next.js 14 → 16.** Закрывает оставшиеся 6 уязвимостей (postcss XSS, Next.js DoS/SSRF). Требует прогон Playwright E2E + ручной QA. **Заводится отдельной веткой/PR.**
2. **Дубликаты ESLint config:** `.eslintrc.js` (root: true) выигрывает; `.eslintrc.json` остаётся «мёртвым», но содержит `next/core-web-vitals`. Решение: либо перенести `next/core-web-vitals` в `.eslintrc.js` (`extends`), либо удалить `.eslintrc.json`.
3. **Дубликаты Prettier config:** `.prettierrc` (JSON, `endOfLine: lf`) выигрывает; `.prettierrc.js` содержит `@trivago/prettier-plugin-sort-imports` — **не работает**, потому что не подхватывается. Решение: смерджить нужное в один файл или удалить.
4. **Next.js ESLint plugin не подключён** (`The Next.js plugin was not detected`). Добавить в `.eslintrc.js` `extends: ['next/core-web-vitals', ...]`.

### B. Backend — code smells (приоритет 3)

| Находка | Где | Что делать |
|---|---|---|
| `print()` в проде (~30 случаев) | `services/telethon_collector.py` (14), `trading_pair_validator.py` (10), `services/dedup.py`, `parsers/telegram_parser.py`, `tasks/collect_signals.py`, `services/collection_pipeline.py` | Заменить на `logger.info/warning/error`. Часть — legacy debug. |
| Bare `except Exception:` без логирования | `main.py` (4), `services/collection_pipeline.py` (2), `services/telegram_scraper.py` (2), `services/ocr_signal_parser.py` (4), `services/redis_cache.py` (4), `services/deep_collector.py` (2), `api/endpoints/dashboard.py` (4), и др. | Аудит каждого: добавить `logger.exception(...)` или конкретный класс исключения. |
| ML KPI 87.2% — не закрыт | `ml-service/`, `docs/ML_DATA_INTEGRITY_ROADMAP.md` | Выполнить план интеграции ML-данных. |
| Coverage 60% (CI gate) vs цель ТЗ 80% | `.github/workflows/ci.yml`, `backend/tests/` | Поднять покрытие в `services/` и `api/endpoints/`, повышать gate инкрементально. |

### C. Безопасность и конфигурация (приоритет 1, эксплуатация)

| Пункт | Статус | Что сделать |
|---|---|---|
| `.env` в working copy (не в git) с test Stripe keys | ⚠️ | `.gitignore` корректен (`.env`); риск — случайный `git add .env`. Защита: pre-commit detect-secrets уже подключен. |
| `.env` никогда не было в git history | ✅ | Подтверждено `git log -- .env`. |
| `OPENAPI_DOCS_ENABLED=false` в проде | ✅ | Уже в `docker-compose.production.yml` (этот спринт). |
| Postgres/Redis наружу через host ports | ⚠️ | `docker-compose.production.yml` всё ещё публикует `${POSTGRES_PORT:-5432}` и `${REDIS_PORT:-6379}`. В проде — только `127.0.0.1`-bind или вообще без `ports:`. См. [`SINGLE_NODE_SLA.md`](./SINGLE_NODE_SLA.md). |
| TLS на edge | ⚠️ | nginx/Traefik + Let's Encrypt — вне репо. |
| Ротация секретов из публичной истории | ⚠️ | См. [`SECURITY_PUBLIC_REPO.md`](./SECURITY_PUBLIC_REPO.md). |
| k6 prod-нагрузка | ⚠️ | Запуск + строки в `LOAD_TEST_RESULTS.md`. |

### D. Архитектура (приоритет 2)

См. [`DATA_PLANE_NEXT_SPRINT.md`](./DATA_PLANE_NEXT_SPRINT.md):
- **Association engine (фаза 7):** `signal_relations` есть, авто-кандидаты — нет.
- **Outcome engine (фаза 11):** v0.x, нужен стабильный пересчёт по свечам + тест различимости execution models (G4 приёмки).
- **A/B legacy vs canonical:** план `Planned`, dashboard не сделан.

## Что зафиксировано в коде этим аудитом

| Файл | Что |
|---|---|
| `frontend/.eslintrc.js`, `.eslintrc.json` | `endOfLine: 'auto'` для prettier; `no-unnecessary-condition: off` в overrides страниц |
| `frontend/src/**/*.{ts,tsx}` | `prettier --write` (7 файлов) |
| `frontend/package-lock.json` | `npm audit fix --legacy-peer-deps`: 19 → 6 уязвимостей |
| `docs/AUDIT_REPORT_2026_04_28.md` | этот файл |

## Регрессия

```powershell
cd backend; pytest tests/ --ignore=tests/test_z_production_integration.py -q --cov=app --cov-fail-under=60
cd frontend; npm run type-check; npx next lint --max-warnings 0; npm test -- --watchAll=false
python scripts/validate_docs_sync.py
```

Все четыре прошли локально на момент коммита.

## Закрыто после ревизии (2026-04-28, follow-up)

- **OPENAPI_DOCS_ENABLED регрессия** — добавлены тесты `backend/tests/test_openapi_docs_flag.py` (default `/docs` → 200, `false` → 404 для `/docs` и `/redoc`).
- **Postgres/Redis в проде не публикуются на 0.0.0.0** — в `docker-compose.production.yml` ports забинжены на `${POSTGRES_BIND_HOST:-127.0.0.1}` и `${REDIS_BIND_HOST:-127.0.0.1}`. Для полной приватной сети — снять блок `ports:`.
- **Frontend конфиги дедуплицированы** — удалены мёртвые `frontend/.eslintrc.json` и `frontend/.prettierrc.js` (последний ссылался на не-установленный `@trivago/prettier-plugin-sort-imports`); единый источник правды — `.eslintrc.js` + `.prettierrc`.
- **Next.js ESLint plugin** — на ветке `chore/nextjs-16-migration` починен:
    - `eslint-config-next` понижен `^16.1.6` → `^14.2.35` (mismatch с `next@14` и был причиной `Converting circular structure to JSON`).
    - `next/core-web-vitals` подключён в `.eslintrc.js`, дубль `eslintConfig` в `package.json` удалён.
    - Удалены мёртвые `eslint-disable-next-line` на правила `react-hooks/incompatible-library|set-state-in-effect` (они есть только в `eslint-plugin-react-hooks@v6` canary).
    - В `ResponsiveCard.tsx` точечный `jsx-a11y/no-static-element-interactions` disable (false positive).
    - Verification: `next lint --max-warnings 0` ✔, `tsc --noEmit` ✔, `next build` ✔.
    - Сама миграция `next@14 → next@16` — отдельным PR, чек-лист в `docs/MIGRATION_NEXT_16.md`.
- **`print()` в продовом коде** → `logger.warning` в `backend/app/parsers/telegram_parser.py` (импорт telethon). Остальные `print(...)` локализованы в CLI-обвязках (`--auth/--check/--collect`, `if __name__ == "__main__":`, `test_validator()`) — оставлены как ожидаемое поведение.
- **Bare `except: pass`** заменены на `logger.warning(..., exc_info=True)` / `logger.exception(...)` в `app/services/redis_cache.py` и `app/api/endpoints/dashboard.py` (cache fallback на DB больше не молчит).
- **G4 (различимость execution models)** — закрыт: `backend/tests/test_execution_models_g4_distinguishable.py`, 5 тестов:
    - три модели дают разные `entry_fill_price` на одном сценарии,
    - различающиеся MFE/MAE,
    - `market_on_publish` игнорирует limit `entry_price`,
    - `first_touch_limit` отдаёт `DATA_INCOMPLETE` если limit не касался свечей,
    - неизвестный `model_key` → `ERROR`/`unknown_model_key`.

## Дальше (top-3 для следующего спринта)

1. **Closeout `OPENAPI_DOCS_ENABLED=false`** реально применён на проде; проверить что `/docs` отдаёт 404.
2. **Next.js 14 → 16** в отдельном PR (закрывает все оставшиеся npm audit + новые перфоулучшения).
3. **Outcomes G4** — тест различимости execution models на эталонном сценарии (см. приёмка ТЗ).
