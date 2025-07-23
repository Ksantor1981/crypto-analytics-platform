"""
Market data processing module for real-time volume, volatility, and trend analysis
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Market data structure"""
    timestamp: datetime
    price: float
    volume: float
    high: float
    low: float
    open_price: float
    close_price: float

@dataclass
class MarketMetrics:
    """Calculated market metrics"""
    volume_ma: float  # Volume moving average
    volume_ratio: float  # Current volume / average volume
    volatility: float  # Price volatility
    volatility_ma: float  # Volatility moving average
    trend_strength: float  # Trend strength indicator
    trend_direction: str  # "bullish", "bearish", "sideways"
    price_momentum: float  # Price momentum
    volume_momentum: float  # Volume momentum
    market_regime: str  # "trending", "ranging", "volatile"

class MarketDataProcessor:
    """Processor for real-time market data analysis"""
    
    def __init__(self, window_sizes: List[int] = None):
        self.window_sizes = window_sizes or [14, 30, 60]  # Default windows
        self.data_buffer = []  # Buffer for recent data
        self.max_buffer_size = 1000
        
    def add_market_data(self, market_data: MarketData):
        """Add new market data point"""
        self.data_buffer.append(market_data)
        
        # Keep buffer size manageable
        if len(self.data_buffer) > self.max_buffer_size:
            self.data_buffer = self.data_buffer[-self.max_buffer_size:]
    
    def calculate_volume_metrics(self, window: int = 30) -> Dict[str, float]:
        """Calculate volume-based metrics"""
        if len(self.data_buffer) < window:
            return self._get_default_volume_metrics()
        
        recent_data = self.data_buffer[-window:]
        volumes = [d.volume for d in recent_data]
        current_volume = volumes[-1]
        
        # Volume moving average
        volume_ma = np.mean(volumes)
        
        # Volume ratio (current vs average)
        volume_ratio = current_volume / volume_ma if volume_ma > 0 else 1.0
        
        # Volume momentum (rate of change)
        if len(volumes) >= 5:
            recent_avg = np.mean(volumes[-5:])
            volume_momentum = (current_volume - recent_avg) / recent_avg if recent_avg > 0 else 0.0
        else:
            volume_momentum = 0.0
        
        # Volume volatility
        volume_volatility = np.std(volumes) / volume_ma if volume_ma > 0 else 0.0
        
        return {
            'volume_ma': float(volume_ma),
            'volume_ratio': float(volume_ratio),
            'volume_momentum': float(volume_momentum),
            'volume_volatility': float(volume_volatility),
            'volume_trend': 'increasing' if volume_momentum > 0.1 else 'decreasing' if volume_momentum < -0.1 else 'stable'
        }
    
    def calculate_volatility_metrics(self, window: int = 30) -> Dict[str, float]:
        """Calculate volatility-based metrics"""
        if len(self.data_buffer) < window:
            return self._get_default_volatility_metrics()
        
        recent_data = self.data_buffer[-window:]
        prices = [d.close_price for d in recent_data]
        
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        # Current volatility (standard deviation of returns)
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        
        # Volatility moving average
        volatility_ma = np.mean([np.std(returns[i:i+10]) * np.sqrt(252) for i in range(0, len(returns)-9, 5)]) if len(returns) >= 10 else volatility
        
        # Volatility ratio (current vs average)
        volatility_ratio = volatility / volatility_ma if volatility_ma > 0 else 1.0
        
        # Volatility trend
        if len(returns) >= 20:
            recent_vol = np.std(returns[-10:]) * np.sqrt(252)
            vol_trend = (recent_vol - volatility_ma) / volatility_ma if volatility_ma > 0 else 0.0
        else:
            vol_trend = 0.0
        
        return {
            'volatility': float(volatility),
            'volatility_ma': float(volatility_ma),
            'volatility_ratio': float(volatility_ratio),
            'volatility_trend': float(vol_trend),
            'volatility_regime': 'high' if volatility > volatility_ma * 1.5 else 'low' if volatility < volatility_ma * 0.5 else 'normal'
        }
    
    def calculate_trend_metrics(self, window: int = 30) -> Dict[str, Any]:
        """Calculate trend-based metrics"""
        if len(self.data_buffer) < window:
            return self._get_default_trend_metrics()
        
        recent_data = self.data_buffer[-window:]
        prices = np.array([d.close_price for d in recent_data])
        
        # Linear regression for trend
        x = np.arange(len(prices))
        slope, intercept = np.polyfit(x, prices, 1)
        
        # Trend strength (R-squared)
        y_pred = slope * x + intercept
        ss_res = np.sum((prices - y_pred) ** 2)
        ss_tot = np.sum((prices - np.mean(prices)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        # Trend direction
        if slope > 0 and r_squared > 0.3:
            trend_direction = "bullish"
        elif slope < 0 and r_squared > 0.3:
            trend_direction = "bearish"
        else:
            trend_direction = "sideways"
        
        # Price momentum
        if len(prices) >= 5:
            recent_change = (prices[-1] - prices[-5]) / prices[-5]
            price_momentum = recent_change
        else:
            price_momentum = 0.0
        
        # Trend strength (0-1 scale)
        trend_strength = min(r_squared, 1.0)
        
        # Support and resistance levels
        support = np.min(prices[-10:]) if len(prices) >= 10 else prices[0]
        resistance = np.max(prices[-10:]) if len(prices) >= 10 else prices[0]
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': float(trend_strength),
            'trend_slope': float(slope),
            'price_momentum': float(price_momentum),
            'support_level': float(support),
            'resistance_level': float(resistance),
            'r_squared': float(r_squared)
        }
    
    def calculate_market_regime(self) -> str:
        """Determine current market regime"""
        if len(self.data_buffer) < 30:
            return "unknown"
        
        # Get metrics
        volume_metrics = self.calculate_volume_metrics()
        volatility_metrics = self.calculate_volatility_metrics()
        trend_metrics = self.calculate_trend_metrics()
        
        # Determine regime based on metrics
        volatility = volatility_metrics['volatility']
        trend_strength = trend_metrics['trend_strength']
        volume_ratio = volume_metrics['volume_ratio']
        
        if volatility > 0.5:  # High volatility
            return "volatile"
        elif trend_strength > 0.6 and volume_ratio > 1.2:  # Strong trend with volume
            return "trending"
        elif trend_strength < 0.3 and volume_ratio < 0.8:  # Weak trend, low volume
            return "ranging"
        else:
            return "mixed"
    
    def get_comprehensive_market_metrics(self) -> MarketMetrics:
        """Get comprehensive market metrics"""
        if len(self.data_buffer) < 30:
            return self._get_default_market_metrics()
        
        # Calculate all metrics
        volume_metrics = self.calculate_volume_metrics()
        volatility_metrics = self.calculate_volatility_metrics()
        trend_metrics = self.calculate_trend_metrics()
        market_regime = self.calculate_market_regime()
        
        return MarketMetrics(
            volume_ma=volume_metrics['volume_ma'],
            volume_ratio=volume_metrics['volume_ratio'],
            volatility=volatility_metrics['volatility'],
            volatility_ma=volatility_metrics['volatility_ma'],
            trend_strength=trend_metrics['trend_strength'],
            trend_direction=trend_metrics['trend_direction'],
            price_momentum=trend_metrics['price_momentum'],
            volume_momentum=volume_metrics['volume_momentum'],
            market_regime=market_regime
        )
    
    def get_feature_vector(self) -> Dict[str, float]:
        """Get feature vector for ML models"""
        metrics = self.get_comprehensive_market_metrics()
        
        return {
            'volume_ma': metrics.volume_ma,
            'volume_ratio': metrics.volume_ratio,
            'volume_momentum': metrics.volume_momentum,
            'volatility': metrics.volatility,
            'volatility_ma': metrics.volatility_ma,
            'trend_strength': metrics.trend_strength,
            'price_momentum': metrics.price_momentum,
            'market_regime_trending': 1.0 if metrics.market_regime == 'trending' else 0.0,
            'market_regime_volatile': 1.0 if metrics.market_regime == 'volatile' else 0.0,
            'market_regime_ranging': 1.0 if metrics.market_regime == 'ranging' else 0.0,
            'trend_bullish': 1.0 if metrics.trend_direction == 'bullish' else 0.0,
            'trend_bearish': 1.0 if metrics.trend_direction == 'bearish' else 0.0
        }
    
    def _get_default_volume_metrics(self) -> Dict[str, float]:
        """Get default volume metrics when insufficient data"""
        return {
            'volume_ma': 1000.0,
            'volume_ratio': 1.0,
            'volume_momentum': 0.0,
            'volume_volatility': 0.0,
            'volume_trend': 'stable'
        }
    
    def _get_default_volatility_metrics(self) -> Dict[str, float]:
        """Get default volatility metrics when insufficient data"""
        return {
            'volatility': 0.2,
            'volatility_ma': 0.2,
            'volatility_ratio': 1.0,
            'volatility_trend': 0.0,
            'volatility_regime': 'normal'
        }
    
    def _get_default_trend_metrics(self) -> Dict[str, Any]:
        """Get default trend metrics when insufficient data"""
        return {
            'trend_direction': 'sideways',
            'trend_strength': 0.0,
            'trend_slope': 0.0,
            'price_momentum': 0.0,
            'support_level': 100.0,
            'resistance_level': 100.0,
            'r_squared': 0.0
        }
    
    def _get_default_market_metrics(self) -> MarketMetrics:
        """Get default market metrics when insufficient data"""
        return MarketMetrics(
            volume_ma=1000.0,
            volume_ratio=1.0,
            volatility=0.2,
            volatility_ma=0.2,
            trend_strength=0.0,
            trend_direction='sideways',
            price_momentum=0.0,
            volume_momentum=0.0,
            market_regime='unknown'
        )


class RealTimeMarketDataFeed:
    """Real-time market data feed with processing"""
    
    def __init__(self):
        self.processors = {}  # One processor per asset
        self.data_sources = {}
        
    def add_asset(self, asset: str):
        """Add new asset for tracking"""
        self.processors[asset] = MarketDataProcessor()
        
    def update_market_data(self, asset: str, market_data: MarketData):
        """Update market data for specific asset"""
        if asset not in self.processors:
            self.add_asset(asset)
        
        self.processors[asset].add_market_data(market_data)
        
    def get_asset_metrics(self, asset: str) -> Optional[MarketMetrics]:
        """Get current metrics for specific asset"""
        if asset not in self.processors:
            return None
        
        return self.processors[asset].get_comprehensive_market_metrics()
    
    def get_all_assets_metrics(self) -> Dict[str, MarketMetrics]:
        """Get metrics for all tracked assets"""
        return {asset: processor.get_comprehensive_market_metrics() 
                for asset, processor in self.processors.items()}
    
    def get_feature_vectors(self) -> Dict[str, Dict[str, float]]:
        """Get feature vectors for all assets"""
        return {asset: processor.get_feature_vector() 
                for asset, processor in self.processors.items()}


def main():
    """Test market data processing"""
    processor = MarketDataProcessor()
    
    # Generate mock market data
    base_price = 100.0
    for i in range(100):
        # Simulate price movement
        price_change = np.random.normal(0, 0.02)
        base_price *= (1 + price_change)
        
        # Simulate volume
        volume = np.random.uniform(800, 1200)
        
        market_data = MarketData(
            timestamp=datetime.now() + timedelta(hours=i),
            price=base_price,
            volume=volume,
            high=base_price * 1.01,
            low=base_price * 0.99,
            open_price=base_price * 0.999,
            close_price=base_price
        )
        
        processor.add_market_data(market_data)
    
    # Get comprehensive metrics
    metrics = processor.get_comprehensive_market_metrics()
    print(f"Market Regime: {metrics.market_regime}")
    print(f"Trend Direction: {metrics.trend_direction}")
    print(f"Volatility: {metrics.volatility:.3f}")
    print(f"Volume Ratio: {metrics.volume_ratio:.3f}")
    
    # Get feature vector
    features = processor.get_feature_vector()
    print(f"Feature vector: {features}")


if __name__ == "__main__":
    main() 