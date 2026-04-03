"""
Сверка подписок в БД с Stripe (dry-run: только вывод расхождений).

Запуск из каталога backend с переменными окружения (DATABASE_URL, STRIPE_SECRET_KEY):

  python -m scripts.stripe_reconcile_subscriptions

Опционально: --apply — обновить subscription_status у пользователя по данным Stripe (осторожно в проде).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# backend/ в PYTHONPATH при запуске как python -m scripts.stripe_reconcile_subscriptions
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

_ROOT = _BACKEND.parent
_env = _ROOT / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(_env)
    except ImportError:
        pass


def _norm_stripe_status(status: str | None) -> str:
    s = (status or "").lower()
    if s in ("canceled", "cancelled"):
        return "cancelled"
    return s


def _norm_local_status(value: str | None) -> str:
    return (value or "").lower()


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile User subscription fields with Stripe")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply Stripe status to local subscription_status (use with care)",
    )
    parser.add_argument("--limit", type=int, default=500, help="Max users to scan")
    args = parser.parse_args()

    key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        print("STRIPE_SECRET_KEY is not set", file=sys.stderr)
        return 1

    import stripe
    from sqlalchemy.orm import Session

    from app.core.database import SessionLocal, engine
    from app.models.user import User, SubscriptionStatus

    stripe.api_key = key

    db: Session = SessionLocal()
    mismatches = 0
    errors = 0
    try:
        q = (
            db.query(User)
            .filter(User.stripe_subscription_id.isnot(None))
            .filter(User.stripe_subscription_id != "")
        )
        users = q.limit(args.limit).all()
        print(f"Checking {len(users)} user(s) with stripe_subscription_id…")
        for u in users:
            sid = (u.stripe_subscription_id or "").strip()
            if not sid:
                continue
            try:
                sub = stripe.Subscription.retrieve(sid)
            except Exception as e:
                errors += 1
                print(f"[error] user_id={u.id} subscription={sid}: {e}")
                continue
            remote = _norm_stripe_status(getattr(sub, "status", None))
            local = _norm_local_status(
                u.subscription_status.value if u.subscription_status else None
            )
            # active/trialing оба «платёжно активны»; грубое сравнение
            ok = remote == local
            if remote == "active" and local == "trialing":
                ok = True
            if remote == "trialing" and local == "active":
                ok = True
            if not ok:
                mismatches += 1
                print(
                    f"[mismatch] user_id={u.id} email={u.email} "
                    f"local_status={local} stripe_status={remote} sub={sid}"
                )
                if args.apply:
                    mapped = SubscriptionStatus.ACTIVE
                    if remote == "cancelled":
                        mapped = SubscriptionStatus.CANCELLED
                    elif remote == "past_due":
                        mapped = SubscriptionStatus.PAST_DUE
                    elif remote == "trialing":
                        mapped = SubscriptionStatus.TRIALING
                    elif remote == "active":
                        mapped = SubscriptionStatus.ACTIVE
                    elif remote in ("unpaid", "incomplete", "incomplete_expired"):
                        mapped = SubscriptionStatus.EXPIRED
                    u.subscription_status = mapped
                    db.commit()
                    print(f"  -> updated local subscription_status to {mapped.value}")
    finally:
        db.close()
        try:
            engine.dispose()
        except Exception:
            pass

    print(f"Done. mismatches={mismatches} stripe_errors={errors}")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
