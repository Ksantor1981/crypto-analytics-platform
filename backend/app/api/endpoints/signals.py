import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from math import ceil
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.core.database import get_db
from app.core.auth import get_current_active_user, require_admin, get_current_user, require_premium
from app.services.signal_service import SignalService
from app.services.telegram_signal_service import TelegramSignalService
from app.models.user import User
from app.models.signal import Signal
from app import schemas
from app.schemas.signal import SignalResponse, SignalCreate, SignalUpdate, SignalFilterParams, SignalStats

router = APIRouter()


def verify_integration_token(
    x_integration_token: Optional[str] = Header(default=None, alias="X-Integration-Token"),
) -> None:
    """Закрывает webhook сигналов токеном из `TELEGRAM_INTEGRATION_TOKEN`.

    Безопасный default: если токен в settings пустой — эндпоинт отключён (503).
    Сравнение через `secrets.compare_digest`, чтобы не давать timing-атак.
    """
    settings = get_settings()
    expected = (settings.TELEGRAM_INTEGRATION_TOKEN or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Integration webhook is not configured (set TELEGRAM_INTEGRATION_TOKEN)",
        )
    provided = (x_integration_token or "").strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Integration-Token",
        )


def get_channel_real_name(channel_id: int) -> str:
    """
    Возвращает реальное название канала по ID
    """
    channel_mapping = {
        200: "📱 Reddit",
        300: "🌐 External APIs",
        301: "📊 CQS API",
        302: "📈 CTA API",
        400: "💬 Telegram",
        401: "🚀 CryptoPapa",
        402: "🐷 FatPigSignals",
        403: "⚡ BinanceKiller",
        404: "🌍 CryptoSignalsWorld",
        405: "💎 CryptoPumps"
    }

    return channel_mapping.get(channel_id, f"📋 Unknown Source {channel_id}")


