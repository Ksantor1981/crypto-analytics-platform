"""
Stripe Webhooks - Enhanced with Email Notifications
Part of Task 2.2.4: Email уведомления о платежах
"""
import logging
import stripe
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from ...database import get_db
from ...core.config import settings
from ...models.user import User, SubscriptionPlan, SubscriptionStatus
from ...models.subscription import Subscription, Payment
from ...services.email_service import email_service

logger = logging.getLogger(__name__)
router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events with email notifications
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        await handle_payment_succeeded(event['data']['object'], db, background_tasks)
    elif event['type'] == 'payment_intent.payment_failed':
        await handle_payment_failed(event['data']['object'], db, background_tasks)
    elif event['type'] == 'customer.subscription.created':
        await handle_subscription_created(event['data']['object'], db, background_tasks)
    elif event['type'] == 'customer.subscription.updated':
        await handle_subscription_updated(event['data']['object'], db, background_tasks)
    elif event['type'] == 'customer.subscription.deleted':
        await handle_subscription_cancelled(event['data']['object'], db, background_tasks)
    elif event['type'] == 'invoice.payment_succeeded':
        await handle_invoice_payment_succeeded(event['data']['object'], db, background_tasks)
    elif event['type'] == 'invoice.payment_failed':
        await handle_invoice_payment_failed(event['data']['object'], db, background_tasks)
    else:
        logger.info(f"Unhandled event type: {event['type']}")

    return {"status": "success"}

async def handle_payment_succeeded(
    payment_intent,
    db: Session,
    background_tasks: BackgroundTasks
):
    """Handle successful payment with email notification"""
    try:
        # Find user by Stripe customer ID
        customer_id = payment_intent.get('customer')
        if not customer_id:
            logger.warning("No customer ID in payment intent")
            return

        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning(f"User not found for customer ID: {customer_id}")
            return

        # Create payment record
        payment = Payment(
            user_id=user.id,
            stripe_payment_intent_id=payment_intent['id'],
            amount=payment_intent['amount'] / 100,  # Convert from cents
            currency=payment_intent['currency'].upper(),
            status='succeeded',
            stripe_invoice_url=payment_intent.get('invoice')
        )
        db.add(payment)

        # Find associated subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == 'active'
        ).first()

        if subscription:
            # Send email notification in background
            background_tasks.add_task(
                email_service.send_payment_success_notification,
                user=user,
                payment=payment,
                subscription=subscription
            )

        db.commit()
        logger.info(f"Payment succeeded for user {user.email}: {payment.amount} {payment.currency}")

    except Exception as e:
        logger.error(f"Error handling payment succeeded: {e}")
        db.rollback()

async def handle_payment_failed(
    payment_intent,
    db: Session,
    background_tasks: BackgroundTasks
):
    """Handle failed payment with email notification"""
    try:
        customer_id = payment_intent.get('customer')
        if not customer_id:
            return

        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            return

        # Find associated subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status.in_(['active', 'past_due'])
        ).first()

        if subscription:
            # Update subscription status to past_due
            subscription.status = 'past_due'
            user.subscription_status = SubscriptionStatus.PAST_DUE

            # Get error message
            error_message = payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')

            # Send email notification in background
            background_tasks.add_task(
                email_service.send_payment_failed_notification,
                user=user,
                subscription=subscription,
                error_message=error_message
            )

        db.commit()
        logger.info(f"Payment failed for user {user.email}")

    except Exception as e:
        logger.error(f"Error handling payment failed: {e}")
        db.rollback()

async def handle_subscription_created(
    subscription_obj,
    db: Session,
    background_tasks: BackgroundTasks
):
    """Handle new subscription creation"""
    try:
        customer_id = subscription_obj['customer']
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        
        if not user:
            return

        # Update user subscription info
        plan_id = subscription_obj['items']['data'][0]['price']['id']
        plan_name = get_plan_name_from_stripe_price_id(plan_id)
        
        user.subscription_plan = get_subscription_plan_enum(plan_name)
        user.subscription_status = SubscriptionStatus.ACTIVE
        user.stripe_subscription_id = subscription_obj['id']
        user.subscription_start_date = datetime.fromtimestamp(subscription_obj['current_period_start'])
        user.subscription_end_date = datetime.fromtimestamp(subscription_obj['current_period_end'])
        
        # Update user limits based on plan
        user.update_subscription_plan(user.subscription_plan)

        # Create subscription record
        subscription = Subscription(
            user_id=user.id,
            stripe_subscription_id=subscription_obj['id'],
            plan_name=plan_name,
            status='active',
            current_period_start=datetime.fromtimestamp(subscription_obj['current_period_start']),
            current_period_end=datetime.fromtimestamp(subscription_obj['current_period_end'])
        )
        db.add(subscription)

        db.commit()
        logger.info(f"Subscription created for user {user.email}: {plan_name}")

    except Exception as e:
        logger.error(f"Error handling subscription created: {e}")
        db.rollback()

