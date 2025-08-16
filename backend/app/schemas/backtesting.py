"""
Backtesting schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class BacktestingRequest(BaseModel):
    """Request model for backtesting strategy"""
    strategy: str = Field(..., description="Strategy name (momentum, mean_reversion, signal_quality)")
    start_date: datetime = Field(..., description="Start date for backtesting")
    end_date: datetime = Field(..., description="End date for backtesting")
    assets: Optional[List[str]] = Field(None, description="List of assets to test (e.g., ['BTCUSDT', 'ETHUSDT'])")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy-specific parameters")

class StrategyResult(BaseModel):
    """Result of strategy backtesting"""
    total_signals: int = Field(..., description="Total number of signals tested")
    successful_signals: int = Field(..., description="Number of successful signals")
    success_rate: float = Field(..., description="Success rate (0.0 to 1.0)")
    total_roi: float = Field(..., description="Total ROI percentage")
    avg_roi: float = Field(..., description="Average ROI per signal")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")

class SignalPerformance(BaseModel):
    """Individual signal performance"""
    signal_id: int = Field(..., description="Signal ID")
    asset: str = Field(..., description="Asset name")
    direction: str = Field(..., description="Signal direction")
    entry_price: Decimal = Field(..., description="Entry price")
    exit_price: Optional[Decimal] = Field(None, description="Exit price")
    roi: Optional[float] = Field(None, description="Return on investment")
    is_successful: Optional[bool] = Field(None, description="Whether signal was successful")

class BacktestingResponse(BaseModel):
    """Response model for backtesting results"""
    strategy: str = Field(..., description="Strategy name")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    total_signals: int = Field(..., description="Total signals analyzed")
    results: StrategyResult = Field(..., description="Strategy results")
    signal_performances: Optional[List[SignalPerformance]] = Field(None, description="Individual signal performances")

class StrategyInfo(BaseModel):
    """Information about available strategy"""
    name: str = Field(..., description="Strategy name")
    description: str = Field(..., description="Strategy description")
    parameters: List[str] = Field(..., description="Required parameters")
