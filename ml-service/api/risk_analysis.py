"""
Risk analysis API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from models.risk_scoring import RiskScoringEngine, RiskMetrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/risk-analysis", tags=["risk-analysis"])


class SignalData(BaseModel):
    """Signal data for risk analysis"""
    id: str
    price_history: List[float]
    success_rate: Optional[float] = 0.6
    avg_win: Optional[float] = 0.05
    avg_loss: Optional[float] = 0.03


class PortfolioRequest(BaseModel):
    """Request for portfolio optimization"""
    signals: List[SignalData]
    max_risk: Optional[float] = 50.0
    account_balance: Optional[float] = 10000.0


class PositionSizeRequest(BaseModel):
    """Request for position sizing"""
    signal: SignalData
    account_balance: float
    max_risk_per_trade: Optional[float] = 0.02


@router.post("/analyze-signal")
async def analyze_signal_risk(signal: SignalData):
    """Analyze risk for a single signal"""
    try:
        engine = RiskScoringEngine()
        
        signal_dict = signal.dict()
        risk_metrics = engine.analyze_signal_risk(signal_dict)
        
        return {
            "status": "success",
            "signal_id": signal.id,
            "risk_metrics": {
                "risk_score": risk_metrics.risk_score,
                "volatility": risk_metrics.volatility,
                "sharpe_ratio": risk_metrics.sharpe_ratio,
                "max_drawdown": risk_metrics.max_drawdown,
                "var_95": risk_metrics.var_95,
                "expected_return": risk_metrics.expected_return,
                "confidence_interval": risk_metrics.confidence_interval
            },
            "risk_level": "Low" if risk_metrics.risk_score < 30 else 
                         "Medium" if risk_metrics.risk_score < 70 else "High"
        }
    except Exception as e:
        logger.error(f"Error analyzing signal risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-portfolio")
async def optimize_portfolio(request: PortfolioRequest):
    """Optimize portfolio allocation"""
    try:
        engine = RiskScoringEngine()
        
        # Convert to list of dictionaries
        signals = [signal.dict() for signal in request.signals]
        
        portfolio = engine.optimize_portfolio(
            signals, 
            max_risk=request.max_risk
        )
        
        return {
            "status": "success",
            "portfolio": portfolio,
            "recommendations": {
                "max_risk_met": portfolio.get('risk_constraint_met', False),
                "diversification_score": portfolio.get('portfolio_metrics', {}).get('diversification_score', 0),
                "suggested_actions": _generate_portfolio_recommendations(portfolio)
            }
        }
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-position-size")
async def calculate_position_size(request: PositionSizeRequest):
    """Calculate optimal position size"""
    try:
        engine = RiskScoringEngine()
        
        signal_dict = request.signal.dict()
        position_data = engine.calculate_position_size(
            signal_dict,
            request.account_balance,
            request.max_risk_per_trade
        )
        
        return {
            "status": "success",
            "position_data": position_data,
            "recommendations": _generate_position_recommendations(position_data)
        }
    except Exception as e:
        logger.error(f"Error calculating position size: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-risk-report")
async def generate_risk_report(request: PortfolioRequest):
    """Generate comprehensive risk report"""
    try:
        engine = RiskScoringEngine()
        
        signals = [signal.dict() for signal in request.signals]
        report = engine.generate_risk_report(signals)
        
        return {
            "status": "success",
            "report": report,
            "summary": _extract_report_summary(report)
        }
    except Exception as e:
        logger.error(f"Error generating risk report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-metrics/{signal_id}")
async def get_signal_risk_metrics(signal_id: str):
    """Get risk metrics for a specific signal (mock data)"""
    try:
        # Mock data for demonstration
        mock_metrics = {
            "risk_score": 45.2,
            "volatility": 0.25,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.15,
            "var_95": -0.08,
            "expected_return": 0.18,
            "confidence_interval": [0.12, 0.24]
        }
        
        return {
            "status": "success",
            "signal_id": signal_id,
            "risk_metrics": mock_metrics,
            "risk_level": "Medium"
        }
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio-risk-summary")
async def get_portfolio_risk_summary():
    """Get portfolio risk summary (mock data)"""
    try:
        # Mock portfolio summary
        summary = {
            "total_signals": 5,
            "average_risk_score": 42.3,
            "portfolio_volatility": 0.18,
            "portfolio_sharpe": 1.45,
            "max_portfolio_drawdown": 0.12,
            "diversification_score": 0.78,
            "risk_distribution": {
                "low_risk": 2,
                "medium_risk": 2,
                "high_risk": 1
            }
        }
        
        return {
            "status": "success",
            "portfolio_summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_portfolio_recommendations(portfolio: Dict[str, Any]) -> List[str]:
    """Generate portfolio recommendations"""
    recommendations = []
    
    if not portfolio.get('risk_constraint_met', False):
        recommendations.append("Consider reducing high-risk positions to meet risk constraints")
    
    diversification = portfolio.get('portfolio_metrics', {}).get('diversification_score', 0)
    if diversification < 0.7:
        recommendations.append("Increase portfolio diversification")
    
    if diversification > 0.9:
        recommendations.append("Portfolio is well diversified")
    
    return recommendations


def _generate_position_recommendations(position_data: Dict[str, Any]) -> List[str]:
    """Generate position sizing recommendations"""
    recommendations = []
    
    position_pct = position_data.get('position_percentage', 0)
    risk_score = position_data.get('risk_metrics', {}).get('risk_score', 0)
    
    if position_pct > 0.1:
        recommendations.append("Consider reducing position size for better risk management")
    
    if risk_score > 70:
        recommendations.append("High risk signal - consider smaller position or skip")
    
    if risk_score < 30:
        recommendations.append("Low risk signal - position size looks appropriate")
    
    return recommendations


def _extract_report_summary(report: str) -> Dict[str, Any]:
    """Extract key metrics from risk report"""
    # Simple parsing for demonstration
    lines = report.split('\n')
    summary = {
        "total_signals": 0,
        "average_risk_score": 0.0,
        "high_risk_signals": 0,
        "low_risk_signals": 0
    }
    
    for line in lines:
        if "Risk Score:" in line:
            try:
                risk_score = float(line.split(':')[1].split('/')[0].strip())
                summary["average_risk_score"] += risk_score
                summary["total_signals"] += 1
                
                if risk_score > 70:
                    summary["high_risk_signals"] += 1
                elif risk_score < 30:
                    summary["low_risk_signals"] += 1
            except:
                pass
    
    if summary["total_signals"] > 0:
        summary["average_risk_score"] /= summary["total_signals"]
    
    return summary 