"""
Enhanced Signal Parsing Patterns
Advanced pattern recognition for crypto trading signals with multi-language support
"""
import re
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Types of trading signals"""
    SPOT = "spot"
    FUTURES = "futures"
    MARGIN = "margin"
    OPTIONS = "options"
    ANALYSIS = "analysis"
    WHALE_MOVE = "whale_move"

class Direction(Enum):
    """Trading directions"""
    LONG = "LONG"
    SHORT = "SHORT"
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class ParsedSignal:
    """Structured representation of a parsed signal"""
    asset: str
    direction: Direction
    entry_price: Decimal
    targets: List[Decimal]
    stop_loss: Optional[Decimal]
    leverage: Optional[int]
    signal_type: SignalType
    confidence: float
    raw_text: str
    metadata: Dict[str, Any]

class EnhancedSignalPatterns:
    """Enhanced signal pattern recognition system"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.validators = self._initialize_validators()
        self.confidence_factors = self._initialize_confidence_factors()
        
    def _initialize_patterns(self) -> Dict[str, Dict[str, re.Pattern]]:
        """Initialize comprehensive pattern dictionary"""
        
        patterns = {
            # Asset patterns (multi-format support)
            'assets': {
                'standard': re.compile(r'\b([A-Z]{2,6}/?[A-Z]{2,6})\b', re.IGNORECASE),
                'with_slash': re.compile(r'\b([A-Z]{2,6}/[A-Z]{2,6})\b', re.IGNORECASE),
                'concatenated': re.compile(r'\b([A-Z]{3,8}USDT?|[A-Z]{3,8}BTC|[A-Z]{3,8}ETH)\b', re.IGNORECASE),
                'hashtag': re.compile(r'#([A-Z]{2,6})', re.IGNORECASE),
                'dollar_sign': re.compile(r'\$([A-Z]{2,6})', re.IGNORECASE)
            },
            
            # Direction patterns (multi-language)
            'directions': {
                'english_long': re.compile(r'\b(long|buy|bullish|up|call)\b', re.IGNORECASE),
                'english_short': re.compile(r'\b(short|sell|bearish|down|put)\b', re.IGNORECASE),
                'symbols_long': re.compile(r'[📈⬆️🔥🚀💚🟢]'),
                'symbols_short': re.compile(r'[📉⬇️❄️💥❌🔴]'),
                'arrows_long': re.compile(r'[↗️⬆️🔺]'),
                'arrows_short': re.compile(r'[↘️⬇️🔻]')
            },
            
            # Entry price patterns
            'entry_prices': {
                'standard': re.compile(r'(?:entry|enter|price|@)[:\s]*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE),
                'at_symbol': re.compile(r'@\s*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE),
                'current': re.compile(r'(?:current|now|market)[:\s]*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE),
                'range': re.compile(r'(?:entry|enter)[:\s]*\$?([0-9]+,?[0-9]*\.?[0-9]*)\s*-\s*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE),
                'around': re.compile(r'(?:around|near|about)[:\s]*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE)
            },
            
            # Target patterns (multiple targets)
            'targets': {
                'numbered': re.compile(r'(?:tp|target|t)\s*([1-5])[:\s]*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE),
                'standard': re.compile(r'(?:tp|target|take\s*profit)[:\s]*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE),
                'percentage': re.compile(r'(?:tp|target)[:\s]*\+?([0-9]+\.?[0-9]*)%', re.IGNORECASE),
                'multiple': re.compile(r'(?:targets?)[:\s]*([0-9]+,?[0-9]*\.?[0-9]*(?:\s*[,\s]\s*[0-9]+,?[0-9]*\.?[0-9]*)*)', re.IGNORECASE),
                'range': re.compile(r'(?:tp|target)[:\s]*\$?([0-9]+,?[0-9]*\.?[0-9]*)\s*-\s*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE)
            },
            
            # Stop loss patterns
            'stop_loss': {
                'standard': re.compile(r'(?:sl|stop\s*loss|stop)[:\s]*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE),
                'percentage': re.compile(r'(?:sl|stop)[:\s]*-?([0-9]+\.?[0-9]*)%', re.IGNORECASE),
                'below': re.compile(r'(?:below|under)[:\s]*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE),
                'above': re.compile(r'(?:above|over)[:\s]*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE),
                'cutloss': re.compile(r'(?:cut\s*loss|cutloss)[:\s]*\$?([0-9]+,?[0-9]*\.?[0-9]*)', re.IGNORECASE)
            },
            
            # Leverage patterns
            'leverage': {
                'standard': re.compile(r'(?:leverage|lev)[:\s]*([0-9]+)x?', re.IGNORECASE),
                'cross': re.compile(r'(?:cross|isolated)[:\s]*([0-9]+)x?', re.IGNORECASE),
                'multiplier': re.compile(r'([0-9]+)x\s*(?:leverage|lev)', re.IGNORECASE)
            },
            
            # Signal type patterns
            'signal_types': {
                'spot': re.compile(r'\b(?:spot|cash)\b', re.IGNORECASE),
                'futures': re.compile(r'\b(?:futures?|perp|perpetual)\b', re.IGNORECASE),
                'margin': re.compile(r'\b(?:margin|cross|isolated)\b', re.IGNORECASE),
                'scalp': re.compile(r'\b(?:scalp|quick)\b', re.IGNORECASE),
                'swing': re.compile(r'\b(?:swing|hold)\b', re.IGNORECASE)
            },
            
            # Quality indicators
            'quality': {
                'high_confidence': re.compile(r'\b(?:confirmed|strong|breakout|momentum|bullish|bearish|pumping|dumping)\b', re.IGNORECASE),
                'medium_confidence': re.compile(r'\b(?:potential|watch|possible|may|could|likely)\b', re.IGNORECASE),
                'low_confidence': re.compile(r'\b(?:risky|uncertain|volatile|caution|maybe)\b', re.IGNORECASE),
                'urgent': re.compile(r'\b(?:urgent|now|immediate|asap|quick)\b', re.IGNORECASE),
                'emoji_positive': re.compile(r'[🎯📈💎🚀🔥💚🟢✅]'),
                'emoji_negative': re.compile(r'[⚠️❌🔴💀📉]')
            },
            
            # Time-based patterns
            'timeframes': {
                'short_term': re.compile(r'\b(?:scalp|5m|15m|1h|quick)\b', re.IGNORECASE),
                'medium_term': re.compile(r'\b(?:4h|daily|swing|hold)\b', re.IGNORECASE),
                'long_term': re.compile(r'\b(?:weekly|monthly|position)\b', re.IGNORECASE)
            }
        }
        
        return patterns
    
    def _initialize_validators(self) -> Dict[str, callable]:
        """Initialize validation functions"""
        
        def validate_price_relationships(entry: Decimal, targets: List[Decimal], 
                                       stop_loss: Optional[Decimal], direction: Direction) -> bool:
            """Validate that price relationships make logical sense"""
            try:
                if direction in [Direction.LONG, Direction.BUY]:
                    # For long positions: targets > entry > stop_loss
                    for target in targets:
                        if target <= entry:
                            return False
                    if stop_loss and stop_loss >= entry:
                        return False
                else:
                    # For short positions: targets < entry < stop_loss
                    for target in targets:
                        if target >= entry:
                            return False
                    if stop_loss and stop_loss <= entry:
                        return False
                return True
            except:
                return False
        
        def validate_risk_reward(entry: Decimal, targets: List[Decimal], 
                               stop_loss: Optional[Decimal]) -> float:
            """Calculate and validate risk-reward ratio"""
            if not targets or not stop_loss:
                return 0.0
            
            try:
                # Use first target for calculation
                reward = abs(targets[0] - entry)
                risk = abs(entry - stop_loss)
                
                if risk == 0:
                    return 0.0
                
                return float(reward / risk)
            except:
                return 0.0
        
        def validate_percentage_moves(entry: Decimal, targets: List[Decimal], 
                                    stop_loss: Optional[Decimal]) -> Dict[str, float]:
            """Calculate percentage moves for targets and stop loss"""
            moves = {}
            
            try:
                for i, target in enumerate(targets, 1):
                    move = abs(target - entry) / entry * 100
                    moves[f'target_{i}_percent'] = float(move)
                
                if stop_loss:
                    sl_move = abs(entry - stop_loss) / entry * 100
                    moves['stop_loss_percent'] = float(sl_move)
                    
            except:
                pass
            
            return moves
        
        return {
            'price_relationships': validate_price_relationships,
            'risk_reward': validate_risk_reward,
            'percentage_moves': validate_percentage_moves
        }
    
    def _initialize_confidence_factors(self) -> Dict[str, Dict[str, float]]:
        """Initialize confidence scoring factors"""
        
        return {
            'completeness': {
                'has_entry': 0.2,
                'has_target': 0.2,
                'has_stop_loss': 0.15,
                'has_leverage': 0.05,
                'multiple_targets': 0.1
            },
            'quality_indicators': {
                'high_confidence_words': 0.1,
                'medium_confidence_words': 0.05,
                'low_confidence_words': -0.1,
                'positive_emojis': 0.05,
                'negative_emojis': -0.05,
                'urgent_indicators': 0.03
            },
            'structure': {
                'clear_formatting': 0.05,
                'numbered_targets': 0.05,
                'proper_symbols': 0.03,
                'consistent_format': 0.02
            },
            'validation': {
                'valid_price_relationships': 0.15,
                'good_risk_reward': 0.1,
                'reasonable_percentages': 0.05
            }
        }
    
    def extract_asset(self, text: str) -> Optional[str]:
        """Extract cryptocurrency asset from text"""
        
        # Try different asset patterns in order of preference
        for pattern_name, pattern in self.patterns['assets'].items():
            matches = pattern.findall(text)
            
            for match in matches:
                asset = match.upper()
                
                # Normalize asset format - keep original format if it's already valid
                if '/' not in asset and len(asset) > 6:
                    if asset.endswith('USDT'):
                        # Keep BTCUSDT format instead of converting to BTC/USDT
                        pass
                    elif asset.endswith('BTC'):
                        pass  # Keep ETHBTC format
                    elif asset.endswith('ETH'):
                        pass  # Keep LINKETH format
                elif '/' in asset:
                    # Convert ETH/USDT to ETHUSDT for consistency
                    asset = asset.replace('/', '')
                
                # Validate asset (basic check)
                if self._is_valid_asset(asset):
                    return asset
        
        return None
    
    def extract_direction(self, text: str) -> Optional[Direction]:
        """Extract trading direction from text"""
        
        direction_scores = {
            Direction.LONG: 0,
            Direction.SHORT: 0
        }
        
        # Check text patterns
        for pattern_type, pattern in self.patterns['directions'].items():
            matches = pattern.findall(text) if 'english' in pattern_type else pattern.search(text)
            
            if matches:
                if 'long' in pattern_type:
                    direction_scores[Direction.LONG] += 1
                else:
                    direction_scores[Direction.SHORT] += 1
        
        # Return direction with highest score
        if direction_scores[Direction.LONG] > direction_scores[Direction.SHORT]:
            return Direction.LONG
        elif direction_scores[Direction.SHORT] > direction_scores[Direction.LONG]:
            return Direction.SHORT
        
        return None
    
    def extract_entry_price(self, text: str) -> Optional[Decimal]:
        """Extract entry price from text"""
        
        for pattern_name, pattern in self.patterns['entry_prices'].items():
            matches = pattern.findall(text)
            
            for match in matches:
                try:
                    if pattern_name == 'range':
                        # For range, take the average
                        price1, price2 = match
                        price = (Decimal(price1) + Decimal(price2)) / 2
                    else:
                        # Clean price string (remove commas)
                        clean_price = match.replace(',', '')
                        price = Decimal(clean_price)
                    
                    if self._is_valid_price(price):
                        return price
                except:
                    continue
        
        return None
    
    def extract_targets(self, text: str) -> List[Decimal]:
        """Extract target prices from text"""
        
        targets = []
        
        # Try numbered targets first
        numbered_matches = self.patterns['targets']['numbered'].findall(text)
        target_dict = {}
        
        for target_num, price_str in numbered_matches:
            try:
                clean_price = price_str.replace(',', '')
                price = Decimal(clean_price)
                if self._is_valid_price(price):
                    target_dict[int(target_num)] = price
            except:
                continue
        
        # Add numbered targets in order
        for i in sorted(target_dict.keys()):
            targets.append(target_dict[i])
        
        # If no numbered targets, try other patterns
        if not targets:
            for pattern_name, pattern in self.patterns['targets'].items():
                if pattern_name == 'numbered':
                    continue
                
                matches = pattern.findall(text)
                for match in matches:
                    try:
                        if pattern_name == 'multiple':
                            # Split multiple targets
                            prices = re.split(r'[,\s]+', match)
                            for price_str in prices:
                                if price_str.strip():
                                    clean_price = price_str.strip().replace(',', '')
                                    price = Decimal(clean_price)
                                    if self._is_valid_price(price):
                                        targets.append(price)
                        elif pattern_name == 'range':
                            # Add both range endpoints as targets
                            price1, price2 = match
                            for price_str in [price1, price2]:
                                clean_price = price_str.replace(',', '')
                                price = Decimal(clean_price)
                                if self._is_valid_price(price):
                                    targets.append(price)
                        else:
                            clean_price = match.replace(',', '')
                            price = Decimal(clean_price)
                            if self._is_valid_price(price):
                                targets.append(price)
                    except:
                        continue
                
                if targets:
                    break
        
        # Remove duplicates and sort
        unique_targets = []
        for target in targets:
            if target not in unique_targets:
                unique_targets.append(target)
        
        return sorted(unique_targets)[:3]  # Max 3 targets
    
    def extract_stop_loss(self, text: str) -> Optional[Decimal]:
        """Extract stop loss from text"""
        
        for pattern_name, pattern in self.patterns['stop_loss'].items():
            matches = pattern.findall(text)
            
            for match in matches:
                try:
                    clean_price = match.replace(',', '')
                    price = Decimal(clean_price)
                    if self._is_valid_price(price):
                        return price
                except:
                    continue
        
        return None
    
    def extract_leverage(self, text: str) -> Optional[int]:
        """Extract leverage from text"""
        
        for pattern_name, pattern in self.patterns['leverage'].items():
            matches = pattern.findall(text)
            
            for match in matches:
                try:
                    leverage = int(match)
                    if 1 <= leverage <= 100:  # Reasonable leverage range
                        return leverage
                except:
                    continue
        
        return None
    
    def calculate_confidence(self, text: str, parsed_data: Dict[str, Any]) -> float:
        """Calculate confidence score for parsed signal"""
        
        confidence = 0.5  # Base confidence
        factors = self.confidence_factors
        
        # Completeness factors
        if parsed_data.get('entry_price'):
            confidence += factors['completeness']['has_entry']
        if parsed_data.get('targets'):
            confidence += factors['completeness']['has_target']
            if len(parsed_data['targets']) > 1:
                confidence += factors['completeness']['multiple_targets']
        if parsed_data.get('stop_loss'):
            confidence += factors['completeness']['has_stop_loss']
        if parsed_data.get('leverage'):
            confidence += factors['completeness']['has_leverage']
        
        # Quality indicators
        for pattern_type, pattern in self.patterns['quality'].items():
            if pattern.search(text):
                if 'high_confidence' in pattern_type:
                    confidence += factors['quality_indicators']['high_confidence_words']
                elif 'medium_confidence' in pattern_type:
                    confidence += factors['quality_indicators']['medium_confidence_words']
                elif 'low_confidence' in pattern_type:
                    confidence += factors['quality_indicators']['low_confidence_words']
                elif 'positive' in pattern_type:
                    confidence += factors['quality_indicators']['positive_emojis']
                elif 'negative' in pattern_type:
                    confidence += factors['quality_indicators']['negative_emojis']
                elif 'urgent' in pattern_type:
                    confidence += factors['quality_indicators']['urgent_indicators']
        
        # Validation factors
        if parsed_data.get('entry_price') and parsed_data.get('targets'):
            entry = parsed_data['entry_price']
            targets = parsed_data['targets']
            stop_loss = parsed_data.get('stop_loss')
            direction = parsed_data.get('direction')
            
            if direction and self.validators['price_relationships'](entry, targets, stop_loss, direction):
                confidence += factors['validation']['valid_price_relationships']
            
            rr_ratio = self.validators['risk_reward'](entry, targets, stop_loss)
            if rr_ratio >= 2.0:
                confidence += factors['validation']['good_risk_reward']
            elif rr_ratio >= 1.0:
                confidence += factors['validation']['good_risk_reward'] * 0.5
        
        return max(0.0, min(1.0, confidence))
    
    def parse_signal(self, text: str, metadata: Dict[str, Any] = None) -> Optional[ParsedSignal]:
        """Parse a complete trading signal from text"""
        
        if not text or len(text.strip()) < 10:
            return None
        
        # Extract components
        asset = self.extract_asset(text)
        if not asset:
            return None
        
        direction = self.extract_direction(text)
        if not direction:
            return None
        
        entry_price = self.extract_entry_price(text)
        if not entry_price:
            return None
        
        targets = self.extract_targets(text)
        stop_loss = self.extract_stop_loss(text)
        leverage = self.extract_leverage(text)
        
        # Basic validation
        if not targets and not stop_loss:
            return None
        
        # Determine signal type
        signal_type = SignalType.SPOT  # Default
        for type_name, pattern in self.patterns['signal_types'].items():
            if pattern.search(text):
                if type_name in ['spot', 'futures', 'margin']:
                    signal_type = SignalType(type_name)
                    break
                elif type_name in ['scalp', 'swing']:
                    signal_type = SignalType.FUTURES  # Map scalp/swing to futures
                    break
        
        # Prepare data for confidence calculation
        parsed_data = {
            'asset': asset,
            'direction': direction,
            'entry_price': entry_price,
            'targets': targets,
            'stop_loss': stop_loss,
            'leverage': leverage,
            'signal_type': signal_type
        }
        
        # Calculate confidence
        confidence = self.calculate_confidence(text, parsed_data)
        
        # Add validation metadata
        validation_metadata = {}
        if targets and stop_loss:
            validation_metadata.update(
                self.validators['percentage_moves'](entry_price, targets, stop_loss)
            )
            validation_metadata['risk_reward_ratio'] = self.validators['risk_reward'](
                entry_price, targets, stop_loss
            )
        
        # Combine metadata
        final_metadata = metadata or {}
        final_metadata.update(validation_metadata)
        
        return ParsedSignal(
            asset=asset,
            direction=direction,
            entry_price=entry_price,
            targets=targets,
            stop_loss=stop_loss,
            leverage=leverage,
            signal_type=signal_type,
            confidence=confidence,
            raw_text=text[:500],  # Truncate for storage
            metadata=final_metadata
        )
    
    def _is_valid_asset(self, asset: str) -> bool:
        """Validate if asset string represents a valid cryptocurrency pair"""
        
        # Basic validation rules
        if len(asset) < 3 or len(asset) > 12:
            return False
        
        # Common crypto patterns
        valid_patterns = [
            r'^[A-Z]{2,6}/[A-Z]{2,6}$',  # BTC/USDT
            r'^[A-Z]{3,8}USDT?$',        # BTCUSDT
            r'^[A-Z]{3,8}BTC$',          # ETHBTC
            r'^[A-Z]{3,8}ETH$'           # LINKETH
        ]
        
        return any(re.match(pattern, asset) for pattern in valid_patterns)
    
    def _is_valid_price(self, price: Decimal) -> bool:
        """Validate if price is within reasonable bounds"""
        
        try:
            price_float = float(price)
            return 0.000001 <= price_float <= 1000000
        except:
            return False

# Global instance for easy import
signal_patterns = EnhancedSignalPatterns()

# Convenience functions
def parse_trading_signal(text: str, metadata: Dict[str, Any] = None) -> Optional[ParsedSignal]:
    """Parse a trading signal from text - convenience function"""
    return signal_patterns.parse_signal(text, metadata)

def extract_signal_components(text: str) -> Dict[str, Any]:
    """Extract individual signal components - convenience function"""
    return {
        'asset': signal_patterns.extract_asset(text),
        'direction': signal_patterns.extract_direction(text),
        'entry_price': signal_patterns.extract_entry_price(text),
        'targets': signal_patterns.extract_targets(text),
        'stop_loss': signal_patterns.extract_stop_loss(text),
        'leverage': signal_patterns.extract_leverage(text)
    } 