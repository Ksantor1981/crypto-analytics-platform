"""
Migrated Enhanced Signal Extractor from analyst_crypto
Адаптирован под новую архитектуру с Pydantic validation
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

class ExtractedSignal(BaseModel):
    """Pydantic модель для извлеченного сигнала"""
    asset: str = Field(..., description="Торговая пара (BTC, ETH, etc.)")
    direction: str = Field(..., description="Направление (LONG/SHORT/BUY/SELL)")
    entry_price: Optional[float] = Field(None, description="Цена входа")
    target_price: Optional[float] = Field(None, description="Целевая цена")
    stop_loss: Optional[float] = Field(None, description="Стоп-лосс")
    leverage: Optional[float] = Field(None, description="Плечо")
    time_horizon: Optional[str] = Field(None, description="Временной горизонт")
    confidence_score: float = Field(50.0, description="Уверенность в сигнале (0-100)")
    original_text: str = Field(..., description="Исходный текст")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('direction')
    def validate_direction(cls, v):
        valid_directions = ['LONG', 'SHORT', 'BUY', 'SELL', 'CALL', 'PUT']
        if v.upper() not in valid_directions:
            raise ValueError(f'Invalid direction: {v}')
        return v.upper()
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Confidence score must be between 0 and 100')
        return v

class MigratedSignalExtractor:
    """
    Мигрированный Enhanced Signal Extractor
    Адаптирован под новую архитектуру с Pydantic validation
    """
    
    def __init__(self):
        """Initialize extractor with RegEx patterns from analyst_crypto"""
        
        # RegEx patterns from analyst_crypto
        self.regex_patterns = {
            'entry': [
                r'entry[:\s@]+\$?(\d+[\d,]*\.?\d*)',           # entry: $45,000
                r'buy[:\s@]+\$?(\d+[\d,]*\.?\d*)',             # buy @ $45000
                r'enter[:\s@]+\$?(\d+[\d,]*\.?\d*)',           # enter @ 45k
                r'(?:entry|buy)\s*[@:]\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)',  # entry @ $45,000
                r'(?:long|call)\s*[@:]\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)',   # long @ 45000
                r'Entry[:\s]+(\d+\.?\d*)',                     # Entry: 45000
                r'📍[:\s]*(\d+\.?\d*)',                        # 📍 45000
            ],
            
            'target': [
                r'target[:\s@]+\$?(\d+[\d,]*\.?\d*)',          # target: $48,000
                r'tp[:\s@]+\$?(\d+[\d,]*\.?\d*)',              # TP: 48000
                r'take\s*profit[:\s@]+\$?(\d+[\d,]*\.?\d*)',   # take profit: 48k
                r'tp[1-3]?[:\s@]+\$?(\d+[\d,]*\.?\d*)',        # TP1: 48000
                r'targets?[:\s@]+\$?(\d+[\d,]*\.?\d*)',        # targets: 48,52
                r'🎯[:\s]*(\d+\.?\d*)',                        # 🎯 48000
            ],
            
            'stop_loss': [
                r'stop[\s-]*loss[:\s@]+\$?(\d+[\d,]*\.?\d*)',  # stop-loss: $42,000
                r'sl[:\s@]+\$?(\d+[\d,]*\.?\d*)',              # SL: 42000
                r'stop[:\s@]+\$?(\d+[\d,]*\.?\d*)',            # stop: 42k
                r'stoploss[:\s@]+\$?(\d+[\d,]*\.?\d*)',        # stoploss: 42000
                r'🛑[:\s]*(\d+\.?\d*)',                        # 🛑 42000
            ],
            
            'asset': [
                r'(BTC|bitcoin)',                              # BTC or bitcoin
                r'(ETH|ethereum)',                             # ETH or ethereum  
                r'(SOL|solana)',                               # SOL or solana
                r'(DOGE|dogecoin)',                            # DOGE or dogecoin
                r'(ADA|cardano)',                              # ADA or cardano
                r'(XRP|ripple)',                               # XRP or ripple
                r'(\b[A-Z]{2,5}\b)(?:/USDT?)?',               # Any crypto symbol
                r'(\b[A-Z]{2,5}USDT\b)',                      # BTCUSDT, ETHUSDT
            ],
            
            'signal_type': [
                r'(BUY|LONG|CALL)',                            # Buy signals
                r'(SELL|SHORT|PUT)',                           # Sell signals
                r'🚀',                                         # 🚀 (bullish)
                r'📈',                                         # 📈 (bullish)
                r'📉',                                         # 📉 (bearish)
                r'🔻',                                         # 🔻 (bearish)
            ],
            
            'leverage': [
                r'leverage[:\s]*(\d+(?:\.\d+)?)[x\s]?',        # leverage: 3x
                r'lev[:\s]*(\d+(?:\.\d+)?)[x\s]?',             # lev: 5x
                r'(\d+)x\s*leverage',                          # 3x leverage
            ],
            
            'time_horizon': [
                r'(\d+)[-\s]*(?:days?|d)',                     # 2-5 days
                r'(\d+)[-\s]*(?:hours?|h)',                    # 24 hours
                r'(\d+)[-\s]*(?:weeks?|w)',                    # 1 week
            ]
        }
        
        # Crypto asset mapping from analyst_crypto
        self.asset_mapping = {
            'bitcoin': 'BTC',
            'ethereum': 'ETH', 
            'solana': 'SOL',
            'dogecoin': 'DOGE',
            'cardano': 'ADA',
            'ripple': 'XRP'
        }
        
        logger.info("✅ Migrated Signal Extractor инициализирован")
    
    def extract_from_text(self, text: str) -> List[ExtractedSignal]:
        """
        MAIN EXTRACTION METHOD using RegEx patterns
        
        Args:
            text: Signal text to extract from
            
        Returns:
            List of extracted trading signals with Pydantic validation
        """
        try:
            signals = []
            
            # 1. Extract crypto asset
            asset = self._extract_asset(text)
            if not asset:
                logger.debug(f"❌ Не найден актив в тексте: {text[:100]}...")
                return []
            
            # 2. Extract signal direction
            direction = self._extract_signal_type(text)
            if not direction:
                logger.debug(f"❌ Не найден тип сигнала в тексте: {text[:100]}...")
                return []
            
            # 3. Extract prices
            entry_price = self._extract_price(text, 'entry')
            target_price = self._extract_price(text, 'target')
            stop_loss = self._extract_price(text, 'stop_loss')
            
            # 4. Extract additional info
            leverage = self._extract_leverage(text)
            time_horizon = self._extract_time_horizon(text)
            
            # 5. Calculate confidence
            confidence_score = self._calculate_confidence(text, asset, direction)
            
            # 6. Create signal with validation
            try:
                signal = ExtractedSignal(
                    asset=asset,
                    direction=direction,
                    entry_price=entry_price,
                    target_price=target_price,
                    stop_loss=stop_loss,
                    leverage=leverage,
                    time_horizon=time_horizon,
                    confidence_score=confidence_score,
                    original_text=text
                )
                signals.append(signal)
                logger.info(f"✅ Извлечен сигнал: {asset} {direction} Entry: {entry_price} Target: {target_price}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка валидации сигнала: {e}")
            
            return signals
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения сигнала: {e}")
            return []
    
    def _extract_asset(self, text: str) -> Optional[str]:
        """Extract crypto asset from text"""
        for pattern in self.regex_patterns['asset']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                asset = match.group(1).upper()
                # Map full names to symbols
                if asset.lower() in self.asset_mapping:
                    return self.asset_mapping[asset.lower()]
                return asset
        return None
    
    def _extract_signal_type(self, text: str) -> Optional[str]:
        """Extract signal direction from text"""
        # Check for emoji indicators first
        if '🚀' in text or '📈' in text:
            return 'LONG'
        if '📉' in text or '🔻' in text:
            return 'SHORT'
        
        # Check for text patterns
        for pattern in self.regex_patterns['signal_type']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                signal_type = match.group(1).upper()
                # Normalize to LONG/SHORT
                if signal_type in ['BUY', 'CALL']:
                    return 'LONG'
                elif signal_type in ['SELL', 'PUT']:
                    return 'SHORT'
                return signal_type
        return None
    
    def _extract_price(self, text: str, price_type: str) -> Optional[float]:
        """Extract price from text"""
        patterns = self.regex_patterns.get(price_type, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    return float(price_str)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_leverage(self, text: str) -> Optional[float]:
        """Extract leverage from text"""
        for pattern in self.regex_patterns['leverage']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, TypeError):
                    continue
        return None
    
    def _extract_time_horizon(self, text: str) -> Optional[str]:
        """Extract time horizon from text"""
        for pattern in self.regex_patterns['time_horizon']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def _calculate_confidence(self, text: str, asset: str, direction: str) -> float:
        """Calculate confidence score for extracted signal"""
        confidence = 50.0  # Base confidence
        
        # Increase confidence for having key elements
        if self._extract_price(text, 'entry'):
            confidence += 15
        if self._extract_price(text, 'target'):
            confidence += 15
        if self._extract_price(text, 'stop_loss'):
            confidence += 10
        
        # Increase for having asset and direction
        if asset:
            confidence += 10
        if direction:
            confidence += 10
        
        # Increase for having leverage info
        if self._extract_leverage(text):
            confidence += 5
        
        # Increase for having time horizon
        if self._extract_time_horizon(text):
            confidence += 5
        
        return min(100.0, confidence)
    
    def extract_multiple_signals(self, text: str) -> List[ExtractedSignal]:
        """
        Extract multiple signals from a single text
        Useful for messages with multiple trading pairs
        """
        signals = []
        
        # Split text by common separators
        text_parts = re.split(r'[;\n\r]+', text)
        
        for part in text_parts:
            part = part.strip()
            if part:
                part_signals = self.extract_from_text(part)
                signals.extend(part_signals)
        
        return signals
    
    def validate_signal(self, signal: ExtractedSignal) -> bool:
        """
        Additional validation for extracted signal
        """
        try:
            # Check if we have minimum required fields
            if not signal.asset or not signal.direction:
                return False
            
            # Check if prices make sense
            if signal.entry_price and signal.target_price:
                if signal.direction == 'LONG' and signal.target_price <= signal.entry_price:
                    logger.warning(f"⚠️ LONG signal with target <= entry: {signal.asset}")
                elif signal.direction == 'SHORT' and signal.target_price >= signal.entry_price:
                    logger.warning(f"⚠️ SHORT signal with target >= entry: {signal.asset}")
            
            # Check if stop loss makes sense
            if signal.entry_price and signal.stop_loss:
                if signal.direction == 'LONG' and signal.stop_loss >= signal.entry_price:
                    logger.warning(f"⚠️ LONG signal with stop loss >= entry: {signal.asset}")
                elif signal.direction == 'SHORT' and signal.stop_loss <= signal.entry_price:
                    logger.warning(f"⚠️ SHORT signal with stop loss <= entry: {signal.asset}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка валидации сигнала: {e}")
            return False

def test_extractor():
    """Test function for the migrated extractor"""
    extractor = MigratedSignalExtractor()
    
    test_texts = [
        "🚀 BTC LONG Entry: $45,000 Target: $48,000 SL: $42,000",
        "ETH SHORT @ 3200 TP: 3000 SL: 3300",
        "SOL/USDT BUY Entry: 100 Target: 120 Stop Loss: 95",
        "📈 Bitcoin Long Entry: 45000 Target: 48000 Stop: 42000",
        "📉 Ethereum Short @ 3200 TP: 3000 SL: 3300"
    ]
    
    for text in test_texts:
        print(f"\n📝 Тестируем текст: {text}")
        signals = extractor.extract_from_text(text)
        
        for signal in signals:
            print(f"✅ Извлечен сигнал: {signal.asset} {signal.direction}")
            print(f"   Entry: {signal.entry_price}, Target: {signal.target_price}, SL: {signal.stop_loss}")
            print(f"   Confidence: {signal.confidence_score}%")

if __name__ == "__main__":
    test_extractor()
