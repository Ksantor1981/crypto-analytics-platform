"""
Custom Alerts and Webhook Service - Pro feature
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import aiohttp
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.user import User, SubscriptionPlan
from ..models.signal import Signal
from ..models.custom_alert import CustomAlert, AlertStatus
from ..middleware.rbac_middleware import check_subscription_limit

logger = logging.getLogger(__name__)


def _signal_confidence_normalized(signal: Signal) -> float:
    if signal.ml_success_probability is not None:
        return float(signal.ml_success_probability)
    if signal.confidence_score is not None:
        return float(signal.confidence_score) / 100.0
    return 0.5


def _signal_direction_str(signal: Signal) -> str:
    d = signal.direction
    return (d.value if hasattr(d, "value") else str(d)).lower()


def _stored_conditions(row: CustomAlert) -> Dict[str, Any]:
    if row.conditions is not None:
        return row.conditions
    c = row.condition
    if isinstance(c, dict) and "conditions" in c:
        return c["conditions"] or {}
    return c if isinstance(c, dict) else {}


def _stored_actions(row: CustomAlert) -> Dict[str, Any]:
    if row.notification_methods is not None:
        return row.notification_methods
    c = row.condition
    if isinstance(c, dict) and "actions" in c:
        return c["actions"] or {}
    return {}


def _symbol_matches(signal_symbol: Optional[str], cond_symbol: Optional[str]) -> bool:
    if not cond_symbol or cond_symbol == "*":
        return True
    s = (signal_symbol or "").replace("/", "").upper()
    c = str(cond_symbol).replace("/", "").upper()
    if not s:
        return False
    return s == c or s.startswith(c) or c in s


class CustomAlertsService:
    """Pro: пользовательские алерты и webhook."""

    def __init__(self):
        self.max_alerts_per_user = {
            SubscriptionPlan.FREE: 0,
            SubscriptionPlan.PREMIUM: 0,
            SubscriptionPlan.PRO: 20,
        }
        self.alert_types = [
            "price_threshold",
            "signal_confidence",
            "volume_spike",
            "trend_change",
            "portfolio_change",
        ]

    def _require_pro(self, user: User) -> None:
        if user.subscription_plan != SubscriptionPlan.PRO:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Custom alerts are only available for Pro subscribers",
            )

    async def create_custom_alert(
        self,
        user: User,
        db: Session,
        alert_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        await check_subscription_limit(user, feature="custom_alerts", api_call=False)
        self._require_pro(user)
        self._validate_alert_config(alert_config)

        conditions = alert_config["conditions"]
        actions = alert_config["actions"]
        webhook = alert_config.get("webhook_url")
        if not webhook and isinstance(actions, dict):
            webhook = actions.get("webhook_url")

        symbol_val = conditions.get("symbol") or "*"
        legacy_condition = {"conditions": conditions, "actions": actions}

        db_alert = CustomAlert(
            user_id=user.id,
            name=alert_config["name"],
            description=None,
            alert_type=alert_config["type"],
            status=AlertStatus.ACTIVE.value,
            symbol=symbol_val,
            condition=legacy_condition,
            conditions=conditions,
            notification_methods=actions,
            webhook_url=webhook,
            triggered_count=0,
            is_active=True,
        )
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)

        logger.info("Custom alert created for user %s: %s", user.email, alert_config.get("name"))

        return {
            "success": True,
            "message": "Custom alert created successfully",
            "data": {
                "id": str(db_alert.id),
                "user_id": user.id,
                "name": alert_config.get("name"),
                "type": alert_config.get("type"),
                "conditions": conditions,
                "actions": actions,
                "webhook_url": webhook,
                "is_active": True,
                "created_at": db_alert.created_at.isoformat() if db_alert.created_at else None,
                "triggered_count": 0,
            },
        }

    def _row_to_runtime_alert(self, db_alert: CustomAlert) -> Dict[str, Any]:
        actions = dict(_stored_actions(db_alert))
        if db_alert.webhook_url and "webhook_url" not in actions:
            actions["webhook_url"] = db_alert.webhook_url
        return {
            "id": str(db_alert.id),
            "name": db_alert.name,
            "type": db_alert.alert_type,
            "conditions": _stored_conditions(db_alert),
            "actions": actions,
            "is_active": db_alert.is_active,
            "created_at": db_alert.created_at.isoformat() if db_alert.created_at else "",
            "triggered_count": db_alert.triggered_count or 0,
        }

    async def trigger_alert_check(self, signal: Signal, db: Session) -> None:
        try:
            from ..models.channel import Channel

            channel = db.query(Channel).filter(Channel.id == signal.channel_id).first()
            if not channel:
                return

            user = db.query(User).filter(User.id == channel.owner_id).first()
            if not user or user.subscription_plan != SubscriptionPlan.PRO:
                return

            db_alerts = (
                db.query(CustomAlert)
                .filter(CustomAlert.user_id == user.id, CustomAlert.is_active.is_(True))
                .all()
            )

            for db_alert in db_alerts:
                alert = self._row_to_runtime_alert(db_alert)
                if await self._should_trigger_alert(alert, signal):
                    await self._execute_alert_actions(db, alert, signal, user)
        except Exception as e:
            logger.error("Error checking custom alerts: %s", e)

    async def send_webhook_notification(
        self,
        webhook_url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        try:
            default_headers = {
                "Content-Type": "application/json",
                "User-Agent": "CryptoAnalyticsPlatform/1.0",
            }
            if headers:
                default_headers.update(headers)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=default_headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        logger.info("Webhook sent successfully to %s", webhook_url)
                        return True
                    logger.warning("Webhook failed %s: %s", response.status, webhook_url)
                    return False
        except Exception as e:
            logger.error("Error sending webhook to %s: %s", webhook_url, e)
            return False

    async def get_user_alerts(self, user: User, db: Session) -> List[Dict[str, Any]]:
        await check_subscription_limit(user, feature="custom_alerts", api_call=False)
        self._require_pro(user)

        rows = (
            db.query(CustomAlert)
            .filter(CustomAlert.user_id == user.id, CustomAlert.is_active.is_(True))
            .all()
        )
        out = []
        for db_alert in rows:
            out.append(
                {
                    "id": str(db_alert.id),
                    "name": db_alert.name,
                    "alert_type": db_alert.alert_type,
                    "conditions": _stored_conditions(db_alert),
                    "notification_methods": _stored_actions(db_alert),
                    "webhook_url": db_alert.webhook_url,
                    "is_active": db_alert.is_active,
                    "created_at": db_alert.created_at.isoformat() if db_alert.created_at else None,
                    "triggered_count": db_alert.triggered_count or 0,
                }
            )
        return out

    async def update_alert(
        self,
        user: User,
        db: Session,
        alert_id: str,
        update_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        await check_subscription_limit(user, feature="custom_alerts", api_call=False)
        self._require_pro(user)

        try:
            aid = int(alert_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

        db_alert = (
            db.query(CustomAlert)
            .filter(CustomAlert.id == aid, CustomAlert.user_id == user.id)
            .first()
        )
        if not db_alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

        allowed = {"name", "is_active", "conditions", "notification_methods", "webhook_url", "symbol"}
        for field, value in update_data.items():
            if field not in allowed:
                continue
            setattr(db_alert, field, value)

        if "conditions" in update_data or "notification_methods" in update_data:
            db_alert.condition = {
                "conditions": _stored_conditions(db_alert),
                "actions": _stored_actions(db_alert),
            }

        db_alert.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_alert)

        return {
            "id": str(db_alert.id),
            "name": db_alert.name,
            "alert_type": db_alert.alert_type,
            "conditions": _stored_conditions(db_alert),
            "notification_methods": _stored_actions(db_alert),
            "webhook_url": db_alert.webhook_url,
            "is_active": db_alert.is_active,
            "created_at": db_alert.created_at.isoformat() if db_alert.created_at else None,
            "updated_at": db_alert.updated_at.isoformat() if db_alert.updated_at else None,
            "triggered_count": db_alert.triggered_count or 0,
        }

    async def delete_alert(self, user: User, db: Session, alert_id: str) -> bool:
        await check_subscription_limit(user, feature="custom_alerts", api_call=False)
        self._require_pro(user)

        try:
            aid = int(alert_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

        db_alert = (
            db.query(CustomAlert)
            .filter(CustomAlert.id == aid, CustomAlert.user_id == user.id)
            .first()
        )
        if not db_alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

        db.delete(db_alert)
        db.commit()
        logger.info("Alert %s deleted for user %s", alert_id, user.email)
        return True

    def _validate_alert_config(self, config: Dict[str, Any]) -> None:
        required_fields = ["name", "type", "conditions", "actions"]
        for field in required_fields:
            if field not in config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

        if config["type"] not in self.alert_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid alert type. Supported types: {', '.join(self.alert_types)}",
            )

        conditions = config["conditions"]
        alert_type = config["type"]

        if alert_type == "price_threshold":
            if "symbol" not in conditions or "threshold_price" not in conditions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Price threshold alerts require 'symbol' and 'threshold_price'",
                )

        elif alert_type == "signal_confidence":
            if "confidence_threshold" not in conditions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Signal confidence alerts require 'confidence_threshold'",
                )

        actions = config["actions"]
        if not isinstance(actions, dict) or not actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Actions must be a non-empty dictionary",
            )

    async def _should_trigger_alert(self, alert: Dict[str, Any], signal: Signal) -> bool:
        conditions = alert["conditions"]
        alert_type = alert["type"]

        if alert_type == "signal_confidence":
            thr = float(conditions.get("confidence_threshold", 0))
            conf = _signal_confidence_normalized(signal)
            if conf < thr:
                return False
            if "symbol" in conditions and not _symbol_matches(signal.symbol, conditions["symbol"]):
                return False
            if "signal_type" in conditions and _signal_direction_str(signal) != str(
                conditions["signal_type"]
            ).lower():
                return False
            return True

        if alert_type == "price_threshold":
            if "symbol" not in conditions or "threshold_price" not in conditions:
                return False
            if not _symbol_matches(signal.symbol, conditions["symbol"]):
                return False
            threshold = float(conditions["threshold_price"])
            entry = float(signal.entry_price) if signal.entry_price is not None else 0.0
            direction = conditions.get("direction", "above")
            if direction == "above" and entry >= threshold:
                return True
            if direction == "below" and entry <= threshold:
                return True
            return False

        return False

    async def _execute_alert_actions(
        self,
        db: Session,
        alert: Dict[str, Any],
        signal: Signal,
        user: User,
    ) -> None:
        actions = alert["actions"]

        payload = {
            "alert_id": alert["id"],
            "alert_name": alert["name"],
            "alert_type": alert["type"],
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "signal": {
                "id": signal.id,
                "symbol": signal.symbol,
                "signal_type": _signal_direction_str(signal),
                "entry_price": float(signal.entry_price) if signal.entry_price is not None else None,
                "target_price": float(signal.tp1_price) if signal.tp1_price is not None else None,
                "stop_loss": float(signal.stop_loss) if signal.stop_loss is not None else None,
                "confidence": _signal_confidence_normalized(signal),
                "created_at": signal.created_at.isoformat() if signal.created_at else None,
            },
            "user": {"id": user.id, "email": user.email},
        }

        if actions.get("webhook_url"):
            await self.send_webhook_notification(
                webhook_url=actions["webhook_url"],
                payload=payload,
            )

        if actions.get("email_notification"):
            await self._send_alert_email(user, alert, signal, payload)

        try:
            aid = int(alert["id"])
            db_alert = db.query(CustomAlert).filter(CustomAlert.id == aid).first()
            if db_alert:
                db_alert.triggered_count = (db_alert.triggered_count or 0) + 1
                db_alert.last_triggered_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as e:
            logger.error("Error updating alert trigger count: %s", e)

    async def _send_alert_email(
        self,
        user: User,
        alert: Dict[str, Any],
        signal: Signal,
        payload: Dict[str, Any],
    ) -> None:
        try:
            from ..services.email_service import email_service

            email_data = {
                "user_name": user.name or user.email,
                "alert_name": alert["name"],
                "alert_type": alert["type"],
                "signal_symbol": signal.symbol,
                "signal_type": _signal_direction_str(signal).upper(),
                "entry_price": signal.entry_price,
                "confidence": _signal_confidence_normalized(signal),
                "triggered_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "dashboard_url": f"{email_service.frontend_url}/dashboard",
                "manage_alerts_url": f"{email_service.frontend_url}/settings/alerts",
            }

            await email_service.send_email(
                to_email=user.email,
                subject=f"Custom Alert Triggered: {alert['name']}",
                template_name="custom_alert_notification",
                template_data=email_data,
            )
        except Exception as e:
            logger.error("Error sending alert email: %s", e)

    def get_alert_templates(self) -> Dict[str, Any]:
        return {
            "templates": {
                "high_confidence_signals": {
                    "name": "High Confidence Signals",
                    "type": "signal_confidence",
                    "description": "Alert when signals have high confidence (>80%)",
                    "conditions": {"confidence_threshold": 0.8},
                    "actions": {"email_notification": True},
                },
                "btc_price_alert": {
                    "name": "BTC Price Alert",
                    "type": "price_threshold",
                    "description": "Alert when BTC entry crosses a threshold",
                    "conditions": {
                        "symbol": "BTC",
                        "threshold_price": 50000,
                        "direction": "above",
                    },
                    "actions": {"email_notification": True},
                },
            },
            "supported_actions": ["email_notification", "webhook_url"],
        }


custom_alerts_service = CustomAlertsService()
