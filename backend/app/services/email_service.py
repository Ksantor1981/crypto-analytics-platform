"""
Email Service - Email notifications for payments and subscriptions
Part of Task 2.2.4: Email уведомления о платежах
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
from jinja2 import Environment, FileSystemLoader, Template
import os

from ..core.config import settings
from ..models.user import User, SubscriptionPlan
from ..models.subscription import Subscription, Payment

logger = logging.getLogger(__name__)

class EmailService:
    """
    Service for sending email notifications related to payments and subscriptions
    """
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME or "Crypto Analytics"
        
        # Setup Jinja2 for email templates
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "emails")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send email with HTML and optional text content
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text content (optional)
            attachments: List of attachments (optional)
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]) -> None:
        """Add attachment to email message"""
        try:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment['content'])
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment["filename"]}'
            )
            msg.attach(part)
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.get('filename', 'unknown')}: {e}")
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render email template with context"""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return ""
    
    async def send_payment_success_notification(
        self,
        user: User,
        payment: Payment,
        subscription: Subscription
    ) -> bool:
        """
        Send payment success notification
        
        Args:
            user: User who made the payment
            payment: Payment record
            subscription: Associated subscription
        
        Returns:
            bool: True if email sent successfully
        """
        context = {
            'user_name': user.full_name or user.username or user.email.split('@')[0],
            'user_email': user.email,
            'payment_amount': payment.amount,
            'payment_currency': payment.currency,
            'payment_date': payment.created_at.strftime('%B %d, %Y'),
            'subscription_plan': subscription.plan_name,
            'subscription_period_start': subscription.current_period_start.strftime('%B %d, %Y'),
            'subscription_period_end': subscription.current_period_end.strftime('%B %d, %Y'),
            'invoice_url': payment.stripe_invoice_url,
            'manage_subscription_url': f"{settings.FRONTEND_URL}/subscription/manage",
            'support_email': settings.SUPPORT_EMAIL,
            'company_name': "Crypto Analytics"
        }
        
        html_content = self._render_template('payment_success.html', context)
        text_content = self._render_template('payment_success.txt', context)
        
        subject = f"Payment Confirmation - {subscription.plan_name} Subscription"
        
        return await self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_payment_failed_notification(
        self,
        user: User,
        subscription: Subscription,
        error_message: str
    ) -> bool:
        """
        Send payment failed notification
        
        Args:
            user: User whose payment failed
            subscription: Associated subscription
            error_message: Error message from payment processor
        
        Returns:
            bool: True if email sent successfully
        """
        context = {
            'user_name': user.full_name or user.username or user.email.split('@')[0],
            'subscription_plan': subscription.plan_name,
            'error_message': error_message,
            'retry_date': (datetime.utcnow() + timedelta(days=3)).strftime('%B %d, %Y'),
            'update_payment_url': f"{settings.FRONTEND_URL}/subscription/payment-method",
            'support_email': settings.SUPPORT_EMAIL,
            'company_name': "Crypto Analytics"
        }
        
        html_content = self._render_template('payment_failed.html', context)
        text_content = self._render_template('payment_failed.txt', context)
        
        subject = "Payment Failed - Action Required"
        
        return await self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_subscription_renewal_reminder(
        self,
        user: User,
        subscription: Subscription,
        days_until_renewal: int
    ) -> bool:
        """
        Send subscription renewal reminder
        
        Args:
            user: User to notify
            subscription: Subscription that will renew
            days_until_renewal: Number of days until renewal
        
        Returns:
            bool: True if email sent successfully
        """
        context = {
            'user_name': user.full_name or user.username or user.email.split('@')[0],
            'subscription_plan': subscription.plan_name,
            'renewal_date': subscription.current_period_end.strftime('%B %d, %Y'),
            'renewal_amount': subscription.plan_price,
            'days_until_renewal': days_until_renewal,
            'manage_subscription_url': f"{settings.FRONTEND_URL}/subscription/manage",
            'cancel_subscription_url': f"{settings.FRONTEND_URL}/subscription/cancel",
            'support_email': settings.SUPPORT_EMAIL,
            'company_name': "Crypto Analytics"
        }
        
        html_content = self._render_template('subscription_renewal_reminder.html', context)
        text_content = self._render_template('subscription_renewal_reminder.txt', context)
        
        if days_until_renewal <= 3:
            subject = f"Your {subscription.plan_name} subscription renews in {days_until_renewal} day{'s' if days_until_renewal != 1 else ''}"
        else:
            subject = f"Your {subscription.plan_name} subscription renews soon"
        
        return await self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_subscription_cancelled_notification(
        self,
        user: User,
        subscription: Subscription
    ) -> bool:
        """
        Send subscription cancellation notification
        
        Args:
            user: User whose subscription was cancelled
            subscription: Cancelled subscription
        
        Returns:
            bool: True if email sent successfully
        """
        context = {
            'user_name': user.full_name or user.username or user.email.split('@')[0],
            'subscription_plan': subscription.plan_name,
            'cancellation_date': datetime.utcnow().strftime('%B %d, %Y'),
            'access_until_date': subscription.current_period_end.strftime('%B %d, %Y'),
            'reactivate_url': f"{settings.FRONTEND_URL}/subscription/plans",
            'export_data_url': f"{settings.FRONTEND_URL}/export",
            'support_email': settings.SUPPORT_EMAIL,
            'company_name': "Crypto Analytics"
        }
        
        html_content = self._render_template('subscription_cancelled.html', context)
        text_content = self._render_template('subscription_cancelled.txt', context)
        
        subject = f"Subscription Cancelled - {subscription.plan_name}"
        
        return await self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_subscription_expired_notification(
        self,
        user: User,
        subscription: Subscription
    ) -> bool:
        """
        Send subscription expired notification
        
        Args:
            user: User whose subscription expired
            subscription: Expired subscription
        
        Returns:
            bool: True if email sent successfully
        """
        context = {
            'user_name': user.full_name or user.username or user.email.split('@')[0],
            'subscription_plan': subscription.plan_name,
            'expiration_date': subscription.current_period_end.strftime('%B %d, %Y'),
            'free_plan_limits': {
                'channels': 3,
                'api_calls': 100
            },
            'resubscribe_url': f"{settings.FRONTEND_URL}/subscription/plans",
            'support_email': settings.SUPPORT_EMAIL,
            'company_name': "Crypto Analytics"
        }
        
        html_content = self._render_template('subscription_expired.html', context)
        text_content = self._render_template('subscription_expired.txt', context)
        
        subject = f"Subscription Expired - {subscription.plan_name}"
        
        return await self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_welcome_email(self, user: User) -> bool:
        """
        Send welcome email to new user
        
        Args:
            user: New user
        
        Returns:
            bool: True if email sent successfully
        """
        context = {
            'user_name': user.full_name or user.username or user.email.split('@')[0],
            'login_url': f"{settings.FRONTEND_URL}/login",
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
            'channels_url': f"{settings.FRONTEND_URL}/channels",
            'upgrade_url': f"{settings.FRONTEND_URL}/subscription/plans",
            'support_email': settings.SUPPORT_EMAIL,
            'company_name': "Crypto Analytics"
        }
        
        html_content = self._render_template('welcome.html', context)
        text_content = self._render_template('welcome.txt', context)
        
        subject = "Welcome to Crypto Analytics!"
        
        return await self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )


