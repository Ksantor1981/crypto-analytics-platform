from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal

# Enums matching the model
class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"

class PaymentMethod(str, Enum):
    STRIPE_CARD = "STRIPE_CARD"
    STRIPE_BANK = "STRIPE_BANK"
    STRIPE_WALLET = "STRIPE_WALLET"
    CRYPTO = "CRYPTO"
    OTHER = "OTHER"

# Base schema for common fields
class PaymentBase(BaseModel):
    amount: float = Field(..., description="Payment amount", gt=0)
    currency: str = Field(default="USD", description="Currency code")
    description: Optional[str] = Field(None, description="Payment description")
    payment_method: PaymentMethod = Field(..., description="Payment method")

# Schema for creating payment
class PaymentCreate(PaymentBase):
    user_id: int = Field(..., description="User ID")
    stripe_payment_intent_id: Optional[str] = Field(None, description="Stripe payment intent ID")
    billing_name: Optional[str] = Field(None, description="Billing name")
    billing_email: Optional[str] = Field(None, description="Billing email")
    billing_address: Optional[Dict[str, Any]] = Field(None, description="Billing address")
    payment_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional payment metadata")

# Schema for updating payment
class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = Field(None, description="Payment status")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    failed_at: Optional[datetime] = Field(None, description="Failure timestamp")
    failure_reason: Optional[str] = Field(None, description="Failure reason")
    failure_code: Optional[str] = Field(None, description="Failure code")
    receipt_url: Optional[str] = Field(None, description="Receipt URL")
    invoice_pdf_url: Optional[str] = Field(None, description="Invoice PDF URL")
    payment_metadata: Optional[Dict[str, Any]] = Field(None, description="Payment metadata")
    notes: Optional[str] = Field(None, description="Internal notes")

# Schema for payment response
class PaymentResponse(PaymentBase):
    id: int
    user_id: int
    status: PaymentStatus
    
    # Stripe integration
    stripe_payment_intent_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    
    # Transaction details
    processed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    failure_code: Optional[str] = None
    
    # Refund information
    refunded_at: Optional[datetime] = None
    refund_amount: Optional[float] = None
    refund_reason: Optional[str] = None
    stripe_refund_id: Optional[str] = None
    
    # Additional metadata
    payment_metadata: Optional[Dict[str, Any]] = None
    receipt_url: Optional[str] = None
    invoice_pdf_url: Optional[str] = None
    
    # Billing details
    billing_name: Optional[str] = None
    billing_email: Optional[str] = None
    billing_address: Optional[Dict[str, Any]] = None
    
    # Internal tracking
    internal_transaction_id: Optional[str] = None
    notes: Optional[str] = None
    
    # Computed properties
    is_successful: bool = False
    is_refundable: bool = False
    net_amount: float = 0.0
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Schema for database representation
class PaymentInDB(PaymentResponse):
    pass

# Schema with user info
class PaymentWithUser(PaymentResponse):
    user_email: Optional[str] = None
    user_name: Optional[str] = None

# Schema for payment intent creation (Stripe)
class PaymentIntentCreate(BaseModel):
    amount: float = Field(..., description="Payment amount", gt=0)
    currency: str = Field(default="USD", description="Currency code")
    description: Optional[str] = Field(None, description="Payment description")
    subscription_id: Optional[int] = Field(None, description="Associated subscription ID")
    automatic_payment_methods: bool = Field(default=True, description="Enable automatic payment methods")
    
    # Customer details
    customer_email: Optional[str] = Field(None, description="Customer email")
    customer_name: Optional[str] = Field(None, description="Customer name")
    
    # Billing details
    billing_address: Optional[Dict[str, Any]] = Field(None, description="Billing address")
    
    # Return URLs
    return_url: Optional[str] = Field(None, description="Return URL after payment")
    cancel_url: Optional[str] = Field(None, description="Cancel URL")

# Schema for payment intent response
class PaymentIntentResponse(BaseModel):
    client_secret: str = Field(..., description="Stripe client secret")
    payment_intent_id: str = Field(..., description="Stripe payment intent ID")
    amount: float = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Payment intent status")
    
    # URLs for redirect
    next_action: Optional[Dict[str, Any]] = Field(None, description="Next action required")
    return_url: Optional[str] = Field(None, description="Return URL")

# Schema for refund request
class RefundRequest(BaseModel):
    amount: Optional[float] = Field(None, description="Refund amount (full refund if not specified)")
    reason: Optional[str] = Field(None, description="Refund reason")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional refund metadata")

