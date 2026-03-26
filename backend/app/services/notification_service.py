"""
Notification Service
Handles user notifications for new signals and other events.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.signal import Signal
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications to users."""

    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()

    async def notify_users_of_new_signal(self, signal: Signal):
        """Notify all users who have notifications enabled about a new signal."""
        try:
            # Get users with notifications enabled
            subscribed_users = self.db.query(User).filter(
                User.is_active == True,
                User.is_verified == True,
                User.role.in_(['PREMIUM_USER', 'PRO_USER', 'ADMIN'])
            ).all()

            notifications_sent = 0
            for user in subscribed_users:
                try:
                    await self._send_signal_notification(user, signal)
                    notifications_sent += 1
                except Exception as e:
                    logger.error(f"Failed to notify user {user.id}: {e}")

            logger.info(f"Sent {notifications_sent} notifications for signal {signal.id}")

        except Exception as e:
            logger.error(f"Error in notify_users_of_new_signal: {e}")

    async def _send_signal_notification(self, user: User, signal: Signal):
        """Send notification about new signal to a user."""
        subject = f"Новый сигнал: {signal.asset} {signal.direction}"

        email_data = {
            "user_name": user.full_name or user.email.split("@")[0],
            "signal_asset": signal.asset,
            "signal_direction": signal.direction,
            "signal_entry": f"${signal.entry_price:.2f}" if signal.entry_price else "N/A",
            "signal_tp": f"${signal.tp1_price:.2f}" if signal.tp1_price else "N/A",
            "signal_sl": f"${signal.stop_loss:.2f}" if signal.stop_loss else "N/A",
            "channel_name": signal.channel.name if signal.channel else "Unknown",
            "dashboard_url": "https://crypto-analytics.com/dashboard/signals",
        }

        html_content = self._render_signal_notification_template(email_data)
        text_content = self._render_signal_notification_text(email_data)

        await self.email_service._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

    def _render_signal_notification_template(self, data: dict) -> str:
        """Render HTML template for signal notification."""
        template = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Новый сигнал</title>
<style>body{font-family:Arial,sans-serif;line-height:1.6;color:#333;}
.container{max-width:600px;margin:0 auto;padding:20px;}
.header{background:#10b981;color:white;padding:20px;text-align:center;}
.content{padding:20px;background:#f9fafb;}
.signal-box{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:15px;margin:15px 0;}
.button{display:inline-block;padding:12px 24px;background:#2563eb;color:white;text-decoration:none;border-radius:6px;}
.footer{text-align:center;padding:20px;color:#6b7280;font-size:14px;}
</style></head><body>
<div class="container">
<div class="header"><h1>🚀 Новый сигнал</h1></div>
<div class="content">
<h2>Привет, {{ user_name }}!</h2>
<p>Поступил новый торговый сигнал:</p>
<div class="signal-box">
<h3>{{ signal_asset }} {{ signal_direction }}</h3>
<p><strong>Вход:</strong> {{ signal_entry }}</p>
<p><strong>Take Profit:</strong> {{ signal_tp }}</p>
<p><strong>Stop Loss:</strong> {{ signal_sl }}</p>
<p><strong>Источник:</strong> {{ channel_name }}</p>
</div>
<p><a href="{{ dashboard_url }}" class="button">Посмотреть в дашборде</a></p>
</div><div class="footer"><p>Crypto Analytics Platform</p></div>
</div></body></html>
"""
        from jinja2 import Template
        return Template(template).render(**data)

    def _render_signal_notification_text(self, data: dict) -> str:
        """Render text template for signal notification."""
        return f"""Новый сигнал

Привет, {data['user_name']}!

Поступил новый торговый сигнал:
{data['signal_asset']} {data['signal_direction']}
Вход: {data['signal_entry']}
Take Profit: {data['signal_tp']}
Stop Loss: {data['signal_sl']}
Источник: {data['channel_name']}

Посмотреть: {data['dashboard_url']}

Crypto Analytics Platform"""
