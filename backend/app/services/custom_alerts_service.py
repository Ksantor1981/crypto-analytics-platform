"""
Custom Alerts and Webhook Service - Pro feature
Part of Task 2.3.2: Pro функции
"""
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.user import User, SubscriptionPlan
from ..models.signal import Signal
from ..middleware.rbac_middleware import check_subscription_limit

logger = logging.getLogger(__name__)

class CustomAlertsService:
    """
    Service for custom alerts and webhook notifications
    Pro feature: Custom alerts and webhook notifications
    """
    
    def __init__(self):
        self.max_alerts_per_user = {
            SubscriptionPlan.FREE: 0,
            SubscriptionPlan.PREMIUM: 0,
            SubscriptionPlan.PRO: 20  # Up to 20 custom alerts
        }
        self.alert_types = [
            'price_threshold',
            'signal_confidence',
            'volume_spike',
            'trend_change',
            'portfolio_change'
        ]
    
    async def create_custom_alert(
        self,
        user: User,
        db: Session,
        alert_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a custom alert for Pro user
        
        Args:
            user: User creating the alert
            db: Database session
            alert_config: Alert configuration
        
        Returns:
            Dict with alert details
        """
        # Check if user has Pro subscription
        await check_subscription_limit(user, feature='custom_alerts', api_call=False)
        
        if user.subscription_plan != SubscriptionPlan.PRO:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Custom alerts are only available for Pro subscribers"
            )
        
        # Validate alert configuration
        self._validate_alert_config(alert_config)
        
        # Create database alert record
        db_alert = CustomAlert(
            user_id=user.id,
            alert_type=alert_config.get('type'),
            conditions=alert_config.get('conditions'),
            notification_methods=alert_config.get('actions'),
            webhook_url=alert_config.get('webhook_url'),
            is_active=True,
            created_at=datetime.utcnow(),
            triggered_count=0
        )
        
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        
        alert_id = str(db_alert.id)
        
        logger.info(f"Custom alert created for user {user.email}: {alert_config.get('name')}")
        
        return {
            'success': True,
            'message': 'Custom alert created successfully',
            'data': {
                'id': alert_id,
                'user_id': user.id,
                'name': alert_config.get('name'),
                'type': alert_config.get('type'),
                'conditions': alert_config.get('conditions'),
                'actions': alert_config.get('actions'),
                'is_active': True,
                'created_at': datetime.utcnow().isoformat(),
                'triggered_count': 0
            }
        }
    
    async def trigger_alert_check(
        self,
        signal: Signal,
        db: Session
    ):
        """
        Check if any custom alerts should be triggered by this signal
        Called when new signals are processed
        """
        try:
            # Get user who owns the channel
            from ..models.channel import Channel
            channel = db.query(Channel).filter(Channel.id == signal.channel_id).first()
            if not channel:
                return
            
            user = db.query(User).filter(User.id == channel.owner_id).first()
            if not user or user.subscription_plan != SubscriptionPlan.PRO:
                return
            
            # Get user's custom alerts from database
            db_alerts = db.query(CustomAlert).filter(
                CustomAlert.user_id == user.id,
                CustomAlert.is_active == True
            ).all()
            
            user_alerts = []
            for db_alert in db_alerts:
                user_alerts.append({
                    'id': str(db_alert.id),
                    'name': db_alert.name,
                    'type': db_alert.alert_type,
                    'conditions': db_alert.conditions,
                    'actions': db_alert.notification_methods,
                    'is_active': db_alert.is_active,
                    'created_at': db_alert.created_at.isoformat(),
                    'triggered_count': db_alert.triggered_count
                })
            
            # Check each alert
            for alert in user_alerts:
                if await self._should_trigger_alert(alert, signal):
                    await self._execute_alert_actions(alert, signal, user)
            
        except Exception as e:
            logger.error(f"Error checking custom alerts: {e}")
    
    async def send_webhook_notification(
        self,
        webhook_url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send webhook notification
        """
        try:
            default_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'CryptoAnalyticsPlatform/1.0'
            }
            
            if headers:
                default_headers.update(headers)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=default_headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook sent successfully to {webhook_url}")
                        return True
                    else:
                        logger.warning(f"Webhook failed with status {response.status}: {webhook_url}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending webhook to {webhook_url}: {e}")
            return False
    
    async def get_user_alerts(self, user: User, db: Session) -> List[Dict[str, Any]]:
        """Get all custom alerts for user"""
        await check_subscription_limit(user, feature='custom_alerts', api_call=False)
        
        # Get user's alerts from database
        db_alerts = db.query(CustomAlert).filter(
            CustomAlert.user_id == user.id,
            CustomAlert.is_active == True
        ).all()
        
        alerts = []
        for db_alert in db_alerts:
            alerts.append({
                "id": str(db_alert.id),
                "alert_type": db_alert.alert_type,
                "conditions": db_alert.conditions,
                "notification_methods": db_alert.notification_methods,
                "webhook_url": db_alert.webhook_url,
                "is_active": db_alert.is_active,
                "created_at": db_alert.created_at.isoformat(),
                "triggered_count": db_alert.triggered_count
            })
        
        return alerts
    
    async def update_alert(
        self,
        user: User,
        db: Session,
        alert_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update custom alert"""
        await check_subscription_limit(user, feature='custom_alerts', api_call=False)
        
        # Update alert in database
        db_alert = db.query(CustomAlert).filter(
            CustomAlert.id == alert_id,
            CustomAlert.user_id == user.id
        ).first()
        
        if not db_alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Update fields
        update_data_dict = update_data
        for field, value in update_data_dict.items():
            setattr(db_alert, field, value)
        
        db_alert.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_alert)
        
        return {
            "id": str(db_alert.id),
            "alert_type": db_alert.alert_type,
            "conditions": db_alert.conditions,
            "notification_methods": db_alert.notification_methods,
            "webhook_url": db_alert.webhook_url,
            "is_active": db_alert.is_active,
            "created_at": db_alert.created_at.isoformat(),
            "updated_at": db_alert.updated_at.isoformat(),
            "triggered_count": db_alert.triggered_count
        }
    
    async def delete_alert(self, user: User, db: Session, alert_id: str) -> bool:
        """Delete custom alert"""
        await check_subscription_limit(user, feature='custom_alerts', api_call=False)
        
        # Delete from database
        db_alert = db.query(CustomAlert).filter(
            CustomAlert.id == alert_id,
            CustomAlert.user_id == user.id
        ).first()
        
        if not db_alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        db.delete(db_alert)
        db.commit()
        
        logger.info(f"Alert {alert_id} deleted for user {user.email}")
        return True
    
    def _validate_alert_config(self, config: Dict[str, Any]):
        """Validate alert configuration"""
        required_fields = ['name', 'type', 'conditions', 'actions']
        
        for field in required_fields:
            if field not in config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        if config['type'] not in self.alert_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid alert type. Supported types: {', '.join(self.alert_types)}"
            )
        
        # Validate conditions based on alert type
        conditions = config['conditions']
        alert_type = config['type']
        
        if alert_type == 'price_threshold':
            if 'symbol' not in conditions or 'threshold_price' not in conditions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Price threshold alerts require 'symbol' and 'threshold_price'"
                )
        
        elif alert_type == 'signal_confidence':
            if 'confidence_threshold' not in conditions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Signal confidence alerts require 'confidence_threshold'"
                )
        
        # Validate actions
        actions = config['actions']
        if not isinstance(actions, dict) or not actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Actions must be a non-empty dictionary"
            )
    
    async def _should_trigger_alert(self, alert: Dict[str, Any], signal: Signal) -> bool:
        """Check if alert should be triggered by this signal"""
        conditions = alert['conditions']
        alert_type = alert['type']
        
        if alert_type == 'signal_confidence':
            # Check if signal meets confidence threshold
            if 'confidence_threshold' in conditions:
                if signal.confidence < conditions['confidence_threshold']:
                    return False
            
            # Check symbol if specified
            if 'symbol' in conditions:
                if signal.symbol != conditions['symbol']:
                    return False
            
            # Check signal type if specified
            if 'signal_type' in conditions:
                if signal.signal_type != conditions['signal_type']:
                    return False
            
            return True
        
        elif alert_type == 'price_threshold':
            # Check if price crosses threshold
            if 'symbol' in conditions and 'threshold_price' in conditions:
                if signal.symbol == conditions['symbol']:
                    threshold = conditions['threshold_price']
                    direction = conditions.get('direction', 'above')
                    
                    if direction == 'above' and signal.entry_price >= threshold:
                        return True
                    elif direction == 'below' and signal.entry_price <= threshold:
                        return True
        
        return False
    
    async def _execute_alert_actions(
        self,
        alert: Dict[str, Any],
        signal: Signal,
        user: User
    ):
        """Execute alert actions (webhook, email, etc.)"""
        actions = alert['actions']
        
        # Prepare alert payload
        payload = {
            'alert_id': alert['id'],
            'alert_name': alert['name'],
            'alert_type': alert['type'],
            'triggered_at': datetime.utcnow().isoformat(),
            'signal': {
                'id': signal.id,
                'symbol': signal.symbol,
                'signal_type': signal.signal_type,
                'entry_price': signal.entry_price,
                'target_price': signal.target_price,
                'stop_loss': signal.stop_loss,
                'confidence': signal.confidence,
                'created_at': signal.created_at.isoformat()
            },
            'user': {
                'id': user.id,
                'email': user.email
            }
        }
        
        # Send webhook if configured
        if 'webhook_url' in actions:
            await self.send_webhook_notification(
                webhook_url=actions['webhook_url'],
                payload=payload
            )
        
        # Send email notification if configured
        if actions.get('email_notification', False):
            await self._send_alert_email(user, alert, signal, payload)
        
        # Update alert trigger count in database
        try:
            db_alert = db.query(CustomAlert).filter(CustomAlert.id == alert['id']).first()
            if db_alert:
                db_alert.triggered_count += 1
                db_alert.last_triggered_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Error updating alert trigger count: {e}")
        
        logger.info(f"Alert {alert['id']} triggered for user {user.id}")
    
    async def _send_alert_email(
        self,
        user: User,
        alert: Dict[str, Any],
        signal: Signal,
        payload: Dict[str, Any]
    ):
        """Send email notification for triggered alert"""
        try:
            from ..services.email_service import email_service
            
            email_data = {
                'user_name': user.name or user.email,
                'alert_name': alert['name'],
                'alert_type': alert['type'],
                'signal_symbol': signal.symbol,
                'signal_type': signal.signal_type.upper(),
                'entry_price': signal.entry_price,
                'confidence': signal.confidence,
                'triggered_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'dashboard_url': f"{email_service.frontend_url}/dashboard",
                'manage_alerts_url': f"{email_service.frontend_url}/settings/alerts"
            }
            
            await email_service.send_email(
                to_email=user.email,
                subject=f"🚨 Custom Alert Triggered: {alert['name']}",
                template_name='custom_alert_notification',
                template_data=email_data
            )
            
        except Exception as e:
            logger.error(f"Error sending alert email: {e}")
    
    def get_alert_templates(self) -> Dict[str, Any]:
        """Get predefined alert templates for users"""
        return {
            'templates': {
                'high_confidence_signals': {
                    'name': 'High Confidence Signals',
                    'type': 'signal_confidence',
                    'description': 'Alert when signals have high confidence (>80%)',
                    'conditions': {
                        'confidence_threshold': 0.8
                    },
                    'actions': {
                        'email_notification': True
                    }
                },
                'btc_price_alert': {
                    'name': 'BTC Price Alert',
                    'type': 'price_threshold',
                    'description': 'Alert when BTC price crosses a threshold',
                    'conditions': {
                        'symbol': 'BTC',
                        'threshold_price': 50000,
                        'direction': 'above'
                    },
                    'actions': {
                        'email_notification': True
                    }
                },
                'portfolio_change': {
                    'name': 'Portfolio Change Alert',
                    'type': 'portfolio_change',
                    'description': 'Alert on significant portfolio changes',
                    'conditions': {
                        'change_threshold': 0.05  # 5% change
                    },
                    'actions': {
                        'email_notification': True
                    }
                }
            },
            'supported_actions': [
                'email_notification',
                'webhook_url',
                'sms_notification',  # Future feature
                'push_notification'  # Future feature
            ]
        }


# Global custom alerts service instance
custom_alerts_service = CustomAlertsService()