@router.post("/", response_model=schemas.signal.SignalResponse, status_code=status.HTTP_201_CREATED)
async def create_signal(
    signal_in: schemas.signal.SignalCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new signal manually (admin-only).

    Обычные пользователи не публикуют сигналы — это делает либо парсер
    (`POST /signals/telegram/webhook` с `X-Integration-Token`), либо админ
    через эту ручку для тестов/ручных корректировок.
    """
    signal_service = SignalService(db)
    signal = signal_service.create_signal(signal_in=signal_in)

    # Send notifications to subscribed users
    from app.services.notification_service import NotificationService
    notification_service = NotificationService(db)
    background_tasks.add_task(notification_service.notify_users_of_new_signal, signal)

    return signal


@router.get("/", response_model=schemas.signal.SignalListResponse)
def get_signals(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(100, ge=1, le=200, description="Page size"),
    filters: schemas.signal.SignalFilterParams = Depends(),
    current_user: User = Depends(require_premium),
):
    """Retrieve a list of signals with pagination and filtering."""
    signal_service = SignalService(db)
    skip = (page - 1) * size
    signals, total = signal_service.get_signals(
        skip=skip, limit=size, filters=filters, user_subscription_tier=current_user.role.value
    )

    signals_with_channels = []
    for s in signals:
        s_dict = {c.name: getattr(s, c.name) for c in s.__table__.columns}
        s_dict["channel_name"] = s.channel.name if s.channel else None
        s_dict["channel_username"] = s.channel.username if s.channel else None
        signals_with_channels.append(s_dict)

    pages = ceil(total / size) if size else 0
    return {
        "signals": signals_with_channels,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


@router.get("/dashboard")
def get_signals_dashboard(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get signals without JOIN - simple version for dashboard.

    Authenticated-only: сигналы — premium-функционал по бизнес-модели Free/Premium.
    Free пользователь видит свой dashboard, монетизация платных деталей —
    через `/api/v1/signals/` (require_premium) и Stripe-подписку.
    """
    query = db.query(Signal)

    # Get total count
    total = query.count()

    # Apply pagination
    signals = query.order_by(Signal.created_at.desc()).offset(skip).limit(limit).all()

    # Convert to simple dict format
    result = []
    for signal in signals:
        signal_dict = {
            "id": signal.id,
            "asset": signal.asset,
            "symbol": signal.symbol,
            "direction": signal.direction,
            "entry_price": float(signal.entry_price) if signal.entry_price else None,
            "tp1_price": float(signal.tp1_price) if signal.tp1_price else None,
            "tp2_price": float(signal.tp2_price) if signal.tp2_price else None,
            "tp3_price": float(signal.tp3_price) if signal.tp3_price else None,
            "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
            "original_text": signal.original_text,
            "status": signal.status,
            "confidence_score": float(signal.confidence_score) if signal.confidence_score else None,
            "created_at": signal.created_at.isoformat() if signal.created_at else None,
            "updated_at": signal.updated_at.isoformat() if signal.updated_at else None,
            "expires_at": signal.expires_at.isoformat() if signal.expires_at else None,  # Ожидаемая дата выполнения
            "channel_id": signal.channel_id,
            "channel_name": get_channel_real_name(signal.channel_id)
        }
        result.append(signal_dict)

    return result


@router.get("/{signal_id}", response_model=schemas.signal.SignalWithChannel)
def get_signal(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve a specific signal by its ID (authenticated-only)."""
    signal_service = SignalService(db)
    signal = signal_service.get_signal_by_id(signal_id)
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found"
        )
    return signal


@router.put("/{signal_id}", response_model=schemas.signal.SignalResponse, dependencies=[Depends(require_admin)])
def update_signal(
    signal_id: int,
    signal_in: schemas.signal.SignalUpdate,
    db: Session = Depends(get_db),
):
    """Update a signal's details (admin only)."""
    signal_service = SignalService(db)
    updated_signal = signal_service.update_signal(signal_id=signal_id, signal_in=signal_in)
    if not updated_signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found"
        )
    return updated_signal


@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_signal(
    signal_id: int,
    db: Session = Depends(get_db),
):
    """Delete a signal (admin only)."""
    signal_service = SignalService(db)
    if not signal_service.delete_signal(signal_id=signal_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found"
        )
    return


@router.get("/stats/overview", response_model=schemas.signal.SignalStats, dependencies=[Depends(require_admin)])
def get_general_stats(db: Session = Depends(get_db)):
    """Get overall signal statistics."""
    signal_service = SignalService(db)
    return signal_service.get_signal_stats()


@router.get("/stats/channel/{channel_id}", response_model=schemas.signal.ChannelSignalStats)
def get_channel_stats(
    channel_id: int,
    db: Session = Depends(get_db),
):
    """Get signal statistics for a specific channel."""
    signal_service = SignalService(db)
    stats = signal_service.get_channel_stats(channel_id=channel_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found or no signals for this channel"
        )
    return stats


@router.get("/stats/asset-performance", response_model=List[schemas.signal.AssetPerformance], dependencies=[Depends(require_admin)])
def get_asset_performance(
    db: Session = Depends(get_db),
):
    """Get performance statistics for each asset."""
    signal_service = SignalService(db)
    return signal_service.get_asset_performance()


@router.post(
    "/telegram/webhook",
    response_model=schemas.signal.TelegramSignalResponse,
    dependencies=[Depends(verify_integration_token)],
)
def handle_telegram_signal(
    signal_in: schemas.signal.TelegramSignalCreate,
    db: Session = Depends(get_db),
):
    """Webhook endpoint to receive signals from Telegram bots/integrations.

    Auth: header `X-Integration-Token` равен `settings.TELEGRAM_INTEGRATION_TOKEN`.
    Если токен не сконфигурирован, эндпоинт возвращает 503 (закрыт по умолчанию).
    """
    telegram_signal_service = TelegramSignalService(db)
    telegram_signal = telegram_signal_service.create_signal(signal_in)
    return telegram_signal
