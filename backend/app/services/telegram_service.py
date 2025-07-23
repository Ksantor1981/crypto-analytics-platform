"""
Telegram Service for Backend Integration
Enhanced version with proper database integration
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.channel import Channel
from app.models.signal import Signal, SignalDirection
from app.core.database import get_db

# Import Telegram client (will be None if not available)
try:
    from workers.telegram.telegram_client import TelegramSignalCollector
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    TelegramSignalCollector = None

logger = logging.getLogger(__name__)

# Configuration for real Telegram channels
REAL_TELEGRAM_CHANNELS = [
    {
        "name": "CryptoSignalsPro",
        "url": "t.me/cryptosignalspro",
        "description": "Professional crypto trading signals",
        "category": "premium"
    },
    {
        "name": "WhaleSignals",
        "url": "t.me/whalesignals",
        "description": "Whale movement tracking signals",
        "category": "whale_tracking"
    }
]

class BackendTelegramService:
    """Backend service for Telegram integration with database operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.collector = None
        
        if TELEGRAM_AVAILABLE:
            try:
                self.collector = TelegramSignalCollector()
                logger.info("✅ Telegram collector initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Telegram collector: {e}")
                self.collector = None
    
    async def initialize_telegram_client(self) -> bool:
        """Initialize Telegram client if available"""
        
        if not TELEGRAM_AVAILABLE or not self.collector:
            logger.error("Telegram client not available - cannot collect signals")
            return {
                "success": False,
                "error": "Telegram client not configured",
                "channels_processed": 0,
                "signals_collected": 0,
                "mode": "error"
            }
        
        try:
            success = await self.collector.initialize_client()
            if success:
                logger.info("✅ Telegram client initialized successfully")
            else:
                logger.warning("❌ Failed to initialize Telegram client")
            return success
        except Exception as e:
            logger.error(f"Error initializing Telegram client: {e}")
            return False
    
    def get_or_create_channel(self, channel_config: Dict) -> Channel:
        """Get existing channel or create new one"""
        
        channel_name = channel_config.get('name', 'Unknown')
        channel_url = channel_config.get('url', '')
        
        # Try to find existing channel by name or URL
        existing_channel = self.db.query(Channel).filter(
            (Channel.name == channel_name) | (Channel.url == channel_url)
        ).first()
        
        if existing_channel:
            # Update existing channel info
            existing_channel.platform = 'telegram'
            existing_channel.is_active = True
            existing_channel.updated_at = datetime.utcnow()
            self.db.commit()
            return existing_channel
        
        # Create new channel
        new_channel = Channel(
            name=channel_name,
            url=channel_url,
            platform='telegram',
            description=channel_config.get('description', ''),
            category=channel_config.get('category', 'crypto'),
            is_active=True,
            signals_count=0,  # Используем правильное поле
            accuracy=0.0,     # Используем правильное поле  
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(new_channel)
        self.db.commit()
        self.db.refresh(new_channel)
        
        logger.info(f"✅ Created new channel: {channel_name}")
        return new_channel
    
    def save_signal_to_db(self, signal_data: Dict, channel: Channel) -> Optional[Signal]:
        """Save parsed signal to database"""
        
        try:
            # Check if signal already exists (prevent duplicates)
            existing_signal = self.db.query(Signal).filter(
                Signal.channel_id == channel.id,
                Signal.asset == signal_data['symbol'],
                Signal.entry_price == signal_data['entry_price'],
                Signal.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).first()
            
            if existing_signal:
                logger.debug(f"Signal already exists for {signal_data['symbol']} in {channel.name}")
                return existing_signal
            
            # Create new signal with proper field mapping
            signal = Signal(
                channel_id=channel.id,
                asset=signal_data['symbol'],  # Use asset field
                symbol=signal_data['symbol'],  # Also populate symbol for compatibility
                direction=signal_data['direction'].upper(),  # Ensure uppercase
                entry_price=signal_data['entry_price'],
                tp1_price=signal_data.get('targets', [None])[0] if signal_data.get('targets') else None,
                tp2_price=signal_data.get('targets', [None, None])[1] if len(signal_data.get('targets', [])) > 1 else None,
                tp3_price=signal_data.get('targets', [None, None, None])[2] if len(signal_data.get('targets', [])) > 2 else None,
                stop_loss=signal_data.get('stop_loss'),
                confidence_score=signal_data.get('confidence_score', 0.5),
                original_text=signal_data.get('raw_message', ''),
                timestamp=signal_data.get('timestamp', datetime.utcnow()),
                message_timestamp=signal_data.get('timestamp', datetime.utcnow())
            )
            
            self.db.add(signal)
            self.db.commit()
            self.db.refresh(signal)
            
            logger.info(f"✅ Saved signal: {signal.symbol} {signal.direction} @ {signal.entry_price}")
            return signal
            
        except Exception as e:
            logger.error(f"Error saving signal to database: {e}")
            self.db.rollback()
            return None
    
    async def collect_signals_from_channels(self) -> Dict[str, Any]:
        """Collect signals from all configured channels"""
        
        if not TELEGRAM_AVAILABLE:
            logger.error("Telegram client not available - cannot collect signals")
            return {
                "success": False,
                "error": "Telegram client not configured",
                "channels_processed": 0,
                "signals_collected": 0,
                "mode": "error"
            }
        
        if not self.collector:
            logger.error("Telegram collector not initialized")
            return {"success": False, "error": "Collector not available"}
        
        try:
            # Initialize client if needed
            if not self.collector.client:
                success = await self.initialize_telegram_client()
                if not success:
                    return {"success": False, "error": "Failed to initialize client"}
            
            # Collect signals from real channels
            results = await self.collector.collect_signals_real()
            
            if not results.get('success', False):
                logger.warning(f"Signal collection failed: {results.get('error', 'Unknown error')}")
                return results
            
            # Process and save signals to database
            total_saved = 0
            total_channels = 0
            
            for channel_name, signals in results.get('signals', {}).items():
                if not signals:
                    continue
                    
                # Get or create channel
                channel_config = next(
                    (ch for ch in REAL_TELEGRAM_CHANNELS if ch.get('name') == channel_name),
                    {'name': channel_name, 'url': f't.me/{channel_name}'}
                )
                
                channel = self.get_or_create_channel(channel_config)
                total_channels += 1
                
                # Save each signal
                for signal_data in signals:
                    saved_signal = self.save_signal_to_db(signal_data, channel)
                    if saved_signal:
                        total_saved += 1
            
            # Update channel statistics
            await self._update_channel_statistics()
            
            return {
                "success": True,
                "total_signals_collected": results.get('total_signals', 0),
                "total_signals_saved": total_saved,
                "channels_processed": total_channels,
                "collection_time": results.get('collection_time', 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in signal collection: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_channel_statistics(self):
        """Update channel statistics based on signals, assign category and score."""
        try:
            # Get all active channels
            channels = self.db.query(Channel).filter(Channel.is_active == True).all()
            for channel in channels:
                # Count total signals
                total_signals = self.db.query(Signal).filter(Signal.channel_id == channel.id).count()
                successful_signals = self.db.query(Signal).filter(
                    Signal.channel_id == channel.id,
                    Signal.is_successful == True
                ).count()
                accuracy = (successful_signals / total_signals * 100) if total_signals > 0 else 0.0
                # ROI, drawdown, sharpe
                roi_values = [float(s.profit_loss_percentage) for s in self.db.query(Signal).filter(Signal.channel_id == channel.id).all() if s.profit_loss_percentage is not None]
                average_roi = sum(roi_values) / len(roi_values) if roi_values else 0.0
                # Max drawdown
                def calc_max_drawdown(roi_list):
                    if not roi_list:
                        return 0.0
                    peak = roi_list[0]
                    max_drawdown = 0.0
                    for roi in roi_list:
                        if roi > peak:
                            peak = roi
                        drawdown = peak - roi
                        if drawdown > max_drawdown:
                            max_drawdown = drawdown
                    return round(max_drawdown, 2)
                max_drawdown = calc_max_drawdown(roi_values)
                # Sharpe ratio
                def calc_sharpe(roi_list):
                    if not roi_list or len(roi_list) < 2:
                        return 0.0
                    mean_roi = sum(roi_list) / len(roi_list)
                    stddev = (sum((x - mean_roi) ** 2 for x in roi_list) / (len(roi_list) - 1)) ** 0.5
                    if stddev == 0:
                        return 0.0
                    return round(mean_roi / stddev, 2)
                sharpe_ratio = calc_sharpe(roi_values)
                # Score (динамический рейтинг)
                score = (accuracy * 0.5) + (average_roi * 0.3) + (sharpe_ratio * 0.2) - (max_drawdown * 0.1)
                # Категоризация
                if total_signals < 10:
                    category = "newcomer"
                elif accuracy > 70 and average_roi > 5:
                    category = "high_accuracy"
                elif max_drawdown > 20:
                    category = "high_risk"
                elif accuracy < 40 or average_roi < 0:
                    category = "underperforming"
                else:
                    category = "stable"
                # Update channel
                channel.signals_count = total_signals
                channel.successful_signals = successful_signals
                channel.accuracy = accuracy
                channel.average_roi = average_roi
                channel.max_drawdown = max_drawdown
                channel.sharpe_ratio = sharpe_ratio
                channel.score = round(score, 2)
                channel.category = category
                channel.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info("✅ Updated channel statistics, categories, and scores")
        except Exception as e:
            logger.error(f"Error updating channel statistics: {e}")
            self.db.rollback()
    
    def get_recent_signals(self, channel_id: Optional[int] = None, limit: int = 50) -> List[Signal]:
        """Get recent signals from database"""
        
        try:
            query = self.db.query(Signal)
            
            if channel_id:
                query = query.filter(Signal.channel_id == channel_id)
            
            signals = query.order_by(desc(Signal.timestamp)).limit(limit).all()
            return signals
            
        except Exception as e:
            logger.error(f"Error getting recent signals: {e}")
            return []
    
    def get_channel_statistics(self, channel_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a channel"""
        
        try:
            channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
            if not channel:
                return {"error": "Channel not found"}
            
            # Get signal statistics
            total_signals = self.db.query(Signal).filter(Signal.channel_id == channel_id).count()
            successful_signals = self.db.query(Signal).filter(
                Signal.channel_id == channel_id,
                Signal.is_successful == True
            ).count()
            
            pending_signals = self.db.query(Signal).filter(
                Signal.channel_id == channel_id,
                Signal.status == 'PENDING'
            ).count()
            
            # Get recent signals for analysis
            recent_signals = self.get_recent_signals(channel_id, 20)
            
            return {
                "channel_name": channel.name,
                "channel_url": channel.url,
                "total_signals": total_signals,
                "successful_signals": successful_signals,
                "pending_signals": pending_signals,
                "accuracy_percentage": channel.accuracy,
                "recent_signals_count": len(recent_signals),
                "is_active": channel.is_active,
                "last_updated": channel.updated_at.isoformat() if channel.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting channel statistics: {e}")
            return {"error": str(e)}

# Background task functions
async def collect_telegram_signals(db: Session) -> Dict[str, Any]:
    """Background task to collect Telegram signals"""
    service = BackendTelegramService(db)
    return await service.collect_signals_from_channels()

async def get_channel_signals(db: Session, channel_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
    """Get channel signals as dictionaries"""
    service = BackendTelegramService(db)
    signals = service.get_recent_signals(channel_id, limit)
    
    return [
        {
            "id": signal.id,
            "symbol": signal.symbol,
            "direction": signal.direction,
            "entry_price": float(signal.entry_price),
            "targets": [float(signal.tp1_price) if signal.tp1_price else None,
                       float(signal.tp2_price) if signal.tp2_price else None,
                       float(signal.tp3_price) if signal.tp3_price else None],
            "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
            "confidence_score": float(signal.confidence_score) if signal.confidence_score else 0.0,
            "status": signal.status,
            "timestamp": signal.timestamp.isoformat() if signal.timestamp else None,
            "channel_name": signal.channel.name if signal.channel else "Unknown"
        }
        for signal in signals
    ] 