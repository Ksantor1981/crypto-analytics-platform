"""
Service for managing Telegram signals
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from fastapi import HTTPException, status
from datetime import datetime
import json

from app.models.signal import TelegramSignal
from app.schemas.signal import TelegramSignalCreate, TelegramSignalResponse


class TelegramSignalService:
    """Service for Telegram signal operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_signal(self, signal_data: TelegramSignalCreate) -> TelegramSignal:
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
        await self.db.commit()
        await self.db.refresh(db_signal)
        
        return db_signal
    
    async def get_signals(
        self,
        skip: int = 0,
        limit: int = 100,
        symbol: Optional[str] = None,
        signal_type: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[TelegramSignal]:
        """Get Telegram signals with filters."""
        query = select(TelegramSignal)
        
        if symbol:
            query = query.where(TelegramSignal.symbol.ilike(f"%{symbol.upper()}%"))
        
        if signal_type:
            query = query.where(TelegramSignal.signal_type == signal_type.lower())
        
        if source:
            query = query.where(TelegramSignal.source.ilike(f"%{source}%"))
        
        if status:
            query = query.where(TelegramSignal.status == status.upper())
        
        query = query.order_by(desc(TelegramSignal.created_at)).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_signal_by_id(self, signal_id: int) -> Optional[TelegramSignal]:
        """Get signal by ID."""
        query = select(TelegramSignal).where(TelegramSignal.id == signal_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_signal_status(self, signal_id: int, status: str) -> TelegramSignal:
        """Update signal status."""
        signal = await self.get_signal_by_id(signal_id)
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found"
            )
        
        signal.status = status.upper()
        signal.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(signal)
        
        return signal
    
    async def delete_signal(self, signal_id: int) -> bool:
        """Delete signal."""
        signal = await self.get_signal_by_id(signal_id)
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found"
            )
        
        await self.db.delete(signal)
        await self.db.commit()
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get signal statistics."""
        total_query = select(func.count(TelegramSignal.id))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()
        
        by_status_query = select(
            TelegramSignal.status,
            func.count(TelegramSignal.id)
        ).group_by(TelegramSignal.status)
        status_result = await self.db.execute(by_status_query)
        by_status = dict(status_result.all())
        
        by_type_query = select(
            TelegramSignal.signal_type,
            func.count(TelegramSignal.id)
        ).group_by(TelegramSignal.signal_type)
        type_result = await self.db.execute(by_type_query)
        by_type = dict(type_result.all())
        
        return {
            "total_signals": total,
            "by_status": by_status,
            "by_type": by_type,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def create_signals_batch(self, signals: List[TelegramSignalCreate]) -> List[TelegramSignal]:
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
        await self.db.commit()
        
        for signal in db_signals:
            await self.db.refresh(signal)
        
        return db_signals 