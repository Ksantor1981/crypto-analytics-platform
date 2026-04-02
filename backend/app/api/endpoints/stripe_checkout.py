"""
Stripe Checkout — create sessions for subscription payments.
"""
import os
import logging
import uuid
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.core.rate_limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# In-memory store for E2E/mock checkout sessions.
# Only intended to be used with STRIPE_MOCK_MODE=true (CI/tests).
MOCK_CHECKOUT_SESSIONS: dict[str, dict[str, str]] = {}

PRICE_MAP = {
    "premium": {"amount": 1900, "name": "Premium Plan", "interval": "month"},
    "pro": {"amount": 4900, "name": "Pro Plan", "interval": "month"},
}


class CheckoutRequest(BaseModel):
    plan: str
    success_url: str = "http://localhost:3000/subscription?success=true"
    cancel_url: str = "http://localhost:3000/subscription?cancelled=true"


@router.post("/create-checkout")
@limiter.limit("10/hour")
async def create_checkout_session(
    request: Request,
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe Checkout session for subscription."""
    settings = get_settings()
    stripe.api_key = settings.STRIPE_SECRET_KEY or ""
    mock_mode = bool(getattr(settings, "STRIPE_MOCK_MODE", False))

    if not stripe.api_key and not mock_mode:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    plan_config = PRICE_MAP.get(req.plan)
    if not plan_config:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {req.plan}. Available: {list(PRICE_MAP.keys())}")

    try:
        if mock_mode:
            # Deterministic fake checkout for E2E: we store mapping server-side
            # and auto-complete it from the generated "checkout page".
            session_id = str(uuid.uuid4())
            MOCK_CHECKOUT_SESSIONS[session_id] = {
                "user_id": str(current_user.id),
                "plan": req.plan,
                "success_url": req.success_url,
                "cancel_url": req.cancel_url,
            }
            base_url = str(request.base_url).rstrip("/")
            checkout_url = f"{base_url}{settings.API_V1_STR}/stripe/mock-checkout/{session_id}"
            return {"checkout_url": checkout_url, "session_id": session_id, "mock": True}

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
        return {"checkout_url": session.url, "session_id": session.id, "mock": False}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


class MockCheckoutCompleteRequest(BaseModel):
    session_id: str


@router.get("/mock-checkout/{session_id}")
async def mock_checkout_page(session_id: str):
    settings = get_settings()
    if not getattr(settings, "STRIPE_MOCK_MODE", False):
        raise HTTPException(status_code=404, detail="Mock mode disabled")

    if session_id not in MOCK_CHECKOUT_SESSIONS:
        raise HTTPException(status_code=404, detail="Mock checkout session not found")

    complete_path = f"{settings.API_V1_STR.rstrip('/')}/stripe/mock/complete"

    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Mock Stripe Checkout</title>
  </head>
  <body style="font-family: Arial, sans-serif; padding: 24px;">
    <h1>Mock Stripe Checkout</h1>
    <p id="status">Processing...</p>
    <script>
      (async () => {{
        try {{
          const res = await fetch('{complete_path}', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ session_id: '{session_id}' }})
          }});
          const data = await res.json();
          const url = data && data.success_url ? data.success_url : '/subscription?success=true';
          window.location.href = url;
        }} catch (e) {{
          document.getElementById('status').textContent = 'Mock completion failed';
        }}
      }})();
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html)


@router.post("/mock/complete")
async def mock_checkout_complete(payload: MockCheckoutCompleteRequest):
    settings = get_settings()
    if not getattr(settings, "STRIPE_MOCK_MODE", False):
        raise HTTPException(status_code=404, detail="Mock mode disabled")

    data = MOCK_CHECKOUT_SESSIONS.get(payload.session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Mock checkout session not found")

    from app.core.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(data["user_id"])).first()
        if user:
            plan = data["plan"]
            user.role = "PREMIUM_USER" if plan == "premium" else "PRO_USER"
            user.stripe_customer_id = f"mock_customer_{payload.session_id}"
            db.commit()
    finally:
        db.close()

    # Drop mapping after completion (keeps memory bounded).
    MOCK_CHECKOUT_SESSIONS.pop(payload.session_id, None)
    return {"received": True, "success_url": data["success_url"]}


@router.post("/webhook")
@limiter.limit("120/minute")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (subscription created/updated/cancelled)."""
    settings = get_settings()
    webhook_secret = (settings.STRIPE_WEBHOOK_SECRET or "").strip()
    if not webhook_secret:
        raise HTTPException(
            status_code=501,
            detail="Stripe webhook is not configured (set STRIPE_WEBHOOK_SECRET)",
        )

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"Webhook invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload") from e
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook bad signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature") from e

    try:
        event_type = event["type"]
        data = event["data"]["object"]
    except (KeyError, TypeError) as e:
        logger.error("Webhook event shape invalid: %s", e)
        raise HTTPException(status_code=400, detail="Invalid event shape") from e

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
