"""
Fixed risk analysis API without problematic imports
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging
import time
from datetime import datetime
import random
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/risk-analysis", tags=["risk-analysis"])

# Pydantic модели
class RiskAnalysisRequest(BaseModel):
    asset: str = Field(..., description="Asset symbol")
    position_size: float = Field(..., description="Position size in USD")
    entry_price: float = Field(..., description="Entry price")
    stop_loss: float = Field(None, description="Stop loss price")
    take_profit: float = Field(None, description="Take profit price")
    direction: str = Field("LONG", description="Position direction")
    risk_tolerance: str = Field("MEDIUM", description="Risk tolerance level")

class RiskMetrics(BaseModel):
    position_risk: float
    portfolio_risk: float
    var_95: float  # Value at Risk 95%
    expected_shortfall: float
    sharpe_ratio: float
    max_drawdown: float
    risk_reward_ratio: float
    position_correlation: float

class RiskAnalysisResponse(BaseModel):
    asset: str
    risk_level: str
    risk_score: float
    metrics: RiskMetrics
    recommendations: List[str]
    warnings: List[str]
    timestamp: str

class PortfolioRiskRequest(BaseModel):
    positions: List[Dict[str, Any]]
    total_capital: float
    risk_tolerance: str = "MEDIUM"

class PortfolioRiskResponse(BaseModel):
    total_portfolio_risk: float
    portfolio_var: float
    diversification_score: float
    risk_contributions: Dict[str, float]
    recommendations: List[str]
    timestamp: str

def calculate_position_risk(entry_price: float, stop_loss: float, position_size: float, direction: str) -> float:
    """Calculate position risk"""
    if not stop_loss:
        return 0.02  # Default 2% risk
    
    if direction == "LONG":
        risk_per_share = entry_price - stop_loss
    else:
        risk_per_share = stop_loss - entry_price
    
    shares = position_size / entry_price
    total_risk = risk_per_share * shares
    risk_percentage = (total_risk / position_size) * 100
    
    return max(0, risk_percentage)

def calculate_var(returns: List[float], confidence: float = 0.95) -> float:
    """Calculate Value at Risk"""
    if not returns:
        return 0.0
    
    sorted_returns = sorted(returns)
    index = int((1 - confidence) * len(sorted_returns))
    return abs(sorted_returns[index]) if index < len(sorted_returns) else 0.0

def generate_mock_returns(asset: str, days: int = 252) -> List[float]:
    """Generate mock daily returns for risk calculation"""
    # Different volatility for different assets
    volatility_map = {
        "BTC": 0.04,
        "ETH": 0.05,
        "BNB": 0.06,
        "SOL": 0.08,
        "ADA": 0.07,
        "DOT": 0.06,
        "LINK": 0.07,
        "UNI": 0.06
    }
    
    volatility = volatility_map.get(asset.upper(), 0.05)
    returns = np.random.normal(0.001, volatility, days)  # Daily returns
    
    return returns.tolist()

@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_risk(request: RiskAnalysisRequest) -> RiskAnalysisResponse:
    """
    Анализ риска для позиции
    """
    try:
        start_time = time.time()
        
        # Calculate position risk
        position_risk = calculate_position_risk(
            request.entry_price, 
            request.stop_loss, 
            request.position_size, 
            request.direction
        )
        
        # Generate mock returns for risk calculations
        returns = generate_mock_returns(request.asset)
        
        # Calculate risk metrics
        var_95 = calculate_var(returns, 0.95)
        expected_shortfall = np.mean([r for r in returns if r < -var_95]) if any(r < -var_95 for r in returns) else 0
        
        # Calculate Sharpe ratio (simplified)
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate max drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = cumulative_returns - running_max
        max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
        
        # Calculate risk/reward ratio
        risk_reward_ratio = 0.0
        if request.take_profit and request.stop_loss:
            if request.direction == "LONG":
                reward = request.take_profit - request.entry_price
                risk = request.entry_price - request.stop_loss
            else:
                reward = request.entry_price - request.take_profit
                risk = request.stop_loss - request.entry_price
            
            if risk > 0:
                risk_reward_ratio = reward / risk
        
        # Determine risk level
        risk_score = position_risk + var_95 * 100 + max_drawdown * 100
        
        if risk_score < 5:
            risk_level = "LOW"
        elif risk_score < 15:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Generate recommendations
        recommendations = []
        warnings = []
        
        if position_risk > 5:
            warnings.append("Position risk is high (>5%). Consider reducing position size.")
        
        if risk_reward_ratio < 1.5:
            recommendations.append("Risk/reward ratio is low. Consider adjusting take profit or stop loss.")
        
        if var_95 > 0.05:
            warnings.append("High Value at Risk. Consider hedging or reducing exposure.")
        
        if max_drawdown > 0.1:
            warnings.append("High maximum drawdown potential. Monitor position closely.")
        
        if risk_level == "LOW":
            recommendations.append("Risk level is acceptable for most investors.")
        elif risk_level == "MEDIUM":
            recommendations.append("Moderate risk level. Suitable for experienced traders.")
        else:
            recommendations.append("High risk level. Only for aggressive traders with proper risk management.")
        
        # Add asset-specific recommendations
        if request.asset.upper() in ["BTC", "ETH"]:
            recommendations.append("Major cryptocurrency with lower volatility compared to altcoins.")
        else:
            recommendations.append("Altcoin with higher volatility. Consider smaller position sizes.")
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"✅ Risk analysis completed for {request.asset} in {processing_time:.2f}ms")
        
        return RiskAnalysisResponse(
            asset=request.asset,
            risk_level=risk_level,
            risk_score=risk_score,
            metrics=RiskMetrics(
                position_risk=position_risk,
                portfolio_risk=position_risk,  # Simplified for single position
                var_95=var_95,
                expected_shortfall=expected_shortfall,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                risk_reward_ratio=risk_reward_ratio,
                position_correlation=0.5  # Mock correlation
            ),
            recommendations=recommendations,
            warnings=warnings,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Risk analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")

@router.post("/portfolio", response_model=PortfolioRiskResponse)
async def analyze_portfolio_risk(request: PortfolioRiskRequest) -> PortfolioRiskResponse:
    """
    Анализ риска портфеля
    """
    try:
        start_time = time.time()
        
        total_capital = request.total_capital
        portfolio_risk = 0.0
        risk_contributions = {}
        
        # Calculate individual position risks
        for position in request.positions:
            asset = position.get("asset", "UNKNOWN")
            position_size = position.get("position_size", 0)
            entry_price = position.get("entry_price", 1)
            stop_loss = position.get("stop_loss", entry_price * 0.95)
            direction = position.get("direction", "LONG")
            
            # Calculate position risk
            pos_risk = calculate_position_risk(entry_price, stop_loss, position_size, direction)
            portfolio_risk += pos_risk * (position_size / total_capital)
            
            risk_contributions[asset] = pos_risk
        
        # Calculate portfolio VaR (simplified)
        portfolio_var = portfolio_risk * total_capital * 0.02  # 2% daily VaR
        
        # Calculate diversification score
        position_count = len(request.positions)
        if position_count > 1:
            # Simple diversification score based on number of positions
            diversification_score = min(0.9, 0.3 + (position_count * 0.1))
        else:
            diversification_score = 0.3
        
        # Generate recommendations
        recommendations = []
        
        if portfolio_risk > 0.1:
            recommendations.append("Portfolio risk is high. Consider reducing position sizes.")
        
        if diversification_score < 0.5:
            recommendations.append("Low diversification. Consider adding more assets to portfolio.")
        
        if position_count < 3:
            recommendations.append("Portfolio has few positions. Consider diversification.")
        
        if portfolio_var > total_capital * 0.05:
            recommendations.append("High portfolio VaR. Consider risk management strategies.")
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"✅ Portfolio risk analysis completed in {processing_time:.2f}ms")
        
        return PortfolioRiskResponse(
            total_portfolio_risk=portfolio_risk,
            portfolio_var=portfolio_var,
            diversification_score=diversification_score,
            risk_contributions=risk_contributions,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Portfolio risk analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Portfolio risk analysis failed: {str(e)}")

@router.get("/risk-metrics/{asset}")
async def get_risk_metrics(asset: str) -> Dict[str, Any]:
    """
    Получение метрик риска для актива
    """
    try:
        # Generate mock risk metrics
        returns = generate_mock_returns(asset)
        
        metrics = {
            "asset": asset.upper(),
            "volatility": np.std(returns) * np.sqrt(252),  # Annualized volatility
            "var_95": calculate_var(returns, 0.95),
            "var_99": calculate_var(returns, 0.99),
            "sharpe_ratio": np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0,
            "max_drawdown": abs(np.min(np.cumsum(returns) - np.maximum.accumulate(np.cumsum(returns)))),
            "beta": random.uniform(0.8, 1.2),  # Mock beta
            "correlation_btc": random.uniform(0.3, 0.9),  # Mock correlation with BTC
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Risk metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk metrics: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check для risk analysis API
    """
    return {
        "status": "healthy",
        "service": "risk-analysis",
        "timestamp": datetime.now().isoformat()
    } 