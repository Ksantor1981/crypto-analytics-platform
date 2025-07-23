"""
Service for managing Telegram signals
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException, status
from datetime import datetime
import json

from app.models.signal import TelegramSignal
from app.schemas.signal import TelegramSignalCreate


class TelegramSignalService:
    """Service for Telegram signal operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_signal(self, signal_data: TelegramSignalCreate) -> TelegramSignal:
        """Create a new Telegram signal."""
        db_signal = TelegramSignal(
            symbol=signal_data.symbol.upper(),
            signal_type=signal_data.signal_type.lower(),
            entry_price=signal_data.entry_price,
            target_price=signal_data.target_price,
            stop_loss=signal_data.stop_loss,
            confidence=signal_data.confidence,
            source=signal_data.source,
            original_text=signal_data.original_text,
            metadata=signal_data.metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_signal)
        self.db.commit()
        self.db.refresh(db_signal)
        
        return db_signal
    
    def get_signals(
        self,
        skip: int = 0,
        limit: int = 100,
        symbol: Optional[str] = None,
        signal_type: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[TelegramSignal]:
        """Get Telegram signals with filters."""
        query = self.db.query(TelegramSignal)
        
        if symbol:
            query = query.filter(TelegramSignal.symbol.ilike(f"%{symbol.upper()}%"))
        
        if signal_type:
            query = query.filter(TelegramSignal.signal_type == signal_type.lower())
        
        if source:
            query = query.filter(TelegramSignal.source.ilike(f"%{source}%"))
        
        if status:
            query = query.filter(TelegramSignal.status == status.upper())
        
        return query.order_by(desc(TelegramSignal.created_at)).offset(skip).limit(limit).all()
    
    def get_signal_by_id(self, signal_id: int) -> Optional[TelegramSignal]:
        """Get signal by ID."""
        return self.db.query(TelegramSignal).filter(TelegramSignal.id == signal_id).first()
    
    def update_signal_status(self, signal_id: int, status: str) -> TelegramSignal:
        """Update signal status."""
        signal = self.get_signal_by_id(signal_id)
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found"
            )
        
        signal.status = status.upper()
        signal.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(signal)
        
        return signal
    
    def delete_signal(self, signal_id: int) -> bool:
        """Delete signal."""
        signal = self.get_signal_by_id(signal_id)
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found"
            )
        
        self.db.delete(signal)
        self.db.commit()
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get signal statistics."""
        total = self.db.query(func.count(TelegramSignal.id)).scalar()
        
        by_status_query = self.db.query(
            TelegramSignal.status,
            func.count(TelegramSignal.id)
        ).group_by(TelegramSignal.status)
        by_status = dict(by_status_query.all())
        
        by_type_query = self.db.query(
            TelegramSignal.signal_type,
            func.count(TelegramSignal.id)
        ).group_by(TelegramSignal.signal_type)
        by_type = dict(by_type_query.all())
        
        return {
            "total_signals": total,
            "by_status": by_status,
            "by_type": by_type,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def create_signals_batch(self, signals: List[TelegramSignalCreate]) -> List[TelegramSignal]:
        """Create multiple signals in batch."""
        db_signals = []
        
        for signal_data in signals:
            db_signal = TelegramSignal(
                symbol=signal_data.symbol.upper(),
                signal_type=signal_data.signal_type.lower(),
                entry_price=signal_data.entry_price,
                target_price=signal_data.target_price,
                stop_loss=signal_data.stop_loss,
                confidence=signal_data.confidence,
                source=signal_data.source,
                original_text=signal_data.original_text,
                metadata=signal_data.metadata,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_signals.append(db_signal)
        
        self.db.add_all(db_signals)
        self.db.commit()
        
        for signal in db_signals:
            self.db.refresh(signal)
        
        return db_signals