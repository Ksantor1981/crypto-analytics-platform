"""
Channel metrics calculation and performance tracking
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class SignalStatus(Enum):
    """Signal status enumeration"""
    PENDING = "pending"
    EXECUTED = "executed"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class SignalResult:
    """Signal execution result"""
    signal_id: str
    channel_id: str
    timestamp: datetime
    entry_price: float
    exit_price: Optional[float] = None
    status: SignalStatus = SignalStatus.PENDING
    roi: Optional[float] = None
    duration_hours: Optional[float] = None
    volume: Optional[float] = None
    fees: Optional[float] = None

@dataclass
class ChannelMetrics:
    """Comprehensive channel performance metrics"""
    channel_id: str
    total_signals: int
    successful_signals: int
    accuracy: float  # Success rate
    total_roi: float  # Cumulative ROI
    avg_roi: float  # Average ROI per signal
    sharpe_ratio: float  # Risk-adjusted returns
    max_drawdown: float  # Maximum drawdown
    win_rate: float  # Win rate
    avg_win: float  # Average winning trade
    avg_loss: float  # Average losing trade
    profit_factor: float  # Profit factor
    signal_frequency: float  # Signals per day
    consistency_score: float  # Performance consistency
    risk_score: float  # Risk assessment
    performance_rating: str  # "Excellent", "Good", "Average", "Poor"

class ChannelMetricsCalculator:
    """Calculator for channel performance metrics"""
    
    def __init__(self):
        self.min_signals_for_rating = 10
        self.risk_free_rate = 0.02  # 2% annual
        
    def calculate_channel_metrics(self, channel_id: str, 
                                signals: List[SignalResult]) -> ChannelMetrics:
        """Calculate comprehensive channel metrics"""
        if not signals:
            return self._get_default_metrics(channel_id)
        
        # Filter completed signals
        completed_signals = [s for s in signals if s.status in [SignalStatus.SUCCESSFUL, SignalStatus.FAILED]]
        
        if len(completed_signals) < 5:
            return self._get_default_metrics(channel_id)
        
        # Basic metrics
        total_signals = len(completed_signals)
        successful_signals = len([s for s in completed_signals if s.status == SignalStatus.SUCCESSFUL])
        accuracy = successful_signals / total_signals if total_signals > 0 else 0.0
        
        # ROI calculations
        rois = [s.roi for s in completed_signals if s.roi is not None]
        total_roi = sum(rois) if rois else 0.0
        avg_roi = np.mean(rois) if rois else 0.0
        
        # Risk metrics
        sharpe_ratio = self._calculate_sharpe_ratio(rois)
        max_drawdown = self._calculate_max_drawdown(rois)
        
        # Win/Loss analysis
        winning_signals = [s for s in completed_signals if s.roi and s.roi > 0]
        losing_signals = [s for s in completed_signals if s.roi and s.roi < 0]
        
        win_rate = len(winning_signals) / total_signals if total_signals > 0 else 0.0
        avg_win = np.mean([s.roi for s in winning_signals]) if winning_signals else 0.0
        avg_loss = abs(np.mean([s.roi for s in losing_signals])) if losing_signals else 0.0
        
        # Profit factor
        total_wins = sum([s.roi for s in winning_signals]) if winning_signals else 0.0
        total_losses = abs(sum([s.roi for s in losing_signals])) if losing_signals else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Signal frequency
        signal_frequency = self._calculate_signal_frequency(signals)
        
        # Consistency score
        consistency_score = self._calculate_consistency_score(rois)
        
        # Risk score
        risk_score = self._calculate_risk_score(accuracy, avg_roi, max_drawdown, consistency_score)
        
        # Performance rating
        performance_rating = self._calculate_performance_rating(accuracy, avg_roi, sharpe_ratio, risk_score)
        
        return ChannelMetrics(
            channel_id=channel_id,
            total_signals=total_signals,
            successful_signals=successful_signals,
            accuracy=float(accuracy),
            total_roi=float(total_roi),
            avg_roi=float(avg_roi),
            sharpe_ratio=float(sharpe_ratio),
            max_drawdown=float(max_drawdown),
            win_rate=float(win_rate),
            avg_win=float(avg_win),
            avg_loss=float(avg_loss),
            profit_factor=float(profit_factor),
            signal_frequency=float(signal_frequency),
            consistency_score=float(consistency_score),
            risk_score=float(risk_score),
            performance_rating=performance_rating
        )
    
    def _calculate_sharpe_ratio(self, rois: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if not rois or len(rois) < 2:
            return 0.0
        
        returns = np.array(rois)
        excess_returns = returns - self.risk_free_rate / 252  # Daily risk-free rate
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        return float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252))
    
    def _calculate_max_drawdown(self, rois: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not rois:
            return 0.0
        
        cumulative_returns = np.cumsum(rois)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = cumulative_returns - running_max
        
        return float(np.min(drawdown))
    
    def _calculate_signal_frequency(self, signals: List[SignalResult]) -> float:
        """Calculate average signals per day"""
        if len(signals) < 2:
            return 0.0
        
        # Sort by timestamp
        sorted_signals = sorted(signals, key=lambda x: x.timestamp)
        first_signal = sorted_signals[0].timestamp
        last_signal = sorted_signals[-1].timestamp
        
        days_span = (last_signal - first_signal).days
        if days_span == 0:
            days_span = 1
        
        return len(signals) / days_span
    
    def _calculate_consistency_score(self, rois: List[float]) -> float:
        """Calculate performance consistency score"""
        if not rois or len(rois) < 5:
            return 0.5
        
        # Calculate rolling performance consistency
        window_size = min(10, len(rois) // 2)
        consistency_scores = []
        
        for i in range(window_size, len(rois)):
            window_rois = rois[i-window_size:i]
            window_std = np.std(window_rois)
            window_mean = np.mean(window_rois)
            
            # Lower std/mean ratio indicates higher consistency
            if abs(window_mean) > 0.001:
                consistency = 1.0 / (1.0 + window_std / abs(window_mean))
            else:
                consistency = 0.5
            
            consistency_scores.append(consistency)
        
        return float(np.mean(consistency_scores)) if consistency_scores else 0.5
    
    def _calculate_risk_score(self, accuracy: float, avg_roi: float, 
                            max_drawdown: float, consistency: float) -> float:
        """Calculate overall risk score (0-100, lower is better)"""
        # Accuracy penalty (lower accuracy = higher risk)
        accuracy_penalty = (1.0 - accuracy) * 30
        
        # ROI penalty (negative ROI = higher risk)
        roi_penalty = max(0, -avg_roi * 100)
        
        # Drawdown penalty
        drawdown_penalty = abs(max_drawdown) * 50
        
        # Consistency penalty (lower consistency = higher risk)
        consistency_penalty = (1.0 - consistency) * 20
        
        risk_score = accuracy_penalty + roi_penalty + drawdown_penalty + consistency_penalty
        
        return float(np.clip(risk_score, 0, 100))
    
    def _calculate_performance_rating(self, accuracy: float, avg_roi: float, 
                                    sharpe_ratio: float, risk_score: float) -> str:
        """Calculate performance rating"""
        # Scoring system
        score = 0
        
        # Accuracy score (0-25 points)
        if accuracy >= 0.8:
            score += 25
        elif accuracy >= 0.7:
            score += 20
        elif accuracy >= 0.6:
            score += 15
        elif accuracy >= 0.5:
            score += 10
        else:
            score += 5
        
        # ROI score (0-25 points)
        if avg_roi >= 0.1:
            score += 25
        elif avg_roi >= 0.05:
            score += 20
        elif avg_roi >= 0.02:
            score += 15
        elif avg_roi >= 0.0:
            score += 10
        else:
            score += 5
        
        # Sharpe ratio score (0-25 points)
        if sharpe_ratio >= 2.0:
            score += 25
        elif sharpe_ratio >= 1.5:
            score += 20
        elif sharpe_ratio >= 1.0:
            score += 15
        elif sharpe_ratio >= 0.5:
            score += 10
        else:
            score += 5
        
        # Risk score (0-25 points)
        if risk_score <= 20:
            score += 25
        elif risk_score <= 40:
            score += 20
        elif risk_score <= 60:
            score += 15
        elif risk_score <= 80:
            score += 10
        else:
            score += 5
        
        # Determine rating
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Average"
        else:
            return "Poor"
    
    def _get_default_metrics(self, channel_id: str) -> ChannelMetrics:
        """Get default metrics for new channels"""
        return ChannelMetrics(
            channel_id=channel_id,
            total_signals=0,
            successful_signals=0,
            accuracy=0.5,
            total_roi=0.0,
            avg_roi=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            profit_factor=0.0,
            signal_frequency=0.0,
            consistency_score=0.5,
            risk_score=50.0,
            performance_rating="Average"
        )
    
    def generate_performance_report(self, channel_metrics: ChannelMetrics) -> str:
        """Generate detailed performance report"""
        report = f"""
