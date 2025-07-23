"""
Backtesting API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import pandas as pd
import logging

from models.backtesting import BacktestingEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backtesting", tags=["backtesting"])


class BacktestRequest(BaseModel):
    """Request model for backtesting"""
    data_path: Optional[str] = None
    cv_splits: int = 5
    train_size: float = 0.8


class RetrainingRequest(BaseModel):
    """Request model for continuous retraining"""
    new_data: Dict[str, Any]  # JSON data for new training samples


@router.post("/run-ensemble-test")
async def run_ensemble_backtest(request: BacktestRequest):
    """Run backtest on ensemble model"""
    try:
        engine = BacktestingEngine(
            data_path=request.data_path if request.data_path else "data/historical_signals.csv"
        )
        
        results = engine.test_ensemble_model()
        
        return {
            "status": "success",
            "results": results,
            "target_accuracy": engine.target_accuracy,
            "achieved_accuracy": results['ensemble_model']['achieved_accuracy'],
            "target_met": results['ensemble_model']['target_met']
        }
    except Exception as e:
        logger.error(f"Error in ensemble backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-individual-tests")
async def run_individual_model_tests(request: BacktestRequest):
    """Run backtest on individual models"""
    try:
        engine = BacktestingEngine(
            data_path=request.data_path if request.data_path else "data/historical_signals.csv"
        )
        
        results = engine.test_individual_models()
        
        return {
            "status": "success",
            "results": results,
            "target_accuracy": engine.target_accuracy
        }
    except Exception as e:
        logger.error(f"Error in individual model tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-report")
async def generate_performance_report(request: BacktestRequest):
    """Generate comprehensive performance report"""
    try:
        engine = BacktestingEngine(
            data_path=request.data_path if request.data_path else "data/historical_signals.csv"
        )
        
        report = engine.generate_performance_report()
        
        return {
            "status": "success",
            "report": report,
            "target_accuracy": engine.target_accuracy
        }
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continuous-retraining")
async def continuous_retraining(
    request: RetrainingRequest, 
    background_tasks: BackgroundTasks
):
    """Continuous retraining with new data"""
    try:
        # Convert JSON data to DataFrame
        new_data = pd.DataFrame(request.new_data)
        
        engine = BacktestingEngine()
        
        # Run retraining in background
        def retrain_model():
            try:
                return engine.continuous_retraining_pipeline(new_data)
            except Exception as e:
                logger.error(f"Background retraining failed: {e}")
        
        background_tasks.add_task(retrain_model)
        
        return {
            "status": "success",
            "message": "Retraining started in background",
            "new_data_size": len(new_data)
        }
    except Exception as e:
        logger.error(f"Error in continuous retraining: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accuracy-status")
async def get_accuracy_status():
    """Get current accuracy status vs target"""
    try:
        engine = BacktestingEngine()
        
        # Quick test with minimal data
        df = engine.load_historical_data()
        if len(df) < 100:  # Need minimum data
            return {
                "status": "insufficient_data",
                "message": "Need at least 100 historical records for testing",
                "target_accuracy": engine.target_accuracy
            }
        
        X, y = engine.prepare_features(df)
        ensemble = engine.test_ensemble_model()
        
        achieved = ensemble['ensemble_model']['achieved_accuracy']
        target_met = ensemble['ensemble_model']['target_met']
        
        return {
            "status": "success",
            "target_accuracy": engine.target_accuracy,
            "achieved_accuracy": achieved,
            "target_met": target_met,
            "accuracy_gap": engine.target_accuracy - achieved,
            "recommendation": "Model ready for production" if target_met else "Consider feature engineering or tuning"
        }
    except Exception as e:
        logger.error(f"Error getting accuracy status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-performance-summary")
async def get_model_performance_summary():
    """Get summary of all model performances"""
    try:
        engine = BacktestingEngine()
        
        # Test all models
        ensemble_results = engine.test_ensemble_model()
        individual_results = engine.test_individual_models()
        
        summary = {
            "target_accuracy": engine.target_accuracy,
            "ensemble": {
                "accuracy": ensemble_results['ensemble_model']['achieved_accuracy'],
                "target_met": ensemble_results['ensemble_model']['target_met']
            },
            "individual_models": {}
        }
        
        for name, results in individual_results.items():
            summary["individual_models"][name] = {
                "accuracy": results['achieved_accuracy'],
                "cv_accuracy_mean": results['cv_results']['accuracy_mean'],
                "cv_accuracy_std": results['cv_results']['accuracy_std']
            }
        
        return {
            "status": "success",
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 