"""
ML Prediction API Endpoints - Pro feature
Part of Task 2.3.2: Pro функции
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.user import User
from ...core.auth import get_current_user
from ...services.ml_prediction_service import ml_prediction_service
from ...middleware.rbac_middleware import require_subscription_plan, SubscriptionPlan

router = APIRouter()

@router.get("/ml/price-prediction/{symbol}")
async def get_price_prediction(
    symbol: str,
    timeframe: str = Query("24h", description="Prediction timeframe: 1h, 4h, 24h, 7d"),
    model_type: str = Query("price_trend", description="Model type: price_trend, volatility, signal_confidence, market_sentiment, risk_assessment"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get ML-based price prediction for a cryptocurrency
    Pro feature - requires Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PRO)
    
    try:
        prediction = await ml_prediction_service.get_price_prediction(
            user=current_user,
            db=db,
            symbol=symbol.upper(),
            timeframe=timeframe,
            model_type=model_type
        )
        
        return {
            "success": True,
            "data": prediction
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate prediction: {str(e)}"
        )

@router.get("/ml/portfolio-analysis")
async def get_portfolio_analysis(
    analysis_type: str = Query("comprehensive", description="Analysis type: comprehensive, performance, risk"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive ML-based portfolio analysis
    Pro feature - requires Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PRO)
    
    try:
        analysis = await ml_prediction_service.get_portfolio_analysis(
            user=current_user,
            db=db,
            analysis_type=analysis_type
        )
        
        return {
            "success": True,
            "data": analysis
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate portfolio analysis: {str(e)}"
        )

@router.get("/ml/market-insights")
async def get_market_insights(
    market_type: str = Query("crypto", description="Market type: crypto, forex, stocks"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get advanced ML-based market insights
    Pro feature - requires Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PRO)
    
    try:
        insights = await ml_prediction_service.get_market_insights(
            user=current_user,
            db=db,
            market_type=market_type
        )
        
        return {
            "success": True,
            "data": insights
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate market insights: {str(e)}"
        )

@router.get("/ml/models")
async def get_available_models(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available ML models and their descriptions
    Pro feature - requires Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PRO)
    
    return {
        "success": True,
        "data": {
            "prediction_models": {
                "price_trend": {
                    "name": "Price Trend Prediction",
                    "description": "Predicts short to medium-term price movements",
                    "timeframes": ["1h", "4h", "24h", "7d"],
                    "accuracy": "75-85%"
                },
                "volatility": {
                    "name": "Volatility Analysis",
                    "description": "Analyzes price volatility and risk levels",
                    "timeframes": ["24h", "7d", "30d"],
                    "accuracy": "70-80%"
                },
                "signal_confidence": {
                    "name": "Signal Confidence Enhancement",
                    "description": "Enhances trading signal confidence using ML",
                    "timeframes": ["real-time"],
                    "accuracy": "80-90%"
                },
                "market_sentiment": {
                    "name": "Market Sentiment Analysis",
                    "description": "Analyzes overall market sentiment and mood",
                    "timeframes": ["24h", "7d"],
                    "accuracy": "65-75%"
                },
                "risk_assessment": {
                    "name": "Risk Assessment Model",
                    "description": "Comprehensive risk analysis for investments",
                    "timeframes": ["real-time", "7d", "30d"],
                    "accuracy": "70-85%"
                }
            },
            "analysis_types": {
                "portfolio_analysis": [
                    "comprehensive",
                    "performance",
                    "risk",
                    "diversification"
                ],
                "market_insights": [
                    "trends",
                    "sentiment",
                    "volatility",
                    "opportunities"
                ]
            },
            "disclaimer": "ML predictions are for informational purposes only and should not be considered as financial advice."
        }
    }
