"""
Backtesting API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
# import pandas as pd
# import numpy as np

from ...core.database import get_db
from ...models.signal import Signal, SignalDirection, SignalStatus
from ...schemas.backtesting import (
    BacktestingRequest,
    BacktestingResponse,
    StrategyResult,
    SignalPerformance
)

router = APIRouter()

@router.post("/strategy", response_model=BacktestingResponse)
async def backtest_strategy(
    request: BacktestingRequest,
    db: Session = Depends(get_db)
):
    """
    Backtest trading strategy on historical signals
    """
    try:
        # Получаем сигналы для backtesting
        signals = db.query(Signal).filter(
            Signal.created_at >= request.start_date,
            Signal.created_at <= request.end_date,
            Signal.asset.in_(request.assets) if request.assets else True
        ).all()
        
        if not signals:
            raise HTTPException(status_code=404, detail="No signals found for the specified period")
        
        # Выполняем backtesting
        results = perform_backtesting(signals, request.strategy, request.parameters)
        
        return BacktestingResponse(
            strategy=request.strategy,
            start_date=request.start_date,
            end_date=request.end_date,
            total_signals=len(signals),
            results=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtesting failed: {str(e)}")

@router.get("/strategies")
async def get_available_strategies():
    """
    Get list of available backtesting strategies
    """
    strategies = [
        {
            "name": "momentum",
            "description": "Momentum-based strategy using signal strength and market conditions",
            "parameters": ["lookback_period", "threshold"]
        },
        {
            "name": "mean_reversion",
            "description": "Mean reversion strategy based on price deviations",
            "parameters": ["deviation_threshold", "holding_period"]
        },
        {
            "name": "signal_quality",
            "description": "Strategy based on signal quality metrics",
            "parameters": ["min_confidence", "min_risk_reward"]
        }
    ]
    return {"strategies": strategies}

def perform_backtesting(signals: List[Signal], strategy: str, parameters: dict) -> StrategyResult:
    """
    Perform backtesting on signals using specified strategy
    """
    if strategy == "momentum":
        return momentum_strategy(signals, parameters)
    elif strategy == "mean_reversion":
        return mean_reversion_strategy(signals, parameters)
    elif strategy == "signal_quality":
        return signal_quality_strategy(signals, parameters)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

def momentum_strategy(signals: List[Signal], parameters: dict) -> StrategyResult:
    """
    Momentum-based strategy implementation
    """
    lookback_period = parameters.get("lookback_period", 7)
    threshold = parameters.get("threshold", 0.7)
    
    # Фильтруем сигналы по условиям стратегии
    filtered_signals = []
    for signal in signals:
        if signal.ml_success_probability and signal.ml_success_probability >= threshold:
            filtered_signals.append(signal)
    
    # Рассчитываем метрики
    total_signals = len(filtered_signals)
    successful_signals = len([s for s in filtered_signals if s.is_successful])
    success_rate = successful_signals / total_signals if total_signals > 0 else 0
    
    # Рассчитываем ROI
    total_roi = sum([s.profit_loss_percentage or 0 for s in filtered_signals])
    avg_roi = total_roi / total_signals if total_signals > 0 else 0
    
    return StrategyResult(
        total_signals=total_signals,
        successful_signals=successful_signals,
        success_rate=success_rate,
        total_roi=total_roi,
        avg_roi=avg_roi,
        max_drawdown=calculate_max_drawdown(filtered_signals),
        sharpe_ratio=calculate_sharpe_ratio(filtered_signals)
    )

def mean_reversion_strategy(signals: List[Signal], parameters: dict) -> StrategyResult:
    """
    Mean reversion strategy implementation
    """
    deviation_threshold = parameters.get("deviation_threshold", 0.1)
    holding_period = parameters.get("holding_period", 24)
    
    # Фильтруем сигналы по условиям стратегии
    filtered_signals = []
    for signal in signals:
        if signal.risk_reward_ratio and signal.risk_reward_ratio >= deviation_threshold:
            filtered_signals.append(signal)
    
    # Рассчитываем метрики
    total_signals = len(filtered_signals)
    successful_signals = len([s for s in filtered_signals if s.is_successful])
    success_rate = successful_signals / total_signals if total_signals > 0 else 0
    
    total_roi = sum([s.profit_loss_percentage or 0 for s in filtered_signals])
    avg_roi = total_roi / total_signals if total_signals > 0 else 0
    
    return StrategyResult(
        total_signals=total_signals,
        successful_signals=successful_signals,
        success_rate=success_rate,
        total_roi=total_roi,
        avg_roi=avg_roi,
        max_drawdown=calculate_max_drawdown(filtered_signals),
        sharpe_ratio=calculate_sharpe_ratio(filtered_signals)
    )

def signal_quality_strategy(signals: List[Signal], parameters: dict) -> StrategyResult:
    """
    Signal quality-based strategy implementation
    """
    min_confidence = parameters.get("min_confidence", 80)
    min_risk_reward = parameters.get("min_risk_reward", 2.0)
    
    # Фильтруем сигналы по качеству
    filtered_signals = []
    for signal in signals:
        if (signal.confidence_score and signal.confidence_score >= min_confidence and
            signal.risk_reward_ratio and signal.risk_reward_ratio >= min_risk_reward):
            filtered_signals.append(signal)
    
    # Рассчитываем метрики
    total_signals = len(filtered_signals)
    successful_signals = len([s for s in filtered_signals if s.is_successful])
    success_rate = successful_signals / total_signals if total_signals > 0 else 0
    
    total_roi = sum([s.profit_loss_percentage or 0 for s in filtered_signals])
    avg_roi = total_roi / total_signals if total_signals > 0 else 0
    
    return StrategyResult(
        total_signals=total_signals,
        successful_signals=successful_signals,
        success_rate=success_rate,
        total_roi=total_roi,
        avg_roi=avg_roi,
        max_drawdown=calculate_max_drawdown(filtered_signals),
        sharpe_ratio=calculate_sharpe_ratio(filtered_signals)
    )

def calculate_max_drawdown(signals: List[Signal]) -> float:
    """Calculate maximum drawdown"""
    if not signals:
        return 0.0
    
    cumulative_returns = []
    cumulative = 0
    for signal in signals:
        roi = signal.profit_loss_percentage or 0
        cumulative += roi
        cumulative_returns.append(cumulative)
    
    if not cumulative_returns:
        return 0.0
    
    # Calculate drawdown
    peak = cumulative_returns[0]
    max_dd = 0
    
    for value in cumulative_returns:
        if value > peak:
            peak = value
        dd = (peak - value) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)
    
    return max_dd

def calculate_sharpe_ratio(signals: List[Signal]) -> float:
    """Calculate Sharpe ratio"""
    if not signals:
        return 0.0
    
    returns = [s.profit_loss_percentage or 0 for s in signals]
    if not returns:
        return 0.0
    
    # Calculate mean
    avg_return = sum(returns) / len(returns)
    
    # Calculate standard deviation
    variance = sum((x - avg_return) ** 2 for x in returns) / len(returns)
    std_return = variance ** 0.5
    
    if std_return == 0:
        return 0.0
    
    # Assuming risk-free rate of 0 for simplicity
    sharpe = avg_return / std_return
    return sharpe
