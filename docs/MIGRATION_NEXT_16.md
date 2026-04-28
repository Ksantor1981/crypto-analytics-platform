# Миграция Next.js 14 → 16

**Цель**: закрыть оставшиеся `npm audit` уязвимости (next@14 + postcss<8.5.10) и привести фронт в актуальную версию.

**Статус**: подготовительный PR — выровнен ESLint/Next plugin, но сама миграция Next 16 НЕ выполняется в этом PR (требует визуальной приёмки UX).

---

## Что уже сделано на ветке `chore/nextjs-16-migration`

1. `eslint-config-next` понижен `^16.1.6` → `^14.2.35` (совместим с `next@^14`).
   Это убрало ошибку `Converting circular structure to JSON` от ESLint, которую вызывал mismatch eslint-config-next@16 ↔ next@14.
2. `next/core-web-vitals` подключён в `frontend/.eslintrc.js`. Lint снова работает с Next plugin (`✔ No ESLint warnings or errors`, `next lint` больше не ругается на отсутствие плагина).
3. Из `package.json` удалён дубль `"eslintConfig": { "extends": ["next/core-web-vitals"] }` — единый источник правды теперь `.eslintrc.js`.
4. Удалены мёртвые `eslint-disable-next-line` комментарии, ссылавшиеся на правила из `eslint-plugin-react-hooks@v6` (canary), которых нет в установленной v5:
   - `src/components/channels/AddChannelModal.tsx:156` (`react-hooks/incompatible-library`)
   - `src/components/ui/Table.tsx:16` (`react-hooks/incompatible-library`)
   - `src/contexts/LanguageContext.tsx:31` (`react-hooks/set-state-in-effect`)
5. В `src/components/ui/ResponsiveCard.tsx:136` поставлен корректный `eslint-disable-next-line jsx-a11y/no-static-element-interactions` (false positive: role/tabIndex/onKeyDown заданы условно при наличии onClick).
6. Из `.eslintrc.js` убраны мёртвые декларации `react-hooks/incompatible-library: 'off'`, `react-hooks/set-state-in-effect: 'off'`, `react-hooks/refs/purity/immutability: 'off'` — они апеллировали к canary-правилам v6.
7. Verification: `next lint --max-warnings 0` ✔, `tsc --noEmit` ✔, `next build` ✔.

`npm audit --omit=dev` после этого: **2** vulnerability (1 moderate + 1 high) — все в `next@14` и его транзитивном `postcss`. Закроются Next 16.

---

## Что осталось сделать в реальном Next 16 PR

### 1. Bump зависимостей

```jsonc
// package.json
"next": "^16.2.4",
"react": "^19.0.0",       // обязательно — Next 15+ требует React 19
"react-dom": "^19.0.0",
"eslint-config-next": "^16.2.4",
// devDependencies:
"@types/react": "19.x",   // уже стоит 19.1.10
"@types/react-dom": "19.x"
```

```bash
npm install --legacy-peer-deps
npx @next/codemod@latest upgrade latest   # официальный codemod от Vercel
```

### 2. Breaking changes Next 15+ к проверке

| # | Что | Где смотреть |
|---|-----|---|
| B1 | Async `params` / `searchParams` в RSC и pages | все `pages/[id].tsx`, `app/.../page.tsx` |
| B2 | Async `cookies()`, `headers()`, `draftMode()` | RSC/middleware/handlers |
| B3 | `fetch` теперь по умолчанию **не кешируется** | API-вызовы в RSC |
| B4 | Server actions: middleware больше не выполняется | проверить `middleware.ts` |
| B5 | `next/image`: новый default loader | визуально проверить картинки |
| B6 | `next/script` с `beforeInteractive` только в `_document` | поиск `<Script strategy="beforeInteractive">` |
| B7 | Удалены устаревшие `next/router` API | поиск `router.events`, `router.beforePopState` |

### 3. Чек-лист визуальной приёмки

- [ ] `npm run dev` поднимает фронт без ошибок гидрации
- [ ] Все ключевые страницы открываются: `/`, `/dashboard`, `/signals`, `/admin/review`, `/auth/login`, `/auth/register`, `/auth/forgot-password`, `/auth/reset-password`
- [ ] Stripe checkout flow (`/pricing` → checkout) работает в обе стороны
- [ ] Sentry получает события (если включён в `.env.local`)
- [ ] Картинки (`next/image`) грузятся
- [ ] Lighthouse: CWV не хуже текущих
- [ ] `npm run build` без warnings/errors
- [ ] `next-bundle-analyzer` (если есть): сравнение размеров chunks

### 4. CI/CD

- В GitHub Actions раскрыть, что миграция произошла, и обновить кеш `.next/`.
- Прогнать E2E (`/.github/workflows/e2e.yml`) на staging до мерджа.

### 5. Rollback план

Если в стейджинге всплывают баги:
1. Откатить ветку `chore/nextjs-16-migration` до `bb7c376` (точка перед миграцией).
2. Все backend / G4 / OpenAPI / compose-ports фиксы остаются на `main`.

---

## Когда удалить этот документ

Когда выполнено всё из секции «Что осталось сделать» и Next 16 в проде >= 7 дней без регрессий, документ архивировать в `docs/archive/MIGRATION_NEXT_16.md` или удалить вместе с пунктом 2 в `docs/AUDIT_REPORT_2026_04_28.md` (Next 14→16).
