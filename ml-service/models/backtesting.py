"""
Backtesting and validation module for ML models
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import logging

from .ensemble_predictor import EnsemblePredictor
from .signal_predictor import SignalPredictor

logger = logging.getLogger(__name__)

class BacktestingEngine:
    """Engine for backtesting ML models on historical data"""
    
    def __init__(self, data_path: str = "data/historical_signals.csv"):
        self.data_path = data_path
        self.target_accuracy = 0.872  # 87.2% target
        self.models = {}
        self.results = {}
        
    def load_historical_data(self) -> pd.DataFrame:
        """Load historical signal data for backtesting"""
        try:
            if os.path.exists(self.data_path):
                df = pd.read_csv(self.data_path)
                logger.info(f"Loaded {len(df)} historical records")
                return df
            else:
                # Generate mock historical data for testing
                logger.warning("Historical data not found, generating mock data")
                return self._generate_mock_historical_data()
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return self._generate_mock_historical_data()
    
    def _generate_mock_historical_data(self) -> pd.DataFrame:
        """Generate mock historical data for backtesting"""
        np.random.seed(42)
        n_samples = 1000
        
        # Generate mock features
        data = {
            'timestamp': pd.date_range(start='2024-01-01', periods=n_samples, freq='H'),
            'price_change': np.random.normal(0, 0.02, n_samples),
            'volume_change': np.random.normal(0, 0.1, n_samples),
            'rsi': np.random.uniform(0, 100, n_samples),
            'macd': np.random.normal(0, 0.01, n_samples),
            'bollinger_position': np.random.uniform(-2, 2, n_samples),
            'signal_strength': np.random.uniform(0, 1, n_samples),
            'channel_rating': np.random.uniform(1, 5, n_samples),
            'subscriber_count': np.random.randint(100, 10000, n_samples),
            'success_rate': np.random.uniform(0.5, 0.9, n_samples)
        }
        
        # Generate target (successful signal = 1, failed = 0)
        # Higher signal_strength and channel_rating should correlate with success
        success_prob = (
            0.3 + 
            0.2 * data['signal_strength'] + 
            0.1 * (data['channel_rating'] / 5) +
            0.1 * (data['success_rate'] - 0.5) * 2
        )
        data['target'] = np.random.binomial(1, np.clip(success_prob, 0, 1))
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} mock historical records")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and target for ML models"""
        feature_columns = [
            'price_change', 'volume_change', 'rsi', 'macd', 
            'bollinger_position', 'signal_strength', 'channel_rating',
            'subscriber_count', 'success_rate'
        ]
        
        X = df[feature_columns].values
        y = df['target'].values
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        
        logger.info(f"Prepared features: {X.shape}, target: {y.shape}")
        return X, y
    
    def run_cross_validation(self, model, X: np.ndarray, y: np.ndarray, 
                           cv_splits: int = 5) -> Dict[str, float]:
        """Run time series cross-validation"""
        # Check if we have enough data for cross-validation
        if len(X) < cv_splits * 2:
            logger.warning(f"Insufficient data for {cv_splits} CV splits, using 2 splits")
            cv_splits = min(2, len(X) // 2)
        
        if cv_splits < 2:
            logger.warning("Insufficient data for cross-validation, returning single train/test split")
            # Fallback to single train/test split
            split_idx = len(X) // 2
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            
            return {
                'accuracy_mean': accuracy_score(y_val, y_pred),
                'precision_mean': precision_score(y_val, y_pred, zero_division=0),
                'recall_mean': recall_score(y_val, y_pred, zero_division=0),
                'f1_mean': f1_score(y_val, y_pred, zero_division=0),
                'accuracy_std': 0.0,
                'precision_std': 0.0,
                'recall_std': 0.0,
                'f1_std': 0.0
            }
        
        tscv = TimeSeriesSplit(n_splits=cv_splits)
        
        cv_scores = {
            'accuracy': [],
            'precision': [],
            'recall': [],
            'f1': []
        }
        
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Train model
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            
            # Calculate metrics
            cv_scores['accuracy'].append(accuracy_score(y_val, y_pred))
            cv_scores['precision'].append(precision_score(y_val, y_pred, zero_division=0))
            cv_scores['recall'].append(recall_score(y_val, y_pred, zero_division=0))
            cv_scores['f1'].append(f1_score(y_val, y_pred, zero_division=0))
        
        # Calculate mean and std
        results = {}
        for metric, scores in cv_scores.items():
            results[f'{metric}_mean'] = np.mean(scores)
            results[f'{metric}_std'] = np.std(scores)
        
        logger.info(f"Cross-validation results: {results}")
        return results
    
    def run_backtest(self, model, X: np.ndarray, y: np.ndarray, 
                    train_size: float = 0.8) -> Dict[str, Any]:
        """Run backtest on historical data"""
        # Split data chronologically
        split_idx = int(len(X) * train_size)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train model
        model.fit(X_train, y_train)
        
        # Predict on test set
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0)
        }
        
        # Detailed analysis
        report = classification_report(y_test, y_pred, output_dict=True)
        confusion = confusion_matrix(y_test, y_pred)
        
        results = {
            'metrics': metrics,
            'classification_report': report,
            'confusion_matrix': confusion.tolist(),
            'predictions': y_pred.tolist(),
            'probabilities': y_pred_proba.tolist() if y_pred_proba is not None else None,
            'test_size': len(X_test),
            'train_size': len(X_train)
        }
        
        logger.info(f"Backtest results - Accuracy: {metrics['accuracy']:.3f}")
        return results
    
    def test_ensemble_model(self) -> Dict[str, Any]:
        """Test ensemble model performance"""
        # Load data
        df = self.load_historical_data()
        X, y = self.prepare_features(df)
        
        # Initialize ensemble model
        ensemble = EnsemblePredictor()
        
        # Run cross-validation
        cv_results = self.run_cross_validation(ensemble, X, y)
        
        # Run backtest
        backtest_results = self.run_backtest(ensemble, X, y)
        
        # Check if target accuracy is achieved
        achieved_accuracy = backtest_results['metrics']['accuracy']
        target_met = achieved_accuracy >= self.target_accuracy
        
        results = {
            'ensemble_model': {
                'cv_results': cv_results,
                'backtest_results': backtest_results,
                'target_accuracy': self.target_accuracy,
                'achieved_accuracy': achieved_accuracy,
                'target_met': target_met
            }
        }
        
        logger.info(f"Ensemble model accuracy: {achieved_accuracy:.3f} "
                   f"(target: {self.target_accuracy:.3f}, met: {target_met})")
        
        return results
    
    def test_individual_models(self) -> Dict[str, Any]:
        """Test individual model performance"""
        df = self.load_historical_data()
        X, y = self.prepare_features(df)
        
        # Create individual model instances
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.neural_network import MLPClassifier
        
        models = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'neural_network': MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
        }
        
        # Note: XGBoost requires additional installation, so we'll skip it for now
        # 'xgboost': XGBClassifier(n_estimators=100, random_state=42)
        
        results = {}
        for name, model in models.items():
            logger.info(f"Testing {name}...")
            
            cv_results = self.run_cross_validation(model, X, y)
            backtest_results = self.run_backtest(model, X, y)
            
            results[name] = {
                'cv_results': cv_results,
                'backtest_results': backtest_results,
                'achieved_accuracy': backtest_results['metrics']['accuracy']
            }
        
        return results
    
    def continuous_retraining_pipeline(self, new_data: pd.DataFrame) -> Dict[str, Any]:
        """Continuous retraining pipeline for new data"""
        # Load existing model
        model_path = "models/ensemble_model.pkl"
        if os.path.exists(model_path):
            ensemble = joblib.load(model_path)
        else:
            ensemble = EnsemblePredictor()
        
        # Prepare new data
        X_new, y_new = self.prepare_features(new_data)
        
        # Retrain model
        ensemble.fit(X_new, y_new)
        
        # Evaluate on validation set
        validation_results = self.run_cross_validation(ensemble, X_new, y_new)
        
        # Save updated model
        os.makedirs("models", exist_ok=True)
        joblib.dump(ensemble, model_path)
        
        # Log retraining
        retraining_log = {
            'timestamp': datetime.now().isoformat(),
            'new_data_size': len(X_new),
            'validation_accuracy': validation_results['accuracy_mean'],
            'model_path': model_path
        }
        
        logger.info(f"Model retrained: {retraining_log}")
        return retraining_log
    
    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        # Test ensemble model
        ensemble_results = self.test_ensemble_model()
        
        # Test individual models
        individual_results = self.test_individual_models()
        
        # Generate report
        report = f"""
# ML Model Performance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Target Accuracy: {self.target_accuracy:.1%}

## Ensemble Model Performance
- Accuracy: {ensemble_results['ensemble_model']['achieved_accuracy']:.3f}
- Target Met: {ensemble_results['ensemble_model']['target_met']}
- Precision: {ensemble_results['ensemble_model']['backtest_results']['metrics']['precision']:.3f}
- Recall: {ensemble_results['ensemble_model']['backtest_results']['metrics']['recall']:.3f}
- F1-Score: {ensemble_results['ensemble_model']['backtest_results']['metrics']['f1']:.3f}

## Individual Model Performance
"""
        
        for name, results in individual_results.items():
            report += f"""
### {name.replace('_', ' ').title()}
- Accuracy: {results['achieved_accuracy']:.3f}
- CV Accuracy: {results['cv_results']['accuracy_mean']:.3f} ± {results['cv_results']['accuracy_std']:.3f}
"""
        
        report += f"""
## Recommendations
- {'✅ Target accuracy achieved! Model ready for production.' if ensemble_results['ensemble_model']['target_met'] else '❌ Target accuracy not met. Consider feature engineering or model tuning.'}
- Monitor model performance continuously
- Retrain model with new data regularly
"""
        
        return report


def main():
    """Main function for running backtesting"""
    engine = BacktestingEngine()
    
    # Generate performance report
    report = engine.generate_performance_report()
    print(report)
    
    # Save report
    with open("ml_performance_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("Performance report saved to ml_performance_report.md")


if __name__ == "__main__":
    main() 