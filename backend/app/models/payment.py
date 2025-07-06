from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey, Numeric, Text, JSON
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from decimal import Decimal

from .base import BaseModel

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"

class PaymentMethod(str, enum.Enum):
    STRIPE_CARD = "STRIPE_CARD"
    STRIPE_BANK = "STRIPE_BANK"
    STRIPE_WALLET = "STRIPE_WALLET"
    CRYPTO = "CRYPTO"  # Future implementation
    OTHER = "OTHER"

class Payment(BaseModel):
    """
    Model representing payment transactions
    """
    __tablename__ = "payments"
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="payments")
    
    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    description = Column(String(500), nullable=True)
    
    # Status and method
    status = Column(Enum(PaymentStatus), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    # Stripe integration
    stripe_payment_intent_id = Column(String(255), nullable=True, unique=True)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_invoice_id = Column(String(255), nullable=True)
    
    # Transaction details
    processed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(String(500), nullable=True)
    failure_code = Column(String(50), nullable=True)
    
    # Refund information
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    refund_amount = Column(Numeric(10, 2), nullable=True)
    refund_reason = Column(String(500), nullable=True)
    stripe_refund_id = Column(String(255), nullable=True)
    
    # Additional metadata
    payment_metadata = Column(JSON, nullable=True)  # Store additional Stripe/payment data
    receipt_url = Column(String(500), nullable=True)
    invoice_pdf_url = Column(String(500), nullable=True)
    
    # Billing details
    billing_name = Column(String(255), nullable=True)
    billing_email = Column(String(255), nullable=True)
    billing_address = Column(JSON, nullable=True)  # Store address as JSON
    
    # Internal tracking
    internal_transaction_id = Column(String(100), nullable=True, unique=True)
    notes = Column(Text, nullable=True)
    
    @property
    def is_successful(self) -> bool:
        """Check if payment was successful"""
        return self.status == PaymentStatus.SUCCEEDED
    
    @property
    def is_refundable(self) -> bool:
        """Check if payment can be refunded"""
        return (
            self.status == PaymentStatus.SUCCEEDED 
            and self.refunded_at is None
        )
    
    @property
    def net_amount(self) -> Decimal:
        """Get net amount after refunds"""
        if self.refund_amount:
            return self.amount - self.refund_amount
        return self.amount
    
    def __repr__(self):
        return f"<Payment {self.amount} {self.currency} - {self.status}>" 