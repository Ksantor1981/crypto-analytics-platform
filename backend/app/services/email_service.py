"""
Email Service for sending payment notifications
Supports both SMTP and SendGrid providers
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import httpx
from jinja2 import Template

from app.core.config import get_settings
from app.models.user import User
from app.models.payment import Payment
from app.models.subscription import Subscription

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.settings = get_settings()
        self.smtp_configured = bool(
            self.settings.EMAIL_SMTP_HOST and 
            self.settings.EMAIL_SMTP_USERNAME and 
            self.settings.EMAIL_SMTP_PASSWORD
        )
        self.sendgrid_configured = bool(self.settings.SENDGRID_API_KEY)
        
        if not self.smtp_configured and not self.sendgrid_configured:
            logger.warning("No email provider configured - email notifications will be disabled")
    
    async def send_payment_confirmation(self, user: User, payment: Payment) -> bool:
        """Send payment confirmation email"""
        try:
            subject = "Payment Confirmed - Crypto Analytics Platform"
            
            # Prepare email data
            email_data = {
                "user_name": user.full_name or user.email,
                "payment_amount": f"${payment.amount:.2f}",
                "payment_currency": payment.currency,
                "payment_date": payment.processed_at.strftime("%B %d, %Y at %H:%M UTC"),
                "payment_id": payment.internal_transaction_id,
                "receipt_url": payment.receipt_url,
                "subscription_plan": self._get_subscription_plan_name(payment),
                "support_email": "support@crypto-analytics.com"
            }
            
            html_content = self._render_payment_confirmation_template(email_data)
            text_content = self._render_payment_confirmation_text(email_data)
            
            return await self._send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending payment confirmation email: {e}")
            return False
    
    async def send_payment_reminder(self, user: User, subscription: Subscription) -> bool:
        """Send payment reminder email"""
        try:
            subject = "Payment Reminder - Crypto Analytics Platform"
            
            email_data = {
                "user_name": user.full_name or user.email,
                "subscription_plan": subscription.plan.value.title(),
                "next_billing_date": subscription.next_billing_date.strftime("%B %d, %Y"),
                "amount": f"${subscription.price:.2f}",
                "currency": subscription.currency,
                "support_email": "support@crypto-analytics.com"
            }
            
            html_content = self._render_payment_reminder_template(email_data)
            text_content = self._render_payment_reminder_text(email_data)
            
            return await self._send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending payment reminder email: {e}")
            return False
    
    async def send_subscription_expired(self, user: User, subscription: Subscription) -> bool:
        """Send subscription expired notification"""
        try:
            subject = "Subscription Expired - Crypto Analytics Platform"
            
            email_data = {
                "user_name": user.full_name or user.email,
                "subscription_plan": subscription.plan.value.title(),
                "expired_date": subscription.current_period_end.strftime("%B %d, %Y"),
                "support_email": "support@crypto-analytics.com"
            }
            
            html_content = self._render_subscription_expired_template(email_data)
            text_content = self._render_subscription_expired_text(email_data)
            
            return await self._send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending subscription expired email: {e}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email using configured provider"""
        if self.sendgrid_configured:
            return await self._send_via_sendgrid(to_email, subject, html_content, text_content)
        elif self.smtp_configured:
            return await self._send_via_smtp(to_email, subject, html_content, text_content)
        else:
            logger.warning("No email provider configured - skipping email send")
            return False
    
    async def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email via SendGrid API"""
        try:
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.settings.SENDGRID_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}],
                        "subject": subject
                    }
                ],
                "from": {
                    "email": self.settings.SENDGRID_FROM_EMAIL,
                    "name": self.settings.SENDGRID_FROM_NAME
                },
                "content": [
                    {
                        "type": "text/html",
                        "value": html_content
                    },
                    {
                        "type": "text/plain",
                        "value": text_content
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                
                if response.status_code == 202:
                    logger.info(f"Email sent successfully via SendGrid to {to_email}")
                    return True
                else:
                    logger.error(f"SendGrid API error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending email via SendGrid: {e}")
            return False
    
    async def _send_via_smtp(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email via SMTP"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.settings.EMAIL_FROM_NAME} <{self.settings.EMAIL_FROM_ADDRESS}>"
            message["To"] = to_email
            
            # Attach both HTML and text versions
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Create SMTP connection
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.settings.EMAIL_SMTP_HOST, self.settings.EMAIL_SMTP_PORT) as server:
                if self.settings.EMAIL_USE_TLS:
                    server.starttls(context=context)
                elif self.settings.EMAIL_USE_SSL:
                    server = smtplib.SMTP_SSL(self.settings.EMAIL_SMTP_HOST, self.settings.EMAIL_SMTP_PORT, context=context)
                
                server.login(self.settings.EMAIL_SMTP_USERNAME, self.settings.EMAIL_SMTP_PASSWORD)
                server.send_message(message)
                
            logger.info(f"Email sent successfully via SMTP to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email via SMTP: {e}")
            return False
    
    def _get_subscription_plan_name(self, payment: Payment) -> str:
        """Get subscription plan name from payment"""
        if payment.stripe_subscription_id:
            # In a real implementation, you'd fetch this from Stripe
            return "Premium Plan"
        return "Unknown Plan"
    
    def _render_payment_confirmation_template(self, data: Dict[str, Any]) -> str:
        """Render payment confirmation HTML template"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Payment Confirmed</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #2563eb; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9fafb; }
                .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }
                .button { display: inline-block; padding: 12px 24px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Payment Confirmed</h1>
                </div>
                <div class="content">
                    <h2>Hello {{ user_name }},</h2>
                    <p>Thank you for your payment! Your transaction has been successfully processed.</p>
                    
                    <h3>Payment Details:</h3>
                    <ul>
                        <li><strong>Amount:</strong> {{ payment_amount }} {{ payment_currency }}</li>
                        <li><strong>Date:</strong> {{ payment_date }}</li>
                        <li><strong>Transaction ID:</strong> {{ payment_id }}</li>
                        <li><strong>Plan:</strong> {{ subscription_plan }}</li>
                    </ul>
                    
                    {% if receipt_url %}
                    <p><a href="{{ receipt_url }}" class="button">View Receipt</a></p>
                    {% endif %}
                    
                    <p>Your subscription is now active. You can access all premium features immediately.</p>
                    
                    <p>If you have any questions, please contact us at <a href="mailto:{{ support_email }}">{{ support_email }}</a>.</p>
                </div>
                <div class="footer">
                    <p>Crypto Analytics Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        return Template(template).render(**data)
    
    def _render_payment_confirmation_text(self, data: Dict[str, Any]) -> str:
        """Render payment confirmation text template"""
        template = """
Payment Confirmed - Crypto Analytics Platform

Hello {{ user_name }},

Thank you for your payment! Your transaction has been successfully processed.

Payment Details:
- Amount: {{ payment_amount }} {{ payment_currency }}
- Date: {{ payment_date }}
- Transaction ID: {{ payment_id }}
- Plan: {{ subscription_plan }}

Your subscription is now active. You can access all premium features immediately.

If you have any questions, please contact us at {{ support_email }}.

Best regards,
Crypto Analytics Platform Team
        """
        return Template(template).render(**data)
    
    def _render_payment_reminder_template(self, data: Dict[str, Any]) -> str:
        """Render payment reminder HTML template"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Payment Reminder</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #f59e0b; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9fafb; }
                .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }
                .button { display: inline-block; padding: 12px 24px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Payment Reminder</h1>
                </div>
                <div class="content">
                    <h2>Hello {{ user_name }},</h2>
                    <p>This is a friendly reminder that your subscription payment is due soon.</p>
                    
                    <h3>Subscription Details:</h3>
                    <ul>
                        <li><strong>Plan:</strong> {{ subscription_plan }}</li>
                        <li><strong>Next Billing Date:</strong> {{ next_billing_date }}</li>
                        <li><strong>Amount:</strong> {{ amount }} {{ currency }}</li>
                    </ul>
                    
                    <p>To ensure uninterrupted access to your premium features, please make sure your payment method is up to date.</p>
                    
                    <p>If you have any questions, please contact us at <a href="mailto:{{ support_email }}">{{ support_email }}</a>.</p>
                </div>
                <div class="footer">
                    <p>Crypto Analytics Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        return Template(template).render(**data)
    
    def _render_payment_reminder_text(self, data: Dict[str, Any]) -> str:
        """Render payment reminder text template"""
        template = """
Payment Reminder - Crypto Analytics Platform

Hello {{ user_name }},

This is a friendly reminder that your subscription payment is due soon.

Subscription Details:
- Plan: {{ subscription_plan }}
- Next Billing Date: {{ next_billing_date }}
- Amount: {{ amount }} {{ currency }}

To ensure uninterrupted access to your premium features, please make sure your payment method is up to date.

If you have any questions, please contact us at {{ support_email }}.

Best regards,
Crypto Analytics Platform Team
        """
        return Template(template).render(**data)
    
    def _render_subscription_expired_template(self, data: Dict[str, Any]) -> str:
        """Render subscription expired HTML template"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Subscription Expired</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #dc2626; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9fafb; }
                .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }
                .button { display: inline-block; padding: 12px 24px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Subscription Expired</h1>
                </div>
                <div class="content">
                    <h2>Hello {{ user_name }},</h2>
                    <p>Your subscription has expired. You've been downgraded to the free plan.</p>
                    
                    <h3>Subscription Details:</h3>
                    <ul>
                        <li><strong>Plan:</strong> {{ subscription_plan }}</li>
                        <li><strong>Expired Date:</strong> {{ expired_date }}</li>
                    </ul>
                    
                    <p>To restore access to premium features, please renew your subscription.</p>
                    
                    <p>If you have any questions, please contact us at <a href="mailto:{{ support_email }}">{{ support_email }}</a>.</p>
                </div>
                <div class="footer">
                    <p>Crypto Analytics Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        return Template(template).render(**data)
    
    def _render_subscription_expired_text(self, data: Dict[str, Any]) -> str:
        """Render subscription expired text template"""
        template = """
Subscription Expired - Crypto Analytics Platform

Hello {{ user_name }},

Your subscription has expired. You've been downgraded to the free plan.

Subscription Details:
- Plan: {{ subscription_plan }}
- Expired Date: {{ expired_date }}

To restore access to premium features, please renew your subscription.

If you have any questions, please contact us at {{ support_email }}.

Best regards,
Crypto Analytics Platform Team
        """
        return Template(template).render(**data)
