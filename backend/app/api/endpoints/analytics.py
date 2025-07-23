"""
Analytics API Endpoints - Real channel metrics and signal validation
Part of Task 3.1: Система реального отслеживания сигналов
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.user import User
from ...models.channel import Channel
from ...core.auth import get_current_user
from ...services.channel_metrics_service import channel_metrics_service
from ...services.price_tracking_service import price_tracking_service
from ...services.signal_validation_service import signal_validation_service

router = APIRouter()

@router.get("/analytics/channel/{channel_id}/metrics")
async def get_channel_metrics(
    channel_id: str,
    period_days: int = Query(30, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive metrics for a specific channel
    Core feature: Real channel performance analysis
    """
    try:
        # Get channel and verify ownership
        channel = db.query(Channel).filter(
            Channel.id == channel_id,
            Channel.owner_id == current_user.id
        ).first()
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found or access denied"
            )
        
        # Calculate metrics
        metrics = await channel_metrics_service.calculate_channel_metrics(
            channel=channel,
            db=db,
            period_days=period_days
        )
        
        return {
            "success": True,
            "data": metrics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate channel metrics: {str(e)}"
        )

@router.get("/analytics/channels/metrics")
async def get_all_channels_metrics(
    period_days: int = Query(30, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get metrics for all user's channels
    """
    try:
        all_metrics = await channel_metrics_service.calculate_all_channels_metrics(
            user=current_user,
            db=db,
            period_days=period_days
        )
        
        return {
            "success": True,
            "data": all_metrics,
            "total_channels": len(all_metrics)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate channels metrics: {str(e)}"
        )

@router.get("/analytics/ranking")
async def get_channel_ranking(
    period_days: int = Query(30, description="Analysis period in days"),
    limit: int = Query(50, description="Number of top channels to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get global channel ranking based on performance
    Core feature: Real channel ratings
    """
    try:
        # Check if user has access to full rankings (Premium/Pro feature)
        if current_user.subscription_plan.value == 'free':
            limit = min(limit, 10)  # Free users see only top 10
        
        ranking = await channel_metrics_service.get_channel_ranking(
            db=db,
            period_days=period_days,
            limit=limit
        )
        
        return {
            "success": True,
            "data": ranking,
            "period_days": period_days,
            "total_ranked": len(ranking),
            "user_access_level": current_user.subscription_plan.value
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get channel ranking: {str(e)}"
        )

@router.get("/analytics/price-tracking/status")
async def get_price_tracking_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get price tracking service status and statistics
    """
    try:
        stats = price_tracking_service.get_tracking_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tracking status: {str(e)}"
        )

@router.get("/analytics/price/{symbol}")
async def get_symbol_price_data(
    symbol: str,
    hours: int = Query(24, description="Hours of price history"),
    current_user: User = Depends(get_current_user)
):
    """
    Get current price and history for a symbol
    """
    try:
        current_price = await price_tracking_service.get_current_price(symbol.upper())
        price_history = await price_tracking_service.get_price_history(symbol.upper(), hours)
        
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "current_price": current_price,
                "price_history": price_history,
                "history_hours": hours,
                "last_updated": price_history[-1]['timestamp'].isoformat() if price_history else None
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get price data: {str(e)}"
        )

@router.post("/analytics/signals/validate")
async def validate_signal_message(
    message: str,
    channel_id: str,
    author: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate and parse a signal message
    Core feature: Signal validation and extraction
    """
    try:
        # Verify channel ownership
        channel = db.query(Channel).filter(
            Channel.id == channel_id,
            Channel.owner_id == current_user.id
        ).first()
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found or access denied"
            )
        
        # Parse and validate signal
        signal_data = await signal_validation_service.parse_and_validate_signal(
            message=message,
            channel_id=channel_id,
            db=db,
            author=author
        )
        
        if signal_data:
            # Create validated signal
            signal = await signal_validation_service.create_validated_signal(signal_data, db)
            
            if signal:
                # Add symbol to price tracking
                await price_tracking_service.add_symbol_tracking(signal.symbol, db)
                
                return {
                    "success": True,
                    "signal_detected": True,
                    "data": {
                        "signal_id": signal.id,
                        "symbol": signal.symbol,
                        "signal_type": signal.signal_type,
                        "entry_price": signal.entry_price,
                        "target_price": signal.target_price,
                        "stop_loss": signal.stop_loss,
                        "confidence": signal.confidence
                    }
                }
            else:
                return {
                    "success": False,
                    "signal_detected": True,
                    "error": "Failed to create signal"
                }
        else:
            return {
                "success": True,
                "signal_detected": False,
                "message": "No valid signal found in message"
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate signal: {str(e)}"
        )

@router.get("/analytics/signals/patterns")
async def get_signal_patterns(
    current_user: User = Depends(get_current_user)
):
    """
    Get supported signal patterns for validation
    """
    return {
        "success": True,
        "data": {
            "supported_patterns": {
                "buy_signals": [
                    "BUY BTC at $50000",
                    "LONG ETH entry: $3000",
                    "BTC buy signal",
                    "Entry: BTC $50000"
                ],
                "sell_signals": [
                    "SELL BTC at $55000",
                    "SHORT ETH entry: $2800",
                    "BTC sell signal",
                    "Exit: BTC $55000"
                ],
                "price_formats": [
                    "$50000",
                    "50000",
                    "entry: 50000",
                    "price: $50000"
                ],
                "target_formats": [
                    "TP: $55000",
                    "Target: 55000",
                    "TP1: $55000",
                    "Take profit: 55000"
                ],
                "stop_loss_formats": [
                    "SL: $45000",
                    "Stop loss: 45000",
                    "Stop: $45000"
                ]
            },
            "supported_symbols": [
                "BTC", "ETH", "BNB", "ADA", "XRP", "SOL", "DOT", "DOGE",
                "AVAX", "LUNA", "LINK", "UNI", "LTC", "BCH", "ALGO", "VET"
            ],
            "confidence_factors": {
                "signal_type_identified": 0.2,
                "symbol_identified": 0.2,
                "entry_price_provided": 0.15,
                "target_prices_provided": 0.1,
                "stop_loss_provided": 0.1,
                "detailed_message": 0.05,
                "technical_analysis": 0.05,
                "risk_management": 0.05
            }
        }
    }
