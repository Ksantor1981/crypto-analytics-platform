from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, extract
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from decimal import Decimal
import stripe
import uuid
import logging

from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
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
    StripeWebhookPayment
)
from app.core.config import settings

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for payment processing and management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_payment(self, payment_data: PaymentCreate) -> Payment:
        """Create a new payment record."""
        # Verify user exists
        user = self.db.query(User).filter(User.id == payment_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate internal transaction ID
        internal_tx_id = f"PAY_{uuid.uuid4().hex[:12].upper()}"
        
        # Create payment
        db_payment = Payment(
            user_id=payment_data.user_id,
            amount=Decimal(str(payment_data.amount)),
            currency=payment_data.currency,
            description=payment_data.description,
            status=PaymentStatus.PENDING,
            payment_method=payment_data.payment_method,
            stripe_payment_intent_id=payment_data.stripe_payment_intent_id,
            billing_name=payment_data.billing_name,
            billing_email=payment_data.billing_email,
            billing_address=payment_data.billing_address,
            payment_metadata=payment_data.payment_metadata,
            internal_transaction_id=internal_tx_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_payment)
        self.db.commit()
        self.db.refresh(db_payment)
        
        return db_payment
    
    def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID with user info."""
        return self.db.query(Payment).options(joinedload(Payment.user)).filter(
            Payment.id == payment_id
        ).first()
    
    def get_user_payments(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Payment], int]:
        """Get user's payments with pagination."""
        query = self.db.query(Payment).filter(Payment.user_id == user_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and sorting
        payments = query.order_by(desc(Payment.created_at)).offset(skip).limit(limit).all()
        
        return payments, total
    
    def get_payments(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[PaymentStatus] = None,
        payment_method: Optional[PaymentMethod] = None,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Tuple[List[Payment], int]:
        """Get payments with filtering and pagination."""
        query = self.db.query(Payment).options(joinedload(Payment.user))
        
        # Apply filters
        if status:
            query = query.filter(Payment.status == status)
        
        if payment_method:
            query = query.filter(Payment.payment_method == payment_method)
        
        if user_id:
            query = query.filter(Payment.user_id == user_id)
        
        if date_from:
            query = query.filter(Payment.created_at >= date_from)
        
        if date_to:
            query = query.filter(Payment.created_at <= date_to)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and sorting
        payments = query.order_by(desc(Payment.created_at)).offset(skip).limit(limit).all()
        
        return payments, total
    
    def update_payment(self, payment_id: int, payment_data: PaymentUpdate) -> Optional[Payment]:
        """Update payment information."""
        payment = self.get_payment_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Update fields
        update_data = payment_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payment, field, value)
        
        payment.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(payment)
        
        return payment
    
    def create_payment_intent(self, user_id: int, intent_data: PaymentIntentCreate) -> PaymentIntentResponse:
        """Create a Stripe payment intent."""
        try:
            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Create or get Stripe customer
            stripe_customer = self._get_or_create_stripe_customer(user)
            
            # Convert amount to cents (Stripe expects cents)
            amount_cents = int(intent_data.amount * 100)
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=intent_data.currency.lower(),
                customer=stripe_customer.id,
                description=intent_data.description,
                automatic_payment_methods={
                    'enabled': intent_data.automatic_payment_methods,
                },
                metadata={
                    'user_id': str(user_id),
                    'subscription_id': str(intent_data.subscription_id) if intent_data.subscription_id else None,
                    'internal_user_email': user.email,
                }
            )
            
            # Create payment record
            payment_create = PaymentCreate(
                user_id=user_id,
                amount=intent_data.amount,
                currency=intent_data.currency,
                description=intent_data.description,
                payment_method=PaymentMethod.STRIPE_CARD,
                stripe_payment_intent_id=payment_intent.id,
                billing_name=intent_data.customer_name,
                billing_email=intent_data.customer_email or user.email,
                billing_address=intent_data.billing_address,
                payment_metadata={
                    'stripe_customer_id': stripe_customer.id,
                    'return_url': intent_data.return_url,
                    'cancel_url': intent_data.cancel_url
                }
            )
            
            self.create_payment(payment_create)
            
            return PaymentIntentResponse(
                client_secret=payment_intent.client_secret,
                payment_intent_id=payment_intent.id,
                amount=intent_data.amount,
                currency=intent_data.currency,
                status=payment_intent.status,
                next_action=payment_intent.next_action,
                return_url=intent_data.return_url
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment processing error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def process_stripe_webhook(self, webhook_data: StripeWebhookPayment) -> Optional[Payment]:
        """Process Stripe webhook events."""
        try:
            # Find payment by Stripe payment intent ID
            payment = self.db.query(Payment).filter(
                Payment.stripe_payment_intent_id == webhook_data.payment_intent_id
            ).first()
            
            if not payment:
                logger.warning(f"Payment not found for Stripe payment intent: {webhook_data.payment_intent_id}")
                return None
            
            # Update payment based on webhook event
            if webhook_data.event_type == "payment_intent.succeeded":
                payment.status = PaymentStatus.SUCCEEDED
                payment.processed_at = webhook_data.created_at
                payment.stripe_customer_id = webhook_data.customer_id
                payment.stripe_subscription_id = webhook_data.subscription_id
                payment.stripe_invoice_id = webhook_data.invoice_id
                payment.receipt_url = webhook_data.receipt_url
                
            elif webhook_data.event_type == "payment_intent.payment_failed":
                payment.status = PaymentStatus.FAILED
                payment.failed_at = webhook_data.created_at
                payment.failure_code = webhook_data.failure_code
                payment.failure_reason = webhook_data.failure_message
                
            elif webhook_data.event_type == "payment_intent.canceled":
                payment.status = PaymentStatus.CANCELLED
                
            elif webhook_data.event_type == "payment_intent.processing":
                payment.status = PaymentStatus.PROCESSING
            
            payment.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(payment)
            
            return payment
            
        except Exception as e:
            logger.error(f"Error processing Stripe webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing webhook"
            )
    
    def refund_payment(self, payment_id: int, refund_data: RefundRequest) -> RefundResponse:
        """Process payment refund."""
        payment = self.get_payment_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        if not payment.is_refundable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment is not refundable"
            )
        
        try:
            # Calculate refund amount
            refund_amount = refund_data.amount if refund_data.amount else float(payment.amount)
            refund_amount_cents = int(refund_amount * 100)
            
            # Create Stripe refund
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=refund_amount_cents,
                reason=refund_data.reason,
                metadata=refund_data.metadata or {}
            )
            
            # Update payment record
            payment.refunded_at = datetime.utcnow()
            payment.refund_amount = Decimal(str(refund_amount))
            payment.refund_reason = refund_data.reason
            payment.stripe_refund_id = refund.id
            
            if refund_amount >= float(payment.amount):
                payment.status = PaymentStatus.REFUNDED
            else:
                payment.status = PaymentStatus.PARTIALLY_REFUNDED
            
            payment.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(payment)
            
            return RefundResponse(
                refund_id=refund.id,
                amount=refund_amount,
                status=refund.status,
                reason=refund_data.reason,
                created_at=datetime.utcnow()
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing refund: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Refund processing error: {str(e)}"
            )
    
    def get_payment_stats(self) -> PaymentStats:
        """Get payment statistics."""
        # Basic counts
        total_payments = self.db.query(Payment).count()
        successful_payments = self.db.query(Payment).filter(
            Payment.status == PaymentStatus.SUCCEEDED
        ).count()
        failed_payments = self.db.query(Payment).filter(
            Payment.status == PaymentStatus.FAILED
        ).count()
        pending_payments = self.db.query(Payment).filter(
            Payment.status == PaymentStatus.PENDING
        ).count()
        refunded_payments = self.db.query(Payment).filter(
            Payment.status.in_([PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED])
        ).count()
        
        # Revenue calculations
        total_revenue_query = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == PaymentStatus.SUCCEEDED
        ).scalar() or 0
        
        refunded_amount_query = self.db.query(func.sum(Payment.refund_amount)).filter(
            Payment.refund_amount.isnot(None)
        ).scalar() or 0
        
        total_revenue = float(total_revenue_query)
        refunded_amount = float(refunded_amount_query)
        net_revenue = total_revenue - refunded_amount
        
        # Time-based revenue
        today = datetime.utcnow().date()
        today_revenue_query = self.db.query(func.sum(Payment.amount)).filter(
            and_(
                Payment.status == PaymentStatus.SUCCEEDED,
                func.date(Payment.created_at) == today
            )
        ).scalar() or 0
        
        this_month_revenue_query = self.db.query(func.sum(Payment.amount)).filter(
            and_(
                Payment.status == PaymentStatus.SUCCEEDED,
                extract('month', Payment.created_at) == datetime.utcnow().month,
                extract('year', Payment.created_at) == datetime.utcnow().year
            )
        ).scalar() or 0
        
        this_year_revenue_query = self.db.query(func.sum(Payment.amount)).filter(
            and_(
                Payment.status == PaymentStatus.SUCCEEDED,
                extract('year', Payment.created_at) == datetime.utcnow().year
            )
        ).scalar() or 0
        
        # Payment method breakdown
        stripe_card_payments = self.db.query(Payment).filter(
            Payment.payment_method == PaymentMethod.STRIPE_CARD
        ).count()
        stripe_bank_payments = self.db.query(Payment).filter(
            Payment.payment_method == PaymentMethod.STRIPE_BANK
        ).count()
        stripe_wallet_payments = self.db.query(Payment).filter(
            Payment.payment_method == PaymentMethod.STRIPE_WALLET
        ).count()
        crypto_payments = self.db.query(Payment).filter(
            Payment.payment_method == PaymentMethod.CRYPTO
        ).count()
        
        # Rates
        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
        refund_rate = (refunded_payments / successful_payments * 100) if successful_payments > 0 else 0
        
        # Average transaction value
        avg_transaction_value = (total_revenue / successful_payments) if successful_payments > 0 else 0
        
        return PaymentStats(
            total_payments=total_payments,
            successful_payments=successful_payments,
            failed_payments=failed_payments,
            pending_payments=pending_payments,
            refunded_payments=refunded_payments,
            total_revenue=round(total_revenue, 2),
            net_revenue=round(net_revenue, 2),
            refunded_amount=round(refunded_amount, 2),
            today_revenue=round(float(today_revenue_query), 2),
            this_month_revenue=round(float(this_month_revenue_query), 2),
            this_year_revenue=round(float(this_year_revenue_query), 2),
            stripe_card_payments=stripe_card_payments,
            stripe_bank_payments=stripe_bank_payments,
            stripe_wallet_payments=stripe_wallet_payments,
            crypto_payments=crypto_payments,
            success_rate=round(success_rate, 2),
            refund_rate=round(refund_rate, 2),
            average_transaction_value=round(avg_transaction_value, 2)
        )
    
    def _get_or_create_stripe_customer(self, user: User) -> stripe.Customer:
        """Get or create Stripe customer for user."""
        try:
            # Check if user already has a Stripe customer ID
            if hasattr(user, 'stripe_customer_id') and user.stripe_customer_id:
                return stripe.Customer.retrieve(user.stripe_customer_id)
            
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={
                    'user_id': str(user.id),
                    'internal_user_email': user.email
                }
            )
            
            # Store customer ID (would need to add this field to User model)
            # user.stripe_customer_id = customer.id
            # self.db.commit()
            
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer creation error: {str(e)}"
            )
    
    def get_payment_by_stripe_intent(self, payment_intent_id: str) -> Optional[Payment]:
        """Get payment by Stripe payment intent ID."""
        return self.db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()
    
    def cancel_payment(self, payment_id: int) -> Payment:
        """Cancel a pending payment."""
        payment = self.get_payment_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        if payment.status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending payments can be cancelled"
            )
        
        try:
            # Cancel Stripe payment intent if exists
            if payment.stripe_payment_intent_id:
                stripe.PaymentIntent.cancel(payment.stripe_payment_intent_id)
            
            # Update payment status
            payment.status = PaymentStatus.CANCELLED
            payment.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(payment)
            
            return payment
            
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling Stripe payment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment cancellation error: {str(e)}"
            ) 