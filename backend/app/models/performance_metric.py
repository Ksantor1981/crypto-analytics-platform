from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Numeric, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

from .base import BaseModel

class PerformanceMetric(BaseModel):
    """
    Model for storing pre-calculated channel performance metrics
    This helps improve dashboard loading performance by avoiding complex calculations on the fly
    """
    __tablename__ = "performance_metrics"
    
    # Channel relationship
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    channel = relationship("Channel", back_populates="performance_metrics")
    
    # Time period for the metrics
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False, index=True)  # daily, weekly, monthly, all_time
    
    # Basic metrics
    total_signals = Column(Integer, default=0)
    successful_signals = Column(Integer, default=0)
    failed_signals = Column(Integer, default=0)
    pending_signals = Column(Integer, default=0)
    cancelled_signals = Column(Integer, default=0)
    
    # Performance metrics
    win_rate = Column(Numeric(5, 2), nullable=True)  # Percentage (0-100)
    average_roi = Column(Numeric(10, 4), nullable=True)  # Percentage
    total_roi = Column(Numeric(15, 4), nullable=True)  # Cumulative ROI
    best_signal_roi = Column(Numeric(10, 4), nullable=True)
    worst_signal_roi = Column(Numeric(10, 4), nullable=True)
    
    # Risk metrics
    max_drawdown = Column(Numeric(10, 4), nullable=True)  # Percentage
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    volatility = Column(Numeric(10, 4), nullable=True)
    
    # Advanced metrics
    risk_reward_ratio = Column(Numeric(10, 4), nullable=True)
    consistency_score = Column(Numeric(5, 2), nullable=True)  # 0-100 score
    profit_factor = Column(Numeric(10, 4), nullable=True)  # Total profits / Total losses
    
    # Timing metrics
    average_signal_duration = Column(Integer, nullable=True)  # Hours
    fastest_success_time = Column(Integer, nullable=True)  # Hours
    slowest_success_time = Column(Integer, nullable=True)  # Hours
    
    # Asset distribution (JSON for flexibility)
    asset_breakdown = Column(JSON, nullable=True)  # {"BTC/USDT": 45, "ETH/USDT": 30, ...}
    direction_breakdown = Column(JSON, nullable=True)  # {"BUY": 60, "SELL": 40}
    
    # Quality score (composite metric)
    quality_score = Column(Numeric(5, 2), nullable=True)  # 0-100 overall quality score
    
    # Ranking
    rank_in_period = Column(Integer, nullable=True)  # Rank among all channels in this period
    percentile = Column(Numeric(5, 2), nullable=True)  # Percentile ranking (0-100)
    
    # Metadata
    calculation_timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    data_points_used = Column(Integer, nullable=True)  # Number of signals used for calculation
    
    # Flags
    is_verified = Column(Boolean, default=False)  # Whether data has been verified
    has_sufficient_data = Column(Boolean, default=False)  # Whether there's enough data for reliable metrics
    
    @property
    def success_rate_category(self) -> str:
        """Categorize channel based on win rate"""
        if not self.win_rate:
            return "UNKNOWN"
        
        if self.win_rate >= 70:
            return "EXCELLENT"
        elif self.win_rate >= 60:
            return "GOOD"
        elif self.win_rate >= 50:
            return "AVERAGE"
        elif self.win_rate >= 40:
            return "BELOW_AVERAGE"
        else:
            return "POOR"
    
    @property
    def roi_category(self) -> str:
        """Categorize channel based on average ROI"""
        if not self.average_roi:
            return "UNKNOWN"
        
        if self.average_roi >= 15:
            return "HIGH_RETURN"
        elif self.average_roi >= 5:
            return "MEDIUM_RETURN"
        elif self.average_roi >= 0:
            return "LOW_RETURN"
        else:
            return "NEGATIVE_RETURN"
    
    def __repr__(self):
        return f"<PerformanceMetric Channel:{self.channel_id} {self.period_type} WinRate:{self.win_rate}%>" 