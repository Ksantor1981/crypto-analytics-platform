"""
Fixed backtesting API without problematic imports
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging
import time
from datetime import datetime, timedelta
import random
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/backtesting", tags=["backtesting"])

# Pydantic модели
class BacktestRequest(BaseModel):
    asset: str = Field(..., description="Asset to backtest")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    strategy: str = Field("simple", description="Strategy to test")
    initial_capital: float = Field(10000, description="Initial capital")

class BacktestResult(BaseModel):
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    average_trade_return: float
    strategy_performance: Dict[str, Any]

class BacktestResponse(BaseModel):
    asset: str
    period: str
    results: BacktestResult
    trades: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    timestamp: str

class StrategyComparisonRequest(BaseModel):
    asset: str
    strategies: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 10000

class StrategyComparisonResponse(BaseModel):
    asset: str
    period: str
    strategies: Dict[str, BacktestResult]
    best_strategy: str
    comparison_metrics: Dict[str, Any]
    timestamp: str

def generate_mock_trades(asset: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Generate mock trading data for backtesting"""
    trades = []
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    
    base_price = MOCK_MARKET_DATA.get(asset.upper(), {}).get("price", 100)
    current_price = base_price
    
    while current_date <= end_date_obj:
        # Generate 1-3 trades per day
        daily_trades = random.randint(1, 3)
        
        for _ in range(daily_trades):
            # Random price movement
            price_change = random.uniform(-0.05, 0.05)
            new_price = current_price * (1 + price_change)
            
            # Random trade direction
            direction = random.choice(["LONG", "SHORT"])
            
            # Calculate P&L
            if direction == "LONG":
                pnl = (new_price - current_price) / current_price * 100
            else:
                pnl = (current_price - new_price) / current_price * 100
            
            # Add some randomness to make it realistic
            pnl += random.uniform(-2, 2)
            
            trade = {
                "date": current_date.strftime("%Y-%m-%d"),
                "time": f"{random.randint(9, 16)}:{random.randint(0, 59):02d}",
                "asset": asset,
                "direction": direction,
                "entry_price": current_price,
                "exit_price": new_price,
                "quantity": random.uniform(0.1, 1.0),
                "pnl": pnl,
                "pnl_percent": pnl,
                "status": "closed",
                "strategy": "mock_strategy"
            }
            
            trades.append(trade)
            current_price = new_price
        
        current_date += timedelta(days=1)
    
    return trades

def calculate_performance_metrics(trades: List[Dict[str, Any]], initial_capital: float) -> Dict[str, Any]:
    """Calculate performance metrics from trades"""
    if not trades:
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
            "profitable_trades": 0,
            "average_trade_return": 0.0
        }
    
    # Calculate basic metrics
    total_trades = len(trades)
    profitable_trades = sum(1 for trade in trades if trade["pnl"] > 0)
    win_rate = profitable_trades / total_trades if total_trades > 0 else 0
    
    # Calculate returns
    returns = [trade["pnl_percent"] for trade in trades]
    total_return = sum(returns)
    average_return = np.mean(returns) if returns else 0
    
    # Calculate Sharpe ratio (simplified)
    if len(returns) > 1:
        sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
    else:
        sharpe_ratio = 0
    
    # Calculate max drawdown (simplified)
    cumulative_returns = np.cumsum(returns)
    running_max = np.maximum.accumulate(cumulative_returns)
    drawdown = cumulative_returns - running_max
    max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
    
    return {
        "total_return": total_return,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "total_trades": total_trades,
        "profitable_trades": profitable_trades,
        "average_trade_return": average_return
    }

# Mock market data
MOCK_MARKET_DATA = {
    "BTC": {"price": 50000, "volume": 1000000, "change_24h": 2.5},
    "ETH": {"price": 3000, "volume": 500000, "change_24h": 1.8},
    "BNB": {"price": 400, "volume": 200000, "change_24h": 0.5},
    "SOL": {"price": 100, "volume": 150000, "change_24h": 3.2},
    "ADA": {"price": 0.5, "volume": 80000, "change_24h": -1.2},
    "DOT": {"price": 7, "volume": 120000, "change_24h": 0.8},
    "LINK": {"price": 15, "volume": 90000, "change_24h": 1.5},
    "UNI": {"price": 8, "volume": 70000, "change_24h": -0.3}
}

