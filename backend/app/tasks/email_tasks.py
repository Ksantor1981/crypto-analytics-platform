"""
Celery tasks for email notifications
"""
import asyncio
from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.services.payment_service import PaymentService
from app.models.payment import Payment

logger = logging.getLogger(__name__)

# Initialize Celery app (this should be imported from your main Celery config)
celery_app = Celery('crypto_analytics')

@celery_app.task
def send_daily_payment_reminders():
    """Send daily payment reminders for upcoming billing dates"""
    try:
        # Create database session
        db = next(get_db())
        payment_service = PaymentService(db)
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(payment_service.send_payment_reminders())
            logger.info(f"Daily payment reminders sent: {result}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in send_daily_payment_reminders task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task
def send_expired_subscription_notifications():
    """Send notifications for expired subscriptions"""
    try:
        # Create database session
        db = next(get_db())
        payment_service = PaymentService(db)
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(payment_service.send_expired_subscription_notifications())
            logger.info(f"Expired subscription notifications sent: {result}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in send_expired_subscription_notifications task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task
def send_weekly_payment_summary():
    """Send weekly payment summary to admin"""
    try:
        # Create database session
        db = next(get_db())
        payment_service = PaymentService(db)
        
        # Get weekly payment statistics
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        payments = db.query(Payment).filter(
            Payment.created_at >= week_ago
        ).all()
        
        total_payments = len(payments)
        successful_payments = len([p for p in payments if p.status == "SUCCEEDED"])
        total_amount = sum(float(p.amount) for p in payments if p.status == "SUCCEEDED")
        
        logger.info(f"Weekly payment summary: {total_payments} total, {successful_payments} successful, ${total_amount:.2f} total")
        
        return {
            "success": True,
            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "total_amount": total_amount,
            "period": "weekly"
        }
        
    except Exception as e:
        logger.error(f"Error in send_weekly_payment_summary task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close() 