# Schema for refund response
class RefundResponse(BaseModel):
    refund_id: str = Field(..., description="Stripe refund ID")
    amount: float = Field(..., description="Refunded amount")
    status: str = Field(..., description="Refund status")
    reason: Optional[str] = Field(None, description="Refund reason")
    created_at: datetime = Field(..., description="Refund creation time")

# Schema for payment statistics
class PaymentStats(BaseModel):
    total_payments: int = 0
    successful_payments: int = 0
    failed_payments: int = 0
    pending_payments: int = 0
    refunded_payments: int = 0
    
    # Revenue stats
    total_revenue: float = 0.0
    net_revenue: float = 0.0
    refunded_amount: float = 0.0
    
    # Time-based stats
    today_revenue: float = 0.0
    this_month_revenue: float = 0.0
    this_year_revenue: float = 0.0
    
    # Method breakdown
    stripe_card_payments: int = 0
    stripe_bank_payments: int = 0
    stripe_wallet_payments: int = 0
    crypto_payments: int = 0
    
    # Success rates
    success_rate: float = 0.0
    refund_rate: float = 0.0
    
    # Average transaction value
    average_transaction_value: float = 0.0

# Schema for payment analytics
class PaymentAnalytics(BaseModel):
    period: str = Field(..., description="Analytics period (daily, weekly, monthly)")
    revenue_trend: List[Dict[str, Any]] = Field(default_factory=list, description="Revenue trend data")
    payment_method_distribution: Dict[str, int] = Field(default_factory=dict, description="Payment method distribution")
    top_customers: List[Dict[str, Any]] = Field(default_factory=list, description="Top customers by revenue")
    failed_payments_reasons: Dict[str, int] = Field(default_factory=dict, description="Failed payment reasons")

# Schema for paginated payment list
class PaymentListResponse(BaseModel):
    payments: List[PaymentWithUser]
    total: int
    page: int
    size: int
    pages: int

# Schema for webhook data
class StripeWebhookPayment(BaseModel):
    event_type: str = Field(..., description="Stripe event type")
    payment_intent_id: str = Field(..., description="Payment intent ID")
    amount: float = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Payment status")
    customer_id: Optional[str] = Field(None, description="Stripe customer ID")
    subscription_id: Optional[str] = Field(None, description="Stripe subscription ID")
    invoice_id: Optional[str] = Field(None, description="Stripe invoice ID")
    failure_code: Optional[str] = Field(None, description="Failure code")
    failure_message: Optional[str] = Field(None, description="Failure message")
    receipt_url: Optional[str] = Field(None, description="Receipt URL")
    created_at: datetime = Field(..., description="Event creation time")

# Schema for customer creation
class CustomerCreate(BaseModel):
    email: str = Field(..., description="Customer email")
    name: Optional[str] = Field(None, description="Customer name")
    phone: Optional[str] = Field(None, description="Customer phone")
    address: Optional[Dict[str, Any]] = Field(None, description="Customer address")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Customer metadata")

# Schema for customer response
class CustomerResponse(BaseModel):
    customer_id: str = Field(..., description="Stripe customer ID")
    email: str = Field(..., description="Customer email")
    name: Optional[str] = Field(None, description="Customer name")
    created_at: datetime = Field(..., description="Customer creation time")
    
    # Payment methods
    default_payment_method: Optional[str] = Field(None, description="Default payment method ID")
    payment_methods: List[Dict[str, Any]] = Field(default_factory=list, description="Available payment methods")

# Schema for invoice creation
class InvoiceCreate(BaseModel):
    customer_id: str = Field(..., description="Stripe customer ID")
    subscription_id: Optional[str] = Field(None, description="Stripe subscription ID")
    amount: float = Field(..., description="Invoice amount")
    currency: str = Field(default="USD", description="Currency code")
    description: Optional[str] = Field(None, description="Invoice description")
    due_date: Optional[datetime] = Field(None, description="Invoice due date")
    auto_advance: bool = Field(default=True, description="Auto-advance invoice")

# Schema for invoice response
class InvoiceResponse(BaseModel):
    invoice_id: str = Field(..., description="Stripe invoice ID")
    customer_id: str = Field(..., description="Stripe customer ID")
    amount: float = Field(..., description="Invoice amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Invoice status")
    invoice_pdf: Optional[str] = Field(None, description="Invoice PDF URL")
    hosted_invoice_url: Optional[str] = Field(None, description="Hosted invoice URL")
    created_at: datetime = Field(..., description="Invoice creation time")
    due_date: Optional[datetime] = Field(None, description="Invoice due date") 