# Global email service instance
email_service = EmailService()


# Background task for sending emails
async def send_email_background(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> None:
    """Background task for sending emails without blocking the main thread"""
    try:
        await email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    except Exception as e:
        logger.error(f"Background email task failed: {e}")


# Scheduled tasks for subscription reminders
async def send_renewal_reminders() -> None:
    """
    Send renewal reminders for subscriptions that will renew soon
    This should be run as a scheduled task (e.g., daily)
    """
    from ..database import get_db
    from sqlalchemy.orm import Session
    
    try:
        db = next(get_db())
        
        # Get subscriptions that will renew in 7, 3, or 1 day(s)
        reminder_days = [7, 3, 1]
        
        for days in reminder_days:
            target_date = datetime.utcnow() + timedelta(days=days)
            
            subscriptions = db.query(Subscription).filter(
                Subscription.status == 'active',
                Subscription.current_period_end.date() == target_date.date()
            ).all()
            
            for subscription in subscriptions:
                if subscription.user:
                    await email_service.send_subscription_renewal_reminder(
                        user=subscription.user,
                        subscription=subscription,
                        days_until_renewal=days
                    )
        
        logger.info(f"Sent renewal reminders for {len(subscriptions)} subscriptions")
        
    except Exception as e:
        logger.error(f"Failed to send renewal reminders: {e}")
    finally:
        db.close()


async def send_expiration_notifications() -> None:
    """
    Send notifications for expired subscriptions
    This should be run as a scheduled task (e.g., daily)
    """
    from ..database import get_db
    from sqlalchemy.orm import Session
    
    try:
        db = next(get_db())
        
        # Get subscriptions that expired yesterday
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        expired_subscriptions = db.query(Subscription).filter(
            Subscription.status == 'expired',
            Subscription.current_period_end.date() == yesterday.date()
        ).all()
        
        for subscription in expired_subscriptions:
            if subscription.user:
                await email_service.send_subscription_expired_notification(
                    user=subscription.user,
                    subscription=subscription
                )
        
        logger.info(f"Sent expiration notifications for {len(expired_subscriptions)} subscriptions")
        
    except Exception as e:
        logger.error(f"Failed to send expiration notifications: {e}")
    finally:
        db.close()
