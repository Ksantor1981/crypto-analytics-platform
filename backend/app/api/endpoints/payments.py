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
from app.core.config import settings
from app.services.payment_service import PaymentService
from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
    PaymentWithUser,
    PaymentListResponse,
    PaymentStats,
    PaymentAnalytics,
    RefundRequest,
    RefundResponse,
    PaymentIntentCreate,
    PaymentIntentResponse,
    CustomerCreate,
    CustomerResponse,
    InvoiceCreate,
    InvoiceResponse,
    StripeWebhookPayment,
    PaymentStatus,
    PaymentMethod
)
from app.models.user import User

# Configure Stripe webhook endpoint secret
stripe.api_key = settings.STRIPE_SECRET_KEY
webhook_secret = settings.STRIPE_WEBHOOK_SECRET

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    intent_data: PaymentIntentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe payment intent for current user."""
    payment_service = PaymentService(db)
    
    payment_intent = payment_service.create_payment_intent(current_user.id, intent_data)
    
    return payment_intent


@router.get("/me", response_model=PaymentListResponse)
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
        payment_dict = PaymentWithUser.from_orm(payment).dict()
        payment_dict["user_email"] = current_user.email
        payment_dict["user_name"] = current_user.full_name
        payment_responses.append(PaymentWithUser(**payment_dict))
    
    return PaymentListResponse(
        payments=payment_responses,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get("/me/{payment_id}", response_model=PaymentResponse)
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
    
    return PaymentResponse.from_orm(payment)


@router.post("/me/{payment_id}/cancel", response_model=PaymentResponse)
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
    
    return PaymentResponse.from_orm(cancelled_payment)


# Stripe webhook endpoint
@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events."""
    try:
        # Get the raw body
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle the event
        if event['type'] in [
            'payment_intent.succeeded',
            'payment_intent.payment_failed',
            'payment_intent.canceled',
            'payment_intent.processing'
        ]:
            payment_intent = event['data']['object']
            
            # Create webhook data
            webhook_data = StripeWebhookPayment(
                event_type=event['type'],
                payment_intent_id=payment_intent['id'],
                amount=payment_intent['amount'] / 100,  # Convert from cents
                currency=payment_intent['currency'].upper(),
                status=payment_intent['status'],
                customer_id=payment_intent.get('customer'),
                subscription_id=payment_intent.get('subscription'),
                invoice_id=payment_intent.get('invoice'),
                failure_code=payment_intent.get('last_payment_error', {}).get('code'),
                failure_message=payment_intent.get('last_payment_error', {}).get('message'),
                receipt_url=payment_intent.get('charges', {}).get('data', [{}])[0].get('receipt_url'),
                created_at=datetime.utcfromtimestamp(payment_intent['created'])
            )
            
            # Process webhook
            payment_service = PaymentService(db)
            payment_service.process_stripe_webhook(webhook_data)
            
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


# Admin endpoints
@router.get("/", response_model=PaymentListResponse, dependencies=[Depends(require_admin)])
async def get_payments(
    skip: int = Query(0, ge=0, description="Number of payments to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of payments to return"),
    status: Optional[PaymentStatus] = Query(None, description="Filter by status"),
    payment_method: Optional[PaymentMethod] = Query(None, description="Filter by payment method"),
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
        payment_dict = PaymentWithUser.from_orm(payment).dict()
        if payment.user:
            payment_dict["user_email"] = payment.user.email
            payment_dict["user_name"] = payment.user.full_name
        payment_responses.append(PaymentWithUser(**payment_dict))
    
    return PaymentListResponse(
        payments=payment_responses,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get("/{payment_id}", response_model=PaymentWithUser, dependencies=[Depends(require_admin)])
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
    payment_dict = PaymentWithUser.from_orm(payment).dict()
    if payment.user:
        payment_dict["user_email"] = payment.user.email
        payment_dict["user_name"] = payment.user.full_name
    
    return PaymentWithUser(**payment_dict)


@router.post("/admin/create", response_model=PaymentResponse, dependencies=[Depends(require_admin)])
async def create_payment_admin(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    """Create a payment for any user (admin only)."""
    payment_service = PaymentService(db)
    
    payment = payment_service.create_payment(payment_data)
    
    return PaymentResponse.from_orm(payment)


@router.put("/{payment_id}", response_model=PaymentResponse, dependencies=[Depends(require_admin)])
async def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db)
):
    """Update payment (admin only)."""
    payment_service = PaymentService(db)
    
    payment = payment_service.update_payment(payment_id, payment_data)
    
    return PaymentResponse.from_orm(payment)


@router.post("/{payment_id}/refund", response_model=RefundResponse, dependencies=[Depends(require_admin)])
async def refund_payment(
    payment_id: int,
    refund_data: RefundRequest,
    db: Session = Depends(get_db)
):
    """Process payment refund (admin only)."""
    payment_service = PaymentService(db)
    
    refund = payment_service.refund_payment(payment_id, refund_data)
    
    return refund


@router.post("/{payment_id}/cancel", response_model=PaymentResponse, dependencies=[Depends(require_admin)])
async def cancel_payment_admin(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """Cancel payment (admin only)."""
    payment_service = PaymentService(db)
    
    payment = payment_service.cancel_payment(payment_id)
    
    return PaymentResponse.from_orm(payment)


@router.get("/stats/overview", response_model=PaymentStats, dependencies=[Depends(require_admin)])
async def get_payment_stats(db: Session = Depends(get_db)):
    """Get payment statistics (admin only)."""
    payment_service = PaymentService(db)
    
    stats = payment_service.get_payment_stats()
    
    return stats


# Stripe customer management
@router.post("/customers/create", response_model=CustomerResponse, dependencies=[Depends(require_admin)])
async def create_stripe_customer(
    customer_data: CustomerCreate,
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
        
        return CustomerResponse(
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


@router.get("/customers/{customer_id}", response_model=CustomerResponse, dependencies=[Depends(require_admin)])
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
        
        return CustomerResponse(
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