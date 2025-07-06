from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, asc, case
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from decimal import Decimal
import math

from app.models.signal import Signal, SignalDirection, SignalStatus
from app.models.channel import Channel
from app.schemas.signal import (
    SignalCreate, 
    SignalUpdate, 
    SignalFilterParams,
    SignalStats,
    ChannelSignalStats,
    AssetPerformance
)


class SignalService:
    """Service for signal management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_signal(self, signal_data: SignalCreate) -> Signal:
        """Create a new signal."""
        # Verify channel exists
        channel = self.db.query(Channel).filter(Channel.id == signal_data.channel_id).first()
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )
        
        # Create signal
        db_signal = Signal(
            channel_id=signal_data.channel_id,
            asset=signal_data.asset.upper(),
            direction=signal_data.direction,
            entry_price=Decimal(str(signal_data.entry_price)),
            tp1_price=Decimal(str(signal_data.tp1_price)) if signal_data.tp1_price else None,
            tp2_price=Decimal(str(signal_data.tp2_price)) if signal_data.tp2_price else None,
            tp3_price=Decimal(str(signal_data.tp3_price)) if signal_data.tp3_price else None,
            stop_loss=Decimal(str(signal_data.stop_loss)) if signal_data.stop_loss else None,
            entry_price_low=Decimal(str(signal_data.entry_price_low)) if signal_data.entry_price_low else None,
            entry_price_high=Decimal(str(signal_data.entry_price_high)) if signal_data.entry_price_high else None,
            original_text=signal_data.original_text,
            message_timestamp=signal_data.message_timestamp or datetime.utcnow(),
            telegram_message_id=signal_data.telegram_message_id,
            expires_at=signal_data.expires_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Calculate risk/reward ratio
        if db_signal.tp1_price and db_signal.stop_loss:
            if signal_data.direction in [SignalDirection.LONG, SignalDirection.BUY]:
                potential_profit = float(db_signal.tp1_price - db_signal.entry_price)
                potential_loss = float(db_signal.entry_price - db_signal.stop_loss)
            else:  # SHORT/SELL
                potential_profit = float(db_signal.entry_price - db_signal.tp1_price)
                potential_loss = float(db_signal.stop_loss - db_signal.entry_price)
            
            if potential_loss > 0:
                db_signal.risk_reward_ratio = Decimal(str(potential_profit / potential_loss))
        
        self.db.add(db_signal)
        self.db.commit()
        self.db.refresh(db_signal)
        
        return db_signal
    
    def get_signal_by_id(self, signal_id: int) -> Optional[Signal]:
        """Get signal by ID with channel info."""
        return self.db.query(Signal).options(joinedload(Signal.channel)).filter(Signal.id == signal_id).first()
    
    def get_signals(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[SignalFilterParams] = None,
        user_subscription_tier: str = "FREE_USER"
    ) -> Tuple[List[Signal], int]:
        """Get signals with filtering and pagination."""
        query = self.db.query(Signal).options(joinedload(Signal.channel))
        
        # Apply filters
        if filters:
            if filters.channel_id:
                query = query.filter(Signal.channel_id == filters.channel_id)
            
            if filters.asset:
                query = query.filter(Signal.asset.ilike(f"%{filters.asset.upper()}%"))
            
            if filters.direction:
                query = query.filter(Signal.direction == filters.direction)
            
            if filters.status:
                query = query.filter(Signal.status == filters.status)
            
            if filters.date_from:
                query = query.filter(Signal.message_timestamp >= filters.date_from)
            
            if filters.date_to:
                query = query.filter(Signal.message_timestamp <= filters.date_to)
            
            if filters.successful_only:
                query = query.filter(Signal.is_successful == True)
            
            if filters.min_roi is not None:
                query = query.filter(Signal.profit_loss_percentage >= filters.min_roi)
            
            if filters.max_roi is not None:
                query = query.filter(Signal.profit_loss_percentage <= filters.max_roi)
        
        # For free users, limit to last 30 days and 50 signals
        if user_subscription_tier == "FREE_USER":
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            query = query.filter(Signal.message_timestamp >= thirty_days_ago)
            limit = min(limit, 50)
        
        # Get total count
        total = query.count()
        
        # Apply sorting and pagination
        signals = query.order_by(desc(Signal.message_timestamp)).offset(skip).limit(limit).all()
        
        return signals, total
    
    def update_signal(self, signal_id: int, signal_data: SignalUpdate) -> Optional[Signal]:
        """Update signal information."""
        signal = self.get_signal_by_id(signal_id)
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found"
            )
        
        # Update fields
        update_data = signal_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['final_exit_price', 'profit_loss_percentage', 'profit_loss_absolute', 
                        'ml_success_probability', 'ml_predicted_roi', 'confidence_score', 'risk_reward_ratio']:
                if value is not None:
                    setattr(signal, field, Decimal(str(value)))
            else:
                setattr(signal, field, value)
        
        # Auto-calculate profit/loss if exit price is set
        if signal_data.final_exit_price and not signal_data.profit_loss_percentage:
            roi = signal.calculate_roi(Decimal(str(signal_data.final_exit_price)))
            signal.profit_loss_percentage = roi
        
        # Auto-determine success based on status
        if signal_data.status:
            if signal_data.status in [SignalStatus.TP1_HIT, SignalStatus.TP2_HIT, SignalStatus.TP3_HIT]:
                signal.is_successful = True
            elif signal_data.status in [SignalStatus.SL_HIT, SignalStatus.EXPIRED]:
                signal.is_successful = False
        
        signal.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(signal)
        
        return signal
    
    def delete_signal(self, signal_id: int) -> bool:
        """Delete signal (admin only)."""
        signal = self.get_signal_by_id(signal_id)
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found"
            )
        
        self.db.delete(signal)
        self.db.commit()
        return True
    
    def get_signal_stats(self, filters: Optional[SignalFilterParams] = None) -> SignalStats:
        """Get signal statistics."""
        query = self.db.query(Signal)
        
        # Apply filters
        if filters:
            if filters.channel_id:
                query = query.filter(Signal.channel_id == filters.channel_id)
            if filters.date_from:
                query = query.filter(Signal.message_timestamp >= filters.date_from)
            if filters.date_to:
                query = query.filter(Signal.message_timestamp <= filters.date_to)
        
        signals = query.all()
        
        if not signals:
            return SignalStats()
        
        total_signals = len(signals)
        successful_signals = len([s for s in signals if s.is_successful == True])
        failed_signals = len([s for s in signals if s.is_successful == False])
        pending_signals = len([s for s in signals if s.is_successful is None])
        
        # Calculate accuracy
        completed_signals = successful_signals + failed_signals
        accuracy = (successful_signals / completed_signals * 100) if completed_signals > 0 else 0
        
        # Calculate ROI stats
        roi_values = [float(s.profit_loss_percentage) for s in signals if s.profit_loss_percentage is not None]
        average_roi = sum(roi_values) / len(roi_values) if roi_values else 0
        total_profit_loss = sum(roi_values) if roi_values else 0
        best_roi = max(roi_values) if roi_values else 0
        worst_roi = min(roi_values) if roi_values else 0
        
        # Calculate duration
        durations = [s.duration_hours for s in signals if s.duration_hours is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Target hit breakdown
        tp1_hits = len([s for s in signals if s.reached_tp1])
        tp2_hits = len([s for s in signals if s.reached_tp2])
        tp3_hits = len([s for s in signals if s.reached_tp3])
        sl_hits = len([s for s in signals if s.hit_stop_loss])
        expired_signals = len([s for s in signals if s.status == SignalStatus.EXPIRED])
        
        return SignalStats(
            total_signals=total_signals,
            successful_signals=successful_signals,
            failed_signals=failed_signals,
            pending_signals=pending_signals,
            accuracy_percentage=round(accuracy, 2),
            average_roi=round(average_roi, 2),
            total_profit_loss=round(total_profit_loss, 2),
            best_signal_roi=round(best_roi, 2),
            worst_signal_roi=round(worst_roi, 2),
            average_duration_hours=round(avg_duration, 2),
            tp1_hits=tp1_hits,
            tp2_hits=tp2_hits,
            tp3_hits=tp3_hits,
            sl_hits=sl_hits,
            expired_signals=expired_signals
        )
    
    def get_channel_stats(self, channel_id: int, days: int = 30) -> ChannelSignalStats:
        """Get signal statistics for a specific channel."""
        date_from = datetime.utcnow() - timedelta(days=days)
        filters = SignalFilterParams(channel_id=channel_id, date_from=date_from)
        
        stats = self.get_signal_stats(filters)
        
        # Get channel name
        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        channel_name = channel.name if channel else None
        
        return ChannelSignalStats(
            channel_id=channel_id,
            channel_name=channel_name,
            period_days=days,
            **stats.dict()
        )
    
    def get_asset_performance(self, days: int = 30) -> List[AssetPerformance]:
        """Get performance analytics by asset."""
        date_from = datetime.utcnow() - timedelta(days=days)
        
        # Query for asset performance
        query = self.db.query(
            Signal.asset,
            func.count(Signal.id).label('total_signals'),
            func.sum(case((Signal.is_successful == True, 1), else_=0)).label('successful_signals'),
            func.avg(Signal.profit_loss_percentage).label('avg_roi'),
            func.sum(Signal.profit_loss_percentage).label('total_profit_loss'),
            func.avg(Signal.risk_reward_ratio).label('avg_risk_reward')
        ).filter(
            Signal.message_timestamp >= date_from
        ).group_by(Signal.asset).order_by(desc('total_signals'))
        
        results = query.all()
        
        asset_performances = []
        for result in results:
            total = result.total_signals or 0
            successful = result.successful_signals or 0
            accuracy = (successful / total * 100) if total > 0 else 0
            
            asset_performances.append(AssetPerformance(
                asset=result.asset,
                total_signals=total,
                successful_signals=successful,
                accuracy_percentage=round(accuracy, 2),
                average_roi=round(float(result.avg_roi or 0), 2),
                total_profit_loss=round(float(result.total_profit_loss or 0), 2),
                risk_reward_ratio=round(float(result.avg_risk_reward or 0), 2)
            ))
        
        return asset_performances
    
    def get_top_performing_signals(self, limit: int = 10, days: int = 30) -> List[Signal]:
        """Get top performing signals by ROI."""
        date_from = datetime.utcnow() - timedelta(days=days)
        
        return self.db.query(Signal).options(joinedload(Signal.channel)).filter(
            and_(
                Signal.message_timestamp >= date_from,
                Signal.profit_loss_percentage.isnot(None),
                Signal.is_successful == True
            )
        ).order_by(desc(Signal.profit_loss_percentage)).limit(limit).all()
    
    def cancel_signal(self, signal_id: int, reason: str = "Manual cancellation") -> Signal:
        """Cancel a signal."""
        signal = self.get_signal_by_id(signal_id)
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found"
            )
        
        if signal.status != SignalStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only cancel pending signals"
            )
        
        signal.status = SignalStatus.CANCELLED
        signal.cancelled_at = datetime.utcnow()
        signal.cancellation_reason = reason
        signal.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(signal)
        
        return signal
    
    def expire_old_signals(self) -> int:
        """Expire signals that have passed their expiration time."""
        now = datetime.utcnow()
        
        expired_signals = self.db.query(Signal).filter(
            and_(
                Signal.status == SignalStatus.PENDING,
                Signal.expires_at.isnot(None),
                Signal.expires_at <= now
            )
        ).all()
        
        for signal in expired_signals:
            signal.status = SignalStatus.EXPIRED
            signal.updated_at = now
        
        self.db.commit()
        
        return len(expired_signals) 