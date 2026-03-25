# Stripe Checkout — smoke-тест (test mode)

Краткая инструкция, чтобы убедиться, что оплата в **test mode** проходит end-to-end: backend → Stripe Hosted Checkout → редирект обратно.

## 1. Переменные окружения (backend)

В `backend/.env` (или экспорт в shell):

| Переменная | Где взять |
|------------|-----------|
| `STRIPE_SECRET_KEY` | [Dashboard → Developers → API keys](https://dashboard.stripe.com/test/apikeys) — **Secret key** (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Опционально для локали; для webhook — Signing secret из Stripe CLI или Dashboard |

Убедитесь, что **не** подставлен `sk_live_` на дев-стенде.

Frontend:

| Переменная | Значение |
|------------|----------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` (или URL вашего API) |

## 2. Запуск

```powershell
# Терминал 1 — API
cd backend
# venv + pip install -r requirements.txt
$env:SECRET_KEY="минимум-32-символа-для-jwt"
$env:STRIPE_SECRET_KEY="sk_test_..."
python -m uvicorn app.main:app --reload --port 8000

# Терминал 2 — Next.js
cd frontend
npm run dev
```

## 3. Сценарий smoke

1. Откройте `http://localhost:3000/auth/register`, создайте пользователя (или войдите).
2. Перейдите на `http://localhost:3000/subscription`.
3. Нажмите оплату **Premium** или **Pro** (не Free).
4. Должен открыться **Stripe Checkout** (hosted page).
5. Карта теста: `4242 4242 4242 4242`, любая будущая дата CVC, любой ZIP.
6. После успеха — редирект на `/subscription?success=true` с зелёным баннером.

## 4. Если не открывается Checkout

- В консоли браузера и Network смотрите ответ `POST .../api/v1/stripe/create-checkout` (401 → нет токена; 422/500 → логи backend).
- Проверьте, что в Stripe Dashboard для test mode созданы **Products/Prices** или что backend мапит `plan` на существующие `price_...` (см. `stripe_checkout` в коде).

## 5. Webhook (опционально)

Локально:

```bash
stripe listen --forward-to localhost:8000/api/v1/stripe/webhook
```

Подставьте выданный `whsec_...` в `STRIPE_WEBHOOK_SECRET`.

---

*Документ для фазы готовности продукта; не храните реальные ключи в репозитории.*
