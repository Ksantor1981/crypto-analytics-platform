"""
Signal Notification Service - Email notifications for new signals
Part of Task 2.3.1: Premium функции
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.user import User, SubscriptionPlan
from ..models.signal import Signal
from ..models.channel import Channel
from ..services.email_service import email_service
from ..database import get_db

logger = logging.getLogger(__name__)

class SignalNotificationService:
    """
    Service for sending email notifications about new crypto signals
    Premium feature: Email notifications for new signals
    """
    
    def __init__(self):
        self.notification_enabled_plans = [SubscriptionPlan.PREMIUM, SubscriptionPlan.PRO]
    
    async def notify_new_signal(self, signal: Signal, db: Session):
        """
        Send email notification to channel owner about new signal
        Only for Premium/Pro users with email notifications enabled
        """
        try:
            # Get channel and owner
            channel = db.query(Channel).filter(Channel.id == signal.channel_id).first()
            if not channel:
                logger.warning(f"Channel not found for signal {signal.id}")
                return
            
            owner = db.query(User).filter(User.id == channel.owner_id).first()
            if not owner:
                logger.warning(f"Owner not found for channel {channel.id}")
                return
            
            # Check if user has Premium/Pro subscription and email notifications enabled
            if not self._should_send_notification(owner):
                return
            
            # Check notification frequency limits
            if not await self._check_notification_frequency(owner, db):
                logger.info(f"Notification frequency limit reached for user {owner.email}")
                return
            
            # Send email notification
            await self._send_signal_email(owner, signal, channel)
            
            # Log notification
            await self._log_notification(owner, signal, db)
            
            logger.info(f"Signal notification sent to {owner.email} for signal {signal.id}")
            
        except Exception as e:
            logger.error(f"Error sending signal notification: {e}")
    
    async def notify_bulk_signals(self, signals: List[Signal], db: Session):
        """
        Send bulk email notifications for multiple new signals
        Optimized for high-volume signal processing
        """
        try:
            # Group signals by channel owner
            owner_signals = {}
            
            for signal in signals:
                channel = db.query(Channel).filter(Channel.id == signal.channel_id).first()
                if not channel:
                    continue
                
                owner = db.query(User).filter(User.id == channel.owner_id).first()
                if not owner or not self._should_send_notification(owner):
                    continue
                
                if owner.id not in owner_signals:
                    owner_signals[owner.id] = {'user': owner, 'signals': []}
                
                owner_signals[owner.id]['signals'].append({
                    'signal': signal,
                    'channel': channel
                })
            
            # Send bulk notifications
            for owner_id, data in owner_signals.items():
                user = data['user']
                signal_data = data['signals']
                
                # Check frequency limits
                if not await self._check_notification_frequency(user, db):
                    continue
                
                # Send bulk email
                await self._send_bulk_signal_email(user, signal_data)
                
                # Log notifications
                for item in signal_data:
                    await self._log_notification(user, item['signal'], db)
                
                logger.info(f"Bulk signal notification sent to {user.email} for {len(signal_data)} signals")
                
        except Exception as e:
            logger.error(f"Error sending bulk signal notifications: {e}")
    
    def _should_send_notification(self, user: User) -> bool:
        """Check if user should receive signal notifications"""
        # Check subscription plan
        if user.subscription_plan not in self.notification_enabled_plans:
            return False
        
        # Check if user has email notifications enabled
        if not getattr(user, 'email_notifications_enabled', True):
            return False
        
        # Check if user has signal notifications specifically enabled
        if not getattr(user, 'signal_notifications_enabled', True):
            return False
        
        return True
    
    async def _check_notification_frequency(self, user: User, db: Session) -> bool:
        """
        Check if user hasn't exceeded notification frequency limits
        Prevent spam by limiting notifications per hour/day
        """
        try:
            # Get notification limits based on subscription
            if user.subscription_plan == SubscriptionPlan.PREMIUM:
                max_per_hour = 10
                max_per_day = 50
            elif user.subscription_plan == SubscriptionPlan.PRO:
                max_per_hour = 20
                max_per_day = 100
            else:
                return False
            
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            # Count recent notifications (would need a notification log table)
            # For now, we'll implement a simple check
            # In production, you'd want to track this in database
            
            # This is a simplified implementation
            # You might want to add a notification_log table to track this properly
            
            return True  # Allow for now, implement proper tracking later
            
        except Exception as e:
            logger.error(f"Error checking notification frequency: {e}")
            return False
    
    async def _send_signal_email(self, user: User, signal: Signal, channel: Channel):
        """Send individual signal notification email"""
        try:
            # Prepare email data
            email_data = {
                'user_name': user.name or user.email,
                'signal_type': signal.signal_type.upper(),
                'symbol': signal.symbol,
                'entry_price': signal.entry_price,
                'target_price': signal.target_price,
                'stop_loss': signal.stop_loss,
                'confidence': signal.confidence,
                'channel_name': channel.name,
                'channel_type': channel.type,
                'created_at': signal.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'raw_message': signal.raw_message[:200] + '...' if len(signal.raw_message) > 200 else signal.raw_message,
                'dashboard_url': f"{email_service.frontend_url}/dashboard",
                'manage_notifications_url': f"{email_service.frontend_url}/settings/notifications"
            }
            
            # Send email
            await email_service.send_email(
                to_email=user.email,
                subject=f"🚨 New {signal.signal_type.upper()} Signal: {signal.symbol}",
                template_name='signal_notification',
                template_data=email_data
            )
            
        except Exception as e:
            logger.error(f"Error sending signal email: {e}")
            raise
    
    async def _send_bulk_signal_email(self, user: User, signal_data: List[dict]):
        """Send bulk signal notification email"""
        try:
            # Prepare bulk email data
            signals_summary = []
            total_signals = len(signal_data)
            
            for item in signal_data[:5]:  # Show max 5 signals in email
                signal = item['signal']
                channel = item['channel']
                
                signals_summary.append({
                    'symbol': signal.symbol,
                    'signal_type': signal.signal_type.upper(),
                    'entry_price': signal.entry_price,
                    'confidence': signal.confidence,
                    'channel_name': channel.name,
                    'created_at': signal.created_at.strftime('%H:%M')
                })
            
            email_data = {
                'user_name': user.name or user.email,
                'total_signals': total_signals,
                'signals_summary': signals_summary,
                'has_more': total_signals > 5,
                'additional_count': total_signals - 5 if total_signals > 5 else 0,
                'dashboard_url': f"{email_service.frontend_url}/dashboard",
                'manage_notifications_url': f"{email_service.frontend_url}/settings/notifications"
            }
            
            # Send email
            await email_service.send_email(
                to_email=user.email,
                subject=f"📊 {total_signals} New Crypto Signals Available",
                template_name='bulk_signal_notification',
                template_data=email_data
            )
            
        except Exception as e:
            logger.error(f"Error sending bulk signal email: {e}")
            raise
    
    async def _log_notification(self, user: User, signal: Signal, db: Session):
        """Log notification for frequency tracking"""
        try:
            # In a production system, you'd want to create a notification_log table
            # For now, we'll just log to application logs
            logger.info(f"Notification logged: user={user.id}, signal={signal.id}, timestamp={datetime.utcnow()}")
            
            # TODO: Implement proper notification logging in database
            # notification_log = NotificationLog(
            #     user_id=user.id,
            #     signal_id=signal.id,
            #     notification_type='signal_alert',
            #     sent_at=datetime.utcnow()
            # )
            # db.add(notification_log)
            # db.commit()
            
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
    
    async def send_daily_summary(self, user: User, db: Session):
        """
        Send daily summary of signals for Premium/Pro users
        Alternative to real-time notifications
        """
        try:
            if not self._should_send_notification(user):
                return
            
            # Get user's channels
            channels = db.query(Channel).filter(Channel.owner_id == user.id).all()
            if not channels:
                return
            
            # Get signals from last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            channel_ids = [c.id for c in channels]
            
            signals = db.query(Signal).filter(
                and_(
                    Signal.channel_id.in_(channel_ids),
                    Signal.created_at >= yesterday
                )
            ).order_by(Signal.created_at.desc()).all()
            
            if not signals:
                return
            
            # Group signals by type and channel
            summary_data = self._prepare_daily_summary(signals, channels)
            
            # Send summary email
            await self._send_daily_summary_email(user, summary_data)
            
            logger.info(f"Daily summary sent to {user.email} with {len(signals)} signals")
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    def _prepare_daily_summary(self, signals: List[Signal], channels: List[Channel]) -> dict:
        """Prepare daily summary data"""
        # Group signals by channel
        channel_map = {c.id: c for c in channels}
        channel_signals = {}
        
        for signal in signals:
            channel_id = signal.channel_id
            if channel_id not in channel_signals:
                channel_signals[channel_id] = []
            channel_signals[channel_id].append(signal)
        
        # Calculate statistics
        total_signals = len(signals)
        buy_signals = len([s for s in signals if s.signal_type == 'buy'])
        sell_signals = len([s for s in signals if s.signal_type == 'sell'])
        
        # Get top symbols
        symbol_counts = {}
        for signal in signals:
            symbol_counts[signal.symbol] = symbol_counts.get(signal.symbol, 0) + 1
        
        top_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Prepare channel summaries
        channel_summaries = []
        for channel_id, channel_signal_list in channel_signals.items():
            channel = channel_map.get(channel_id)
            if channel:
                channel_summaries.append({
                    'name': channel.name,
                    'type': channel.type,
                    'signal_count': len(channel_signal_list),
                    'latest_signal': channel_signal_list[0] if channel_signal_list else None
                })
        
        return {
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'top_symbols': top_symbols,
            'channel_summaries': channel_summaries,
            'date': datetime.utcnow().strftime('%Y-%m-%d')
        }
    
    async def _send_daily_summary_email(self, user: User, summary_data: dict):
        """Send daily summary email"""
        try:
            email_data = {
                'user_name': user.name or user.email,
                **summary_data,
                'dashboard_url': f"{email_service.frontend_url}/dashboard",
                'manage_notifications_url': f"{email_service.frontend_url}/settings/notifications"
            }
            
            await email_service.send_email(
                to_email=user.email,
                subject=f"📈 Daily Crypto Signals Summary - {summary_data['total_signals']} signals",
                template_name='daily_summary',
                template_data=email_data
            )
            
        except Exception as e:
            logger.error(f"Error sending daily summary email: {e}")
            raise


# Global signal notification service instance
signal_notification_service = SignalNotificationService()