async def handle_subscription_cancelled(
    subscription_obj,
    db: Session,
    background_tasks: BackgroundTasks
):
    """Handle subscription cancellation with email notification"""
    try:
        customer_id = subscription_obj['customer']
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        
        if not user:
            return

        # Update user subscription status
        user.subscription_status = SubscriptionStatus.CANCELLED
        
        # Find subscription record
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_obj['id']
        ).first()

        if subscription:
            subscription.status = 'cancelled'
            
            # Send cancellation email in background
            background_tasks.add_task(
                email_service.send_subscription_cancelled_notification,
                user=user,
                subscription=subscription
            )

        db.commit()
        logger.info(f"Subscription cancelled for user {user.email}")

    except Exception as e:
        logger.error(f"Error handling subscription cancelled: {e}")
        db.rollback()

async def handle_invoice_payment_succeeded(
    invoice,
    db: Session,
    background_tasks: BackgroundTasks
):
    """Handle successful invoice payment"""
    try:
        customer_id = invoice['customer']
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        
        if not user:
            return

        # This is a renewal payment
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.stripe_subscription_id == invoice['subscription']
        ).first()

        if subscription:
            # Update subscription period
            subscription.current_period_start = datetime.fromtimestamp(invoice['period_start'])
            subscription.current_period_end = datetime.fromtimestamp(invoice['period_end'])
            
            # Create payment record
            payment = Payment(
                user_id=user.id,
                stripe_invoice_id=invoice['id'],
                amount=invoice['amount_paid'] / 100,
                currency=invoice['currency'].upper(),
                status='succeeded',
                stripe_invoice_url=invoice['hosted_invoice_url']
            )
            db.add(payment)

            # Send renewal confirmation email
            background_tasks.add_task(
                email_service.send_payment_success_notification,
                user=user,
                payment=payment,
                subscription=subscription
            )

        db.commit()
        logger.info(f"Invoice payment succeeded for user {user.email}")

    except Exception as e:
        logger.error(f"Error handling invoice payment succeeded: {e}")
        db.rollback()

async def handle_invoice_payment_failed(
    invoice,
    db: Session,
    background_tasks: BackgroundTasks
):
    """Handle failed invoice payment"""
    try:
        customer_id = invoice['customer']
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        
        if not user:
            return

        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.stripe_subscription_id == invoice['subscription']
        ).first()

        if subscription:
            # Update status to past_due
            subscription.status = 'past_due'
            user.subscription_status = SubscriptionStatus.PAST_DUE

            # Send payment failed email
            background_tasks.add_task(
                email_service.send_payment_failed_notification,
                user=user,
                subscription=subscription,
                error_message="Invoice payment failed"
            )

        db.commit()
        logger.info(f"Invoice payment failed for user {user.email}")

    except Exception as e:
        logger.error(f"Error handling invoice payment failed: {e}")
        db.rollback()

def get_plan_name_from_stripe_price_id(price_id: str) -> str:
    """Map Stripe price ID to plan name"""
    price_map = {
        settings.STRIPE_PREMIUM_PRICE_ID: "Premium",
        settings.STRIPE_PRO_PRICE_ID: "Pro"
    }
    return price_map.get(price_id, "Premium")

def get_subscription_plan_enum(plan_name: str) -> SubscriptionPlan:
    """Map plan name to SubscriptionPlan enum"""
    plan_map = {
        "Premium": SubscriptionPlan.PREMIUM,
        "Pro": SubscriptionPlan.PRO
    }
    return plan_map.get(plan_name, SubscriptionPlan.PREMIUM)