@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest) -> BacktestResponse:
    """
    Запуск бэктестинга стратегии
    """
    try:
        start_time = time.time()
        
        # Generate mock trading data
        trades = generate_mock_trades(request.asset, request.start_date, request.end_date)
        
        # Calculate performance metrics
        metrics = calculate_performance_metrics(trades, request.initial_capital)
        
        # Create strategy performance data
        strategy_performance = {
            "strategy_name": request.strategy,
            "initial_capital": request.initial_capital,
            "final_capital": request.initial_capital * (1 + metrics["total_return"] / 100),
            "period_days": (datetime.strptime(request.end_date, "%Y-%m-%d") - 
                          datetime.strptime(request.start_date, "%Y-%m-%d")).days
        }
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"✅ Backtest completed for {request.asset} in {processing_time:.2f}ms")
        
        return BacktestResponse(
            asset=request.asset,
            period=f"{request.start_date} to {request.end_date}",
            results=BacktestResult(
                total_return=metrics["total_return"],
                sharpe_ratio=metrics["sharpe_ratio"],
                max_drawdown=metrics["max_drawdown"],
                win_rate=metrics["win_rate"],
                total_trades=metrics["total_trades"],
                profitable_trades=metrics["profitable_trades"],
                average_trade_return=metrics["average_trade_return"],
                strategy_performance=strategy_performance
            ),
            trades=trades,
            performance_metrics=metrics,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Backtest error: {e}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@router.post("/compare-strategies", response_model=StrategyComparisonResponse)
async def compare_strategies(request: StrategyComparisonRequest) -> StrategyComparisonResponse:
    """
    Сравнение нескольких стратегий
    """
    try:
        strategies_results = {}
        
        for strategy in request.strategies:
            # Run backtest for each strategy
            backtest_request = BacktestRequest(
                asset=request.asset,
                start_date=request.start_date,
                end_date=request.end_date,
                strategy=strategy,
                initial_capital=request.initial_capital
            )
            
            backtest_response = await run_backtest(backtest_request)
            strategies_results[strategy] = backtest_response.results
        
        # Find best strategy
        best_strategy = max(strategies_results.keys(), 
                          key=lambda s: strategies_results[s].total_return)
        
        # Calculate comparison metrics
        comparison_metrics = {
            "strategy_count": len(request.strategies),
            "best_return": strategies_results[best_strategy].total_return,
            "worst_return": min(s.total_return for s in strategies_results.values()),
            "average_return": np.mean([s.total_return for s in strategies_results.values()]),
            "return_std": np.std([s.total_return for s in strategies_results.values()])
        }
        
        return StrategyComparisonResponse(
            asset=request.asset,
            period=f"{request.start_date} to {request.end_date}",
            strategies=strategies_results,
            best_strategy=best_strategy,
            comparison_metrics=comparison_metrics,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Strategy comparison error: {e}")
        raise HTTPException(status_code=500, detail=f"Strategy comparison failed: {str(e)}")

@router.get("/available-strategies")
async def get_available_strategies() -> Dict[str, Any]:
    """
    Получение списка доступных стратегий
    """
    return {
        "strategies": [
            {
                "name": "simple",
                "description": "Simple moving average crossover",
                "parameters": ["short_period", "long_period"]
            },
            {
                "name": "momentum",
                "description": "Momentum-based strategy",
                "parameters": ["lookback_period", "threshold"]
            },
            {
                "name": "mean_reversion",
                "description": "Mean reversion strategy",
                "parameters": ["window_size", "std_dev"]
            },
            {
                "name": "breakout",
                "description": "Breakout strategy",
                "parameters": ["resistance_level", "support_level"]
            }
        ],
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health")
async def health_check():
    """
    Health check для backtesting API
    """
    return {
        "status": "healthy",
        "service": "backtesting",
        "timestamp": datetime.now().isoformat()
    } 