# Channel Performance Report
Channel ID: {channel_metrics.channel_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Performance Summary
- **Rating**: {channel_metrics.performance_rating}
- **Total Signals**: {channel_metrics.total_signals}
- **Success Rate**: {channel_metrics.accuracy:.1%}
- **Average ROI**: {channel_metrics.avg_roi:.2%}
- **Total ROI**: {channel_metrics.total_roi:.2%}

## Risk Metrics
- **Sharpe Ratio**: {channel_metrics.sharpe_ratio:.2f}
- **Max Drawdown**: {channel_metrics.max_drawdown:.2%}
- **Risk Score**: {channel_metrics.risk_score:.1f}/100
- **Consistency Score**: {channel_metrics.consistency_score:.2f}

## Trading Analysis
- **Win Rate**: {channel_metrics.win_rate:.1%}
- **Average Win**: {channel_metrics.avg_win:.2%}
- **Average Loss**: {channel_metrics.avg_loss:.2%}
- **Profit Factor**: {channel_metrics.profit_factor:.2f}
- **Signal Frequency**: {channel_metrics.signal_frequency:.1f} signals/day

## Recommendations
"""
        
        # Generate recommendations based on metrics
        if channel_metrics.accuracy < 0.6:
            report += "- ⚠️ Low success rate - consider improving signal quality\n"
        
        if channel_metrics.avg_roi < 0.02:
            report += "- ⚠️ Low average ROI - review strategy effectiveness\n"
        
        if channel_metrics.risk_score > 70:
            report += "- ⚠️ High risk score - consider risk management improvements\n"
        
        if channel_metrics.sharpe_ratio < 1.0:
            report += "- ⚠️ Low risk-adjusted returns - optimize risk/reward ratio\n"
        
        if channel_metrics.performance_rating in ["Excellent", "Good"]:
            report += "- ✅ Strong performance - maintain current strategy\n"
        
        return report


class ChannelPerformanceTracker:
    """Real-time channel performance tracking"""
    
    def __init__(self):
        self.calculator = ChannelMetricsCalculator()
        self.channel_data = {}  # channel_id -> list of signals
        
    def add_signal(self, channel_id: str, signal: SignalResult):
        """Add new signal to tracking"""
        if channel_id not in self.channel_data:
            self.channel_data[channel_id] = []
        
        self.channel_data[channel_id].append(signal)
        
    def update_signal_result(self, channel_id: str, signal_id: str, 
                           status: SignalStatus, exit_price: Optional[float] = None,
                           roi: Optional[float] = None):
        """Update signal result"""
        if channel_id not in self.channel_data:
            return
        
        for signal in self.channel_data[channel_id]:
            if signal.signal_id == signal_id:
                signal.status = status
                signal.exit_price = exit_price
                signal.roi = roi
                if signal.timestamp and exit_price:
                    signal.duration_hours = (datetime.now() - signal.timestamp).total_seconds() / 3600
                break
    
    def get_channel_metrics(self, channel_id: str) -> Optional[ChannelMetrics]:
        """Get current metrics for channel"""
        if channel_id not in self.channel_data:
            return None
        
        return self.calculator.calculate_channel_metrics(
            channel_id, self.channel_data[channel_id]
        )
    
    def get_all_channels_metrics(self) -> Dict[str, ChannelMetrics]:
        """Get metrics for all tracked channels"""
        metrics = {}
        for channel_id in self.channel_data:
            metrics[channel_id] = self.get_channel_metrics(channel_id)
        return metrics
    
    def get_top_performing_channels(self, limit: int = 10) -> List[Tuple[str, ChannelMetrics]]:
        """Get top performing channels by rating"""
        all_metrics = self.get_all_channels_metrics()
        
        # Sort by performance rating
        rating_scores = {"Excellent": 4, "Good": 3, "Average": 2, "Poor": 1}
        
        sorted_channels = sorted(
            all_metrics.items(),
            key=lambda x: (rating_scores.get(x[1].performance_rating, 0), x[1].avg_roi),
            reverse=True
        )
        
        return sorted_channels[:limit]


def main():
    """Test channel metrics calculation"""
    calculator = ChannelMetricsCalculator()
    tracker = ChannelPerformanceTracker()
    
    # Generate mock signals
    channel_id = "test_channel_1"
    signals = []
    
    for i in range(20):
        # Mock signal with varying success
        success = np.random.random() > 0.3  # 70% success rate
        roi = np.random.uniform(0.02, 0.08) if success else np.random.uniform(-0.05, -0.01)
        
        signal = SignalResult(
            signal_id=f"signal_{i}",
            channel_id=channel_id,
            timestamp=datetime.now() - timedelta(hours=i*2),
            entry_price=50000.0,
            exit_price=50000.0 * (1 + roi),
            status=SignalStatus.SUCCESSFUL if success else SignalStatus.FAILED,
            roi=roi,
            duration_hours=2.0
        )
        
        signals.append(signal)
        tracker.add_signal(channel_id, signal)
    
    # Calculate metrics
    metrics = calculator.calculate_channel_metrics(channel_id, signals)
    
    print(f"Channel: {metrics.channel_id}")
    print(f"Accuracy: {metrics.accuracy:.1%}")
    print(f"Average ROI: {metrics.avg_roi:.2%}")
    print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"Performance Rating: {metrics.performance_rating}")
    
    # Generate report
    report = calculator.generate_performance_report(metrics)
    print("\nPerformance Report:")
    print(report)


if __name__ == "__main__":
    main() 