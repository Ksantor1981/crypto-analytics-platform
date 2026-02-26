"""
Stripe Checkout — create sessions for subscription payments.
"""
import os
import logging
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PRICE_MAP = {
    "premium": {"amount": 1900, "name": "Premium Plan", "interval": "month"},
    "pro": {"amount": 4900, "name": "Pro Plan", "interval": "month"},
}


class CheckoutRequest(BaseModel):
    plan: str
    success_url: str = "http://localhost:3000/subscription?success=true"
    cancel_url: str = "http://localhost:3000/subscription?cancelled=true"


@router.post("/create-checkout")
async def create_checkout_session(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe Checkout session for subscription."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    plan_config = PRICE_MAP.get(req.plan)
    if not plan_config:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {req.plan}. Available: {list(PRICE_MAP.keys())}")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": plan_config["name"]},
                    "unit_amount": plan_config["amount"],
                    "recurring": {"interval": plan_config["interval"]},
                },
                "quantity": 1,
            }],
            customer_email=current_user.email,
            metadata={"user_id": str(current_user.id), "plan": req.plan},
            success_url=req.success_url,
            cancel_url=req.cancel_url,
        )
        return {"checkout_url": session.url, "session_id": session.id}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (subscription created/updated/cancelled)."""
    import json

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = json.loads(payload)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        user_id = data.get("metadata", {}).get("user_id")
        plan = data.get("metadata", {}).get("plan")
        email = data.get("customer_email")
        logger.info(f"Checkout completed: user={user_id} plan={plan} email={email}")

        if user_id and plan:
            from app.core.database import SessionLocal
            from app.models.user import User
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user:
                    user.role = "PREMIUM_USER" if plan == "premium" else "PRO_USER"
                    user.stripe_customer_id = data.get("customer")
                    db.commit()
                    logger.info(f"User {user_id} upgraded to {plan}")
            finally:
                db.close()

    elif event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
        logger.info(f"Subscription event: {event_type}")

    return {"received": True}


@router.get("/plans")
async def get_plans():
    """Get available subscription plans."""
    return {
        "plans": [
            {"id": "free", "name": "Free", "price": 0, "features": ["3 канала", "Базовая аналитика"]},
            {"id": "premium", "name": "Premium", "price": 19, "features": ["15 каналов", "Excel экспорт", "Push уведомления"]},
            {"id": "pro", "name": "Pro", "price": 49, "features": ["Безлимит каналов", "ML предсказания", "API доступ"]},
        ],
        "stripe_configured": bool(stripe.api_key),
    }
