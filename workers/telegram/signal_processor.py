"""
Signal Processor for Telegram signals
Handles saving signals to database and processing them
"""
import logging
import sys
import os
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

try:
    from sqlalchemy.orm import Session
    from app.database import get_db
    from app.models.signal import Signal
    from app.models.channel import Channel
    from app.models.user import User
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False
    print("Warning: Backend models not available, signals won't be saved to database")

logger = logging.getLogger(__name__)

class TelegramSignalProcessor:
    """
    Processes Telegram signals and saves them to database
    """
    
    def __init__(self):
        self.backend_available = BACKEND_AVAILABLE
        
    def get_or_create_channel(self, db: Session, channel_name: str, channel_id: int = None) -> int:
        """Get or create channel in database"""
        try:
            # Try to find existing channel
            channel = db.query(Channel).filter(
                Channel.name == channel_name
            ).first()
            
            if not channel:
                # Create new channel
                channel = Channel(
                    name=channel_name,
                    platform="telegram",
                    url=f"https://t.me/{channel_name.lower().replace(' ', '_')}",
                    category="crypto",
                    is_active=True,
                    created_at=datetime.now()
                )
                db.add(channel)
                db.commit()
                db.refresh(channel)
                logger.info(f"Created new channel: {channel_name}")
            
            return channel.id
            
        except Exception as e:
            logger.error(f"Error getting/creating channel {channel_name}: {e}")
            db.rollback()
            return None

    def convert_signal_to_db_format(self, signal_data: Dict, channel_id: int) -> Dict:
        """Convert Telegram signal to database format"""
        try:
            # Map direction
            direction_map = {
                'LONG': 'BUY',
                'SHORT': 'SELL'
            }
            
            db_signal = {
                'channel_id': channel_id,
                'asset': signal_data.get('asset'),
                'direction': direction_map.get(signal_data.get('direction'), 'BUY'),
                'entry_price': float(signal_data.get('entry_price', 0)),
                'tp1_price': float(signal_data.get('tp1_price', 0)) if signal_data.get('tp1_price') else None,
                'tp2_price': float(signal_data.get('tp2_price', 0)) if signal_data.get('tp2_price') else None,
                'tp3_price': float(signal_data.get('tp3_price', 0)) if signal_data.get('tp3_price') else None,
                'stop_loss': float(signal_data.get('stop_loss', 0)) if signal_data.get('stop_loss') else None,
                'leverage': signal_data.get('leverage'),
                'original_message': signal_data.get('original_text', ''),
                'message_timestamp': signal_data.get('message_timestamp', datetime.now()),
                'confidence_score': signal_data.get('confidence', 0.0),
                'status': 'PENDING',
                'created_at': datetime.now()
            }
            
            return db_signal
            
        except Exception as e:
            logger.error(f"Error converting signal to DB format: {e}")
            return None

    def save_signal_to_db(self, db: Session, signal_data: Dict, channel_id: int) -> bool:
        """Save a single signal to database"""
        try:
            db_signal_data = self.convert_signal_to_db_format(signal_data, channel_id)
            if not db_signal_data:
                return False
                
            # Check if signal already exists (avoid duplicates)
            existing_signal = db.query(Signal).filter(
                Signal.channel_id == channel_id,
                Signal.asset == db_signal_data['asset'],
                Signal.entry_price == db_signal_data['entry_price'],
                Signal.message_timestamp == db_signal_data['message_timestamp']
            ).first()
            
            if existing_signal:
                logger.debug(f"Signal already exists: {db_signal_data['asset']}")
                return False
                
            # Create new signal
            signal = Signal(**db_signal_data)
            db.add(signal)
            db.commit()
            db.refresh(signal)
            
            logger.info(f"Saved signal: {signal.asset} {signal.direction} at {signal.entry_price}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving signal to database: {e}")
            db.rollback()
            return False

    def process_signals(self, signals_data: List[Dict]) -> Dict[str, Any]:
        """Process and save multiple signals to database"""
        if not self.backend_available:
            logger.warning("Backend not available, cannot save signals to database")
            return {
                "status": "warning",
                "message": "Backend not available",
                "processed": 0,
                "saved": 0,
                "errors": 0
            }
            
        processed = 0
        saved = 0
        errors = 0
        
        try:
            # Get database session
            db = next(get_db())
            
            for signal_data in signals_data:
                processed += 1
                
                try:
                    # Get or create channel
                    channel_name = signal_data.get('channel_name', 'Unknown Channel')
                    channel_id = self.get_or_create_channel(
                        db, 
                        channel_name,
                        signal_data.get('channel_id')
                    )
                    
                    if not channel_id:
                        errors += 1
                        continue
                        
                    # Save signal
                    if self.save_signal_to_db(db, signal_data, channel_id):
                        saved += 1
                    else:
                        errors += 1
                        
                except Exception as e:
                    logger.error(f"Error processing signal: {e}")
                    errors += 1
                    
            db.close()
            
        except Exception as e:
            logger.error(f"Error in signal processing: {e}")
            errors = processed
            
        return {
            "status": "success" if errors == 0 else "partial",
            "processed": processed,
            "saved": saved,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }

    def validate_signal(self, signal_data: Dict) -> bool:
        """Validate signal data before processing"""
        required_fields = ['asset', 'direction', 'entry_price']
        
        for field in required_fields:
            if not signal_data.get(field):
                logger.warning(f"Signal missing required field: {field}")
                return False
                
        # Validate entry price
        try:
            entry_price = float(signal_data.get('entry_price', 0))
            if entry_price <= 0:
                logger.warning("Invalid entry price")
                return False
        except (ValueError, TypeError):
            logger.warning("Entry price is not a valid number")
            return False
            
        # Validate direction
        if signal_data.get('direction') not in ['LONG', 'SHORT', 'BUY', 'SELL']:
            logger.warning(f"Invalid direction: {signal_data.get('direction')}")
            return False
            
        return True

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        if not self.backend_available:
            return {"status": "backend_unavailable"}
            
        try:
            db = next(get_db())
            
            # Get recent signals count
            today_signals = db.query(Signal).filter(
                Signal.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
            ).count()
            
            # Get pending signals
            pending_signals = db.query(Signal).filter(
                Signal.status == 'PENDING'
            ).count()
            
            # Get active channels
            active_channels = db.query(Channel).filter(
                Channel.is_active == True,
                Channel.platform == 'telegram'
            ).count()
            
            db.close()
            
            return {
                "status": "success",
                "today_signals": today_signals,
                "pending_signals": pending_signals,
                "active_channels": active_channels,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            return {"status": "error", "message": str(e)}

# Global processor instance
signal_processor = TelegramSignalProcessor() 