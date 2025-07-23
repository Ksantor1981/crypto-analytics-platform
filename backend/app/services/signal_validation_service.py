"""
Signal Validation Service - Real signal tracking and validation
Part of Task 3.1.1: Система реального отслеживания сигналов
"""
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.signal import Signal, SignalStatus
from ..models.channel import Channel

logger = logging.getLogger(__name__)

class SignalValidationService:
    """
    Service for validating and tracking crypto trading signals
    Core business logic: Real signal performance tracking
    """
    
    def __init__(self):
        self.signal_patterns = {
            'buy_patterns': [
                r'(?i)buy\s+(\w+)',
                r'(?i)long\s+(\w+)',
                r'(?i)entry\s*:?\s*(\w+)',
                r'(?i)(\w+)\s+buy',
                r'(?i)(\w+)\s+long'
            ],
            'sell_patterns': [
                r'(?i)sell\s+(\w+)',
                r'(?i)short\s+(\w+)',
                r'(?i)exit\s*:?\s*(\w+)',
                r'(?i)(\w+)\s+sell',
                r'(?i)(\w+)\s+short'
            ],
            'price_patterns': [
                r'(?i)entry\s*:?\s*\$?([0-9]+\.?[0-9]*)',
                r'(?i)price\s*:?\s*\$?([0-9]+\.?[0-9]*)',
                r'(?i)at\s+\$?([0-9]+\.?[0-9]*)',
                r'(?i)\$([0-9]+\.?[0-9]*)'
            ],
            'target_patterns': [
                r'(?i)tp\s*1?\s*:?\s*\$?([0-9]+\.?[0-9]*)',
                r'(?i)target\s*1?\s*:?\s*\$?([0-9]+\.?[0-9]*)',
                r'(?i)take\s*profit\s*1?\s*:?\s*\$?([0-9]+\.?[0-9]*)',
                r'(?i)tp1\s*:?\s*\$?([0-9]+\.?[0-9]*)'
            ],
            'stop_loss_patterns': [
                r'(?i)sl\s*:?\s*\$?([0-9]+\.?[0-9]*)',
                r'(?i)stop\s*loss\s*:?\s*\$?([0-9]+\.?[0-9]*)',
                r'(?i)stop\s*:?\s*\$?([0-9]+\.?[0-9]*)'
            ]
        }
        
        # Common crypto symbols
        self.crypto_symbols = {
            'BTC', 'ETH', 'BNB', 'ADA', 'XRP', 'SOL', 'DOT', 'DOGE', 'AVAX', 'LUNA',
            'LINK', 'UNI', 'LTC', 'BCH', 'ALGO', 'VET', 'ICP', 'FIL', 'TRX', 'ETC',
            'XLM', 'THETA', 'ATOM', 'NEAR', 'HBAR', 'EGLD', 'MANA', 'SAND', 'AXS',
            'SHIB', 'MATIC', 'FTM', 'CRO', 'AAVE', 'GRT', 'ENJ', 'CHZ', 'SUSHI'
        }
    
    async def parse_and_validate_signal(
        self,
        message: str,
        channel_id: str,
        db: Session,
        author: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Parse message and extract trading signal information
        
        Args:
            message: Raw message text
            channel_id: Channel ID where signal was posted
            db: Database session
            author: Message author
        
        Returns:
            Parsed signal data or None if no valid signal found
        """
        try:
            # Extract signal components
            signal_type = self._extract_signal_type(message)
            if not signal_type:
                return None
            
            symbol = self._extract_symbol(message)
            if not symbol:
                return None
            
            entry_price = self._extract_entry_price(message)
            target_prices = self._extract_target_prices(message)
            stop_loss = self._extract_stop_loss(message)
            
            # Calculate confidence based on signal completeness
            confidence = self._calculate_signal_confidence(
                signal_type, symbol, entry_price, target_prices, stop_loss, message
            )
            
            # Validate signal logic
            if not self._validate_signal_logic(signal_type, entry_price, target_prices, stop_loss):
                logger.warning(f"Invalid signal logic for {symbol} {signal_type}")
                return None
            
            signal_data = {
                'symbol': symbol,
                'signal_type': signal_type,
                'entry_price': entry_price,
                'target_price': target_prices[0] if target_prices else None,
                'target_prices': target_prices,
                'stop_loss': stop_loss,
                'confidence': confidence,
                'raw_message': message,
                'channel_id': channel_id,
                'author': author,
                'status': SignalStatus.PENDING,
                'created_at': datetime.utcnow(),
                'validation_notes': self._generate_validation_notes(message)
            }
            
            logger.info(f"Signal parsed: {symbol} {signal_type} @ {entry_price} (confidence: {confidence:.3f})")
            return signal_data
            
        except Exception as e:
            logger.error(f"Error parsing signal: {e}")
            return None
    
    async def create_validated_signal(
        self,
        signal_data: Dict[str, Any],
        db: Session
    ) -> Optional[Signal]:
        """
        Create and save validated signal to database
        """
        try:
            # Check for duplicate signals (same symbol, type, price within 5 minutes)
            existing_signal = await self._check_duplicate_signal(signal_data, db)
            if existing_signal:
                logger.info(f"Duplicate signal detected, skipping: {signal_data['symbol']}")
                return existing_signal
            
            # Create signal object
            signal = Signal(
                channel_id=signal_data['channel_id'],
                symbol=signal_data['symbol'],
                signal_type=signal_data['signal_type'],
                entry_price=signal_data['entry_price'],
                target_price=signal_data['target_price'],
                stop_loss=signal_data['stop_loss'],
                confidence=signal_data['confidence'],
                raw_message=signal_data['raw_message'],
                author=signal_data.get('author'),
                status=SignalStatus.PENDING,
                source_channel=signal_data.get('source_channel', 'telegram')
            )
            
            db.add(signal)
            db.commit()
            db.refresh(signal)
            
            logger.info(f"Signal created: ID {signal.id} - {signal.symbol} {signal.signal_type}")
            return signal
            
        except Exception as e:
            logger.error(f"Error creating signal: {e}")
            db.rollback()
            return None
    
    async def update_signal_status(
        self,
        signal: Signal,
        new_status: SignalStatus,
        db: Session,
        execution_price: Optional[float] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update signal status and calculate performance metrics
        """
        try:
            old_status = signal.status
            signal.status = new_status
            signal.updated_at = datetime.utcnow()
            
            if execution_price:
                signal.execution_price = execution_price
                
                # Calculate ROI
                if signal.entry_price and execution_price:
                    if signal.signal_type == 'buy':
                        roi = ((execution_price - signal.entry_price) / signal.entry_price) * 100
                    else:  # sell/short
                        roi = ((signal.entry_price - execution_price) / signal.entry_price) * 100
                    
                    signal.roi_percentage = roi
            
            if notes:
                signal.validation_notes = notes
            
            db.commit()
            
            logger.info(f"Signal {signal.id} status updated: {old_status} -> {new_status}")
            
            # Update channel performance metrics
            await self._update_channel_metrics(signal.channel_id, db)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating signal status: {e}")
            db.rollback()
            return False
    
    def _extract_signal_type(self, message: str) -> Optional[str]:
        """Extract signal type (buy/sell) from message"""
        message_lower = message.lower()
        
        # Check for buy patterns
        for pattern in self.signal_patterns['buy_patterns']:
            if re.search(pattern, message):
                return 'buy'
        
        # Check for sell patterns
        for pattern in self.signal_patterns['sell_patterns']:
            if re.search(pattern, message):
                return 'sell'
        
        # Fallback: look for keywords
        buy_keywords = ['buy', 'long', 'bullish', 'call']
        sell_keywords = ['sell', 'short', 'bearish', 'put']
        
        for keyword in buy_keywords:
            if keyword in message_lower:
                return 'buy'
        
        for keyword in sell_keywords:
            if keyword in message_lower:
                return 'sell'
        
        return None
    
    def _extract_symbol(self, message: str) -> Optional[str]:
        """Extract cryptocurrency symbol from message"""
        # Look for known crypto symbols
        words = re.findall(r'\b[A-Z]{2,10}\b', message.upper())
        
        for word in words:
            if word in self.crypto_symbols:
                return word
            
            # Check for common patterns like BTCUSDT -> BTC
            if word.endswith('USDT') and len(word) > 4:
                base_symbol = word[:-4]
                if base_symbol in self.crypto_symbols:
                    return base_symbol
            
            if word.endswith('USD') and len(word) > 3:
                base_symbol = word[:-3]
                if base_symbol in self.crypto_symbols:
                    return base_symbol
        
        # Look for $ symbol patterns
        dollar_pattern = r'\$([A-Z]{2,10})'
        matches = re.findall(dollar_pattern, message.upper())
        for match in matches:
            if match in self.crypto_symbols:
                return match
        
        return None
    
    def _extract_entry_price(self, message: str) -> Optional[float]:
        """Extract entry price from message"""
        for pattern in self.signal_patterns['price_patterns']:
            matches = re.findall(pattern, message)
            if matches:
                try:
                    return float(matches[0])
                except ValueError:
                    continue
        
        return None
    
    def _extract_target_prices(self, message: str) -> List[float]:
        """Extract target prices from message"""
        targets = []
        
        for pattern in self.signal_patterns['target_patterns']:
            matches = re.findall(pattern, message)
            for match in matches:
                try:
                    targets.append(float(match))
                except ValueError:
                    continue
        
        # Look for multiple targets (TP1, TP2, TP3)
        tp_pattern = r'(?i)tp([1-3])\s*:?\s*\$?([0-9]+\.?[0-9]*)'
        tp_matches = re.findall(tp_pattern, message)
        
        for tp_num, price in tp_matches:
            try:
                targets.append(float(price))
            except ValueError:
                continue
        
        return sorted(set(targets))  # Remove duplicates and sort
    
    def _extract_stop_loss(self, message: str) -> Optional[float]:
        """Extract stop loss price from message"""
        for pattern in self.signal_patterns['stop_loss_patterns']:
            matches = re.findall(pattern, message)
            if matches:
                try:
                    return float(matches[0])
                except ValueError:
                    continue
        
        return None
    
    def _calculate_signal_confidence(
        self,
        signal_type: str,
        symbol: str,
        entry_price: Optional[float],
        target_prices: List[float],
        stop_loss: Optional[float],
        message: str
    ) -> float:
        """
        Calculate signal confidence based on completeness and quality
        """
        confidence = 0.3  # Base confidence
        
        # Signal type identified
        if signal_type:
            confidence += 0.2
        
        # Symbol identified
        if symbol and symbol in self.crypto_symbols:
            confidence += 0.2
        
        # Entry price provided
        if entry_price:
            confidence += 0.15
        
        # Target prices provided
        if target_prices:
            confidence += 0.1
            if len(target_prices) > 1:
                confidence += 0.05  # Multiple targets
        
        # Stop loss provided
        if stop_loss:
            confidence += 0.1
        
        # Message quality indicators
        if len(message) > 50:  # Detailed message
            confidence += 0.05
        
        if any(word in message.lower() for word in ['analysis', 'chart', 'support', 'resistance']):
            confidence += 0.05  # Technical analysis mentioned
        
        # Risk management indicators
        if stop_loss and entry_price:
            risk_ratio = abs(stop_loss - entry_price) / entry_price
            if 0.02 <= risk_ratio <= 0.1:  # Reasonable risk (2-10%)
                confidence += 0.05
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _validate_signal_logic(
        self,
        signal_type: str,
        entry_price: Optional[float],
        target_prices: List[float],
        stop_loss: Optional[float]
    ) -> bool:
        """
        Validate signal logic (targets above/below entry for buy/sell)
        """
        if not entry_price or not target_prices:
            return True  # Can't validate without prices
        
        if signal_type == 'buy':
            # For buy signals, targets should be above entry, stop loss below
            for target in target_prices:
                if target <= entry_price:
                    return False
            
            if stop_loss and stop_loss >= entry_price:
                return False
        
        elif signal_type == 'sell':
            # For sell signals, targets should be below entry, stop loss above
            for target in target_prices:
                if target >= entry_price:
                    return False
            
            if stop_loss and stop_loss <= entry_price:
                return False
        
        return True
    
    def _generate_validation_notes(self, message: str) -> str:
        """Generate validation notes for the signal"""
        notes = []
        
        if len(message) < 20:
            notes.append("Short message - limited context")
        
        if not re.search(r'[0-9]+\.?[0-9]*', message):
            notes.append("No numerical values found")
        
        technical_terms = ['support', 'resistance', 'breakout', 'reversal', 'trend']
        if any(term in message.lower() for term in technical_terms):
            notes.append("Technical analysis mentioned")
        
        return "; ".join(notes) if notes else "Standard signal validation"
    
    async def _check_duplicate_signal(
        self,
        signal_data: Dict[str, Any],
        db: Session
    ) -> Optional[Signal]:
        """Check for duplicate signals within 5 minutes"""
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        
        existing = db.query(Signal).filter(
            and_(
                Signal.channel_id == signal_data['channel_id'],
                Signal.symbol == signal_data['symbol'],
                Signal.signal_type == signal_data['signal_type'],
                Signal.created_at >= five_minutes_ago
            )
        ).first()
        
        return existing
    
    async def _update_channel_metrics(self, channel_id: str, db: Session):
        """Update channel performance metrics after signal status change"""
        try:
            # Get channel
            channel = db.query(Channel).filter(Channel.id == channel_id).first()
            if not channel:
                return
            
            # Calculate metrics
            total_signals = db.query(Signal).filter(Signal.channel_id == channel_id).count()
            
            completed_signals = db.query(Signal).filter(
                Signal.channel_id == channel_id,
                Signal.status.in_([SignalStatus.COMPLETED, SignalStatus.STOPPED])
            ).all()
            
            if completed_signals:
                successful_signals = [s for s in completed_signals if s.roi_percentage and s.roi_percentage > 0]
                accuracy = len(successful_signals) / len(completed_signals) * 100
                avg_roi = sum(s.roi_percentage for s in completed_signals if s.roi_percentage) / len(completed_signals)
            else:
                accuracy = 0
                avg_roi = 0
            
            # Update channel metrics (would need to add these fields to Channel model)
            # channel.total_signals = total_signals
            # channel.accuracy_percentage = accuracy
            # channel.average_roi = avg_roi
            # channel.last_signal_at = datetime.utcnow()
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating channel metrics: {e}")


# Global signal validation service instance
signal_validation_service = SignalValidationService()
