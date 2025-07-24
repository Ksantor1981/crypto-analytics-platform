from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, SubscriptionPlan, SubscriptionStatus
from app.services.user_service import UserService
from app.services.subscription_service import SubscriptionService
from app.core.auth import get_current_user
import contextlib

class SubscriptionLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware для проверки лимитов и статуса подписки пользователя.
    - Если подписка истекла — downgrade на free-план.
    - Если лимиты превышены — graceful degradation (ограничение доступа).
    """
    async def dispatch(self, request: Request, call_next):
        # Применять только к защищённым API (например, /api/v1/)
        if not request.url.path.startswith("/api/v1/"):
            return await call_next(request)
        
        # Пропускать публичные эндпоинты
        if any(request.url.path.startswith(p) for p in [
            "/api/v1/auth", "/api/v1/health", "/api/v1/docs", "/api/v1/openapi.json"
        ]):
            return await call_next(request)
        
        # Получаем пользователя (если есть токен)
        user = None
        with contextlib.suppress(Exception):
            user = await get_current_user(request)
        if not user:
            return await call_next(request)
        
        # Проверяем статус подписки
        db: Session = next(get_db())
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)
        db_user = user_service.get_user_by_id(user.id)
        subscription = subscription_service.get_user_subscription(user.id)
        
        # Если подписка истекла — downgrade на free-план
        if subscription and subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]:
            db_user.subscription_plan = SubscriptionPlan.FREE
            db_user.subscription_status = SubscriptionStatus.EXPIRED
            db_user.channels_limit = 3
            db_user.api_calls_limit = 100
            db.commit()
            db.refresh(db_user)
        
        # Проверяем лимиты (каналы, API)
        if db_user.subscription_plan == SubscriptionPlan.FREE:
            if db_user.api_calls_used_today >= db_user.api_calls_limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Лимит API-запросов для Free-плана исчерпан. Оформите подписку для расширения лимитов.",
                        "graceful_degradation": True
                    }
                )
            # Можно добавить проверку лимита каналов и других фич
        # Для premium/pro — можно добавить свои лимиты
        # ...
        return await call_next(request) 