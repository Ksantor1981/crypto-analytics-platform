from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from math import ceil
from datetime import datetime
import stripe
import logging

from app.core.database import get_db
from app.core.auth import (
    get_current_active_user,
    require_admin,
    require_premium
)
from app.core.config import get_settings
from app.services.payment_service import PaymentService
from app import schemas
from app.models.user import User, UserRole

# Получаем настройки
settings = get_settings()

# Configure Stripe webhook endpoint secret
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
webhook_secret = settings.STRIPE_WEBHOOK_SECRET

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create-payment-intent", response_model=schemas.payment.PaymentIntentResponse)
async def create_payment_intent(
    intent_data: schemas.payment.PaymentIntentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe payment intent for current user."""
    payment_service = PaymentService(db)
    
    payment_intent = payment_service.create_payment_intent(current_user.id, intent_data)
    
    return payment_intent


@router.get("/me", response_model=schemas.payment.PaymentListResponse)
async def get_my_payments(
    skip: int = Query(0, ge=0, description="Number of payments to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of payments to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's payments."""
    payment_service = PaymentService(db)
    
    payments, total = payment_service.get_user_payments(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    # Calculate pagination
    pages = ceil(total / limit) if total > 0 else 0
    page = (skip // limit) + 1
    
    # Convert to response format
    payment_responses = []
    for payment in payments:
        payment_dict = schemas.payment.PaymentWithUser.from_orm(payment).dict()
        payment_dict["user_email"] = current_user.email
        payment_dict["user_name"] = current_user.full_name
        payment_responses.append(schemas.payment.PaymentWithUser(**payment_dict))
    
    return schemas.payment.PaymentListResponse(
        payments=payment_responses,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get("/me/{payment_id}", response_model=schemas.payment.PaymentResponse)
async def get_my_payment(
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific payment for current user."""
    payment_service = PaymentService(db)
    
    payment = payment_service.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check if payment belongs to current user
    if payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return schemas.payment.PaymentResponse.from_orm(payment)


@router.post("/me/{payment_id}/cancel", response_model=schemas.payment.PaymentResponse)
async def cancel_my_payment(
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel current user's pending payment."""
    payment_service = PaymentService(db)
    
    payment = payment_service.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check if payment belongs to current user
    if payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    cancelled_payment = payment_service.cancel_payment(payment_id)
    
    return schemas.payment.PaymentResponse.from_orm(cancelled_payment)


# Stripe webhook endpoint
@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe webhooks not configured"
        )
    
    try:
        # Get the raw body
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        # Verify webhook signature
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
        event_type = event['type']
        event_data = event['data']['object']

        payment_service = PaymentService(db)

        if event_type.startswith('payment_intent.'):
            webhook_data = schemas.payment.StripeWebhookPayment(
                event_type=event_type,
                payment_intent_id=event_data['id'],
                amount=event_data['amount'] / 100,
                currency=event_data['currency'].upper(),
                status=event_data['status'],
                customer_id=event_data.get('customer'),
                subscription_id=event_data.get('subscription'),
                invoice_id=event_data.get('invoice'),
                failure_code=event_data.get('last_payment_error', {}).get('code'),
                failure_message=event_data.get('last_payment_error', {}).get('message'),
                receipt_url=event_data.get('charges', {}).get('data', [{}])[0].get('receipt_url'),
                created_at=datetime.utcfromtimestamp(event_data['created'])
            )
            payment_service.process_stripe_webhook(webhook_data)

        elif event_type in ['customer.subscription.updated', 'customer.subscription.deleted']:
            subscription = event_data
            customer_id = subscription.get('customer')
            status = subscription.get('status')

            if customer_id and status in ['canceled', 'unpaid', 'past_due'] or event_type == 'customer.subscription.deleted':
                user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
                if user:
                    user.role = UserRole.FREE_USER
                    user.current_subscription_expires = None
                    db.add(user)
                    db.commit()
                    logger.info(f"User {user.email} has been downgraded to FREE_USER due to subscription status: {status}")
            
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


# Admin endpoints
@router.get("/", response_model=schemas.payment.PaymentListResponse, dependencies=[Depends(require_admin)])
async def get_payments(
    skip: int = Query(0, ge=0, description="Number of payments to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of payments to return"),
        status: Optional[schemas.payment.PaymentStatus] = Query(None, description="Filter by status"),
        payment_method: Optional[schemas.payment.PaymentMethod] = Query(None, description="Filter by payment method"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db)
):
    """Get all payments (admin only)."""
    payment_service = PaymentService(db)
    
    payments, total = payment_service.get_payments(
        skip=skip,
        limit=limit,
        status=status,
        payment_method=payment_method,
        user_id=user_id
    )
    
    # Calculate pagination
    pages = ceil(total / limit) if total > 0 else 0
    page = (skip // limit) + 1
    
    # Convert to response format with user info
    payment_responses = []
    for payment in payments:
        payment_dict = schemas.payment.PaymentWithUser.from_orm(payment).dict()
        if payment.user:
            payment_dict["user_email"] = payment.user.email
            payment_dict["user_name"] = payment.user.full_name
        payment_responses.append(schemas.payment.PaymentWithUser(**payment_dict))
    
    return schemas.payment.PaymentListResponse(
        payments=payment_responses,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get("/{payment_id}", response_model=schemas.payment.PaymentWithUser, dependencies=[Depends(require_admin)])
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """Get payment by ID (admin only)."""
    payment_service = PaymentService(db)
    
    payment = payment_service.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Convert to response with user info
    payment_dict = schemas.payment.PaymentWithUser.from_orm(payment).dict()
    if payment.user:
        payment_dict["user_email"] = payment.user.email
        payment_dict["user_name"] = payment.user.full_name
    
    return schemas.payment.PaymentWithUser(**payment_dict)


@router.post("/admin/create", response_model=schemas.payment.PaymentResponse, dependencies=[Depends(require_admin)])
async def create_payment_admin(
        payment_data: schemas.payment.PaymentCreate,
    db: Session = Depends(get_db)
):
    """Create a payment for any user (admin only)."""
    payment_service = PaymentService(db)
    
    payment = payment_service.create_payment(payment_data)
    
    return schemas.payment.PaymentResponse.from_orm(payment)


@router.put("/{payment_id}", response_model=schemas.payment.PaymentResponse, dependencies=[Depends(require_admin)])
async def update_payment(
    payment_id: int,
        payment_data: schemas.payment.PaymentUpdate,
    db: Session = Depends(get_db)
):
    """Update payment (admin only)."""
    payment_service = PaymentService(db)
    
    payment = payment_service.update_payment(payment_id, payment_data)
    
    return schemas.payment.PaymentResponse.from_orm(payment)


@router.post("/{payment_id}/refund", response_model=schemas.payment.RefundResponse, dependencies=[Depends(require_admin)])
async def refund_payment(
    payment_id: int,
        refund_data: schemas.payment.RefundRequest,
    db: Session = Depends(get_db)
):
    """Process payment refund (admin only)."""
    payment_service = PaymentService(db)
    
    refund = payment_service.refund_payment(payment_id, refund_data)
    
    return refund


@router.post("/{payment_id}/cancel", response_model=schemas.payment.PaymentResponse, dependencies=[Depends(require_admin)])
async def cancel_payment_admin(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """Cancel payment (admin only)."""
    payment_service = PaymentService(db)
    
    payment = payment_service.cancel_payment(payment_id)
    
    return schemas.payment.PaymentResponse.from_orm(payment)


@router.get("/stats/overview", response_model=schemas.payment.PaymentStats, dependencies=[Depends(require_admin)])
async def get_payment_stats(db: Session = Depends(get_db)):
    """Get payment statistics (admin only)."""
    payment_service = PaymentService(db)
    
    stats = payment_service.get_payment_stats()
    
    return stats


# Stripe customer management
@router.post("/customers/create", response_model=schemas.payment.CustomerResponse, dependencies=[Depends(require_admin)])
async def create_stripe_customer(
        customer_data: schemas.payment.CustomerCreate,
    db: Session = Depends(get_db)
):
    """Create Stripe customer (admin only)."""
    try:
        customer = stripe.Customer.create(
            email=customer_data.email,
            name=customer_data.name,
            phone=customer_data.phone,
            address=customer_data.address,
            metadata=customer_data.metadata or {}
        )
        
        # Get payment methods
        payment_methods = stripe.PaymentMethod.list(
            customer=customer.id,
            type="card"
        )
        
        return schemas.payment.CustomerResponse(
            customer_id=customer.id,
            email=customer.email,
            name=customer.name,
            created_at=datetime.utcfromtimestamp(customer.created),
            payment_methods=[pm.to_dict() for pm in payment_methods.data]
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer creation error: {str(e)}"
        )


@router.get("/customers/{customer_id}", response_model=schemas.payment.CustomerResponse, dependencies=[Depends(require_admin)])
async def get_stripe_customer(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """Get Stripe customer (admin only)."""
    try:
        customer = stripe.Customer.retrieve(customer_id)
        
        # Get payment methods
        payment_methods = stripe.PaymentMethod.list(
            customer=customer.id,
            type="card"
        )
        
        return schemas.payment.CustomerResponse(
            customer_id=customer.id,
            email=customer.email,
            name=customer.name,
            created_at=datetime.utcfromtimestamp(customer.created),
            default_payment_method=customer.default_source,
            payment_methods=[pm.to_dict() for pm in payment_methods.data]
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving Stripe customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer not found: {str(e)}"
        )


# Invoice management
@router.post("/invoices/create", response_model=InvoiceResponse, dependencies=[Depends(require_admin)])
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db)
):
    """Create Stripe invoice (admin only)."""
    try:
        # Create invoice
        invoice = stripe.Invoice.create(
            customer=invoice_data.customer_id,
            subscription=invoice_data.subscription_id,
            amount_due=int(invoice_data.amount * 100),  # Convert to cents
            currency=invoice_data.currency.lower(),
            description=invoice_data.description,
            due_date=int(invoice_data.due_date.timestamp()) if invoice_data.due_date else None,
            auto_advance=invoice_data.auto_advance
        )
        
        # Finalize invoice
        if invoice_data.auto_advance:
            invoice = stripe.Invoice.finalize_invoice(invoice.id)
        
        return InvoiceResponse(
            invoice_id=invoice.id,
            customer_id=invoice.customer,
            amount=invoice.amount_due / 100,  # Convert from cents
            currency=invoice.currency.upper(),
            status=invoice.status,
            invoice_pdf=invoice.invoice_pdf,
            hosted_invoice_url=invoice.hosted_invoice_url,
            created_at=datetime.utcfromtimestamp(invoice.created),
            due_date=datetime.utcfromtimestamp(invoice.due_date) if invoice.due_date else None
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice creation error: {str(e)}"
        )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse, dependencies=[Depends(require_admin)])
async def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db)
):
    """Get Stripe invoice (admin only)."""
    try:
        invoice = stripe.Invoice.retrieve(invoice_id)
        
        return InvoiceResponse(
            invoice_id=invoice.id,
            customer_id=invoice.customer,
            amount=invoice.amount_due / 100,  # Convert from cents
            currency=invoice.currency.upper(),
            status=invoice.status,
            invoice_pdf=invoice.invoice_pdf,
            hosted_invoice_url=invoice.hosted_invoice_url,
            created_at=datetime.utcfromtimestamp(invoice.created),
            due_date=datetime.utcfromtimestamp(invoice.due_date) if invoice.due_date else None
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving Stripe invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice not found: {str(e)}"
        )


# Premium user endpoints
@router.get("/premium/history", dependencies=[Depends(require_premium)])
async def get_premium_payment_history(
    skip: int = Query(0, ge=0, description="Number of payments to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of payments to return"),
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db)
):
    """Get premium user's payment history with detailed information."""
    payment_service = PaymentService(db)
    
    payments, total = payment_service.get_user_payments(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    # Calculate pagination
    pages = ceil(total / limit) if total > 0 else 0
    page = (skip // limit) + 1
    
    # Enhanced response with additional details for premium users
    payment_responses = []
    for payment in payments:
        payment_dict = PaymentWithUser.from_orm(payment).dict()
        payment_dict["user_email"] = current_user.email
        payment_dict["user_name"] = current_user.full_name
        
        # Add premium-specific information
        if payment.stripe_payment_intent_id:
            payment_dict["stripe_dashboard_url"] = f"https://dashboard.stripe.com/payments/{payment.stripe_payment_intent_id}"
        
        payment_responses.append(PaymentWithUser(**payment_dict))
    
    return PaymentListResponse(
        payments=payment_responses,
        total=total,
        page=page,
        size=limit,
        pages=pages
    ) 


@router.post("/send-payment-reminders", dependencies=[Depends(require_admin)])
async def send_payment_reminders(
    db: Session = Depends(get_db)
):
    """Send payment reminders for upcoming billing dates (admin only)."""
    payment_service = PaymentService(db)
    
    result = await payment_service.send_payment_reminders()
    
    if result["success"]:
        return {
            "message": "Payment reminders sent successfully",
            "reminders_sent": result["reminders_sent"],
            "total_subscriptions": result["total_subscriptions"]
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send payment reminders: {result.get('error', 'Unknown error')}"
        )


@router.post("/send-expired-notifications", dependencies=[Depends(require_admin)])
async def send_expired_subscription_notifications(
    db: Session = Depends(get_db)
):
    """Send notifications for expired subscriptions (admin only)."""
    payment_service = PaymentService(db)
    
    result = await payment_service.send_expired_subscription_notifications()
    
    if result["success"]:
        return {
            "message": "Expired subscription notifications sent successfully",
            "notifications_sent": result["notifications_sent"],
            "total_expired": result["total_expired"]
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send expired notifications: {result.get('error', 'Unknown error')}"
        ) 