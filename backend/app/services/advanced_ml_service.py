"""
Advanced ML Service - Core ML system for signal analysis and predictions
Part of Task 3.2: Продвинутая ML система
"""
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import joblib
import os

from ..models.signal import Signal, SignalStatus
from ..models.channel import Channel
from ..services.channel_metrics_service import channel_metrics_service

logger = logging.getLogger(__name__)

class AdvancedMLService:
    """
    Advanced ML service for signal analysis and channel predictions
    Core business logic: ML-powered signal confidence and channel rating predictions
    """
    
    def __init__(self):
        self.models = {
            'signal_confidence': None,
            'channel_rating': None,
            'price_prediction': None,
            'risk_assessment': None
        }
        
        self.scalers = {
            'signal_features': StandardScaler(),
            'channel_features': StandardScaler(),
            'price_features': StandardScaler()
        }
        
        self.model_metrics = {
            'signal_confidence': {'accuracy': 0.0, 'last_trained': None},
            'channel_rating': {'mse': 0.0, 'last_trained': None},
            'price_prediction': {'mse': 0.0, 'last_trained': None}
        }
        
        self.feature_importance = {}
        self.models_dir = "ml_models"
        
        # Create models directory
        os.makedirs(self.models_dir, exist_ok=True)
    
    async def train_signal_confidence_model(self, db: Session) -> Dict[str, Any]:
        """
        Train ML model to predict signal confidence and success probability
        """
        try:
            logger.info("Starting signal confidence model training...")
            
            # Get training data
            signals = db.query(Signal).filter(
                Signal.status.in_([SignalStatus.COMPLETED, SignalStatus.STOPPED])
            ).limit(10000).all()
            
            if len(signals) < 100:
                return {"error": "Insufficient training data", "signals_count": len(signals)}
            
            # Extract features and labels
            features, labels = self._extract_signal_features(signals)
            
            if len(features) == 0:
                return {"error": "No valid features extracted"}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, labels, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scalers['signal_features'].fit_transform(X_train)
            X_test_scaled = self.scalers['signal_features'].transform(X_test)
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            self.models['signal_confidence'] = model
            self._save_model('signal_confidence', model)
            self._save_scaler('signal_features', self.scalers['signal_features'])
            
            # Update metrics
            self.model_metrics['signal_confidence'] = {
                'accuracy': accuracy,
                'last_trained': datetime.utcnow(),
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            # Feature importance
            feature_names = self._get_signal_feature_names()
            self.feature_importance['signal_confidence'] = dict(
                zip(feature_names, model.feature_importances_)
            )
            
            logger.info(f"Signal confidence model trained. Accuracy: {accuracy:.3f}")
            
            return {
                "success": True,
                "accuracy": accuracy,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "feature_importance": self.feature_importance['signal_confidence']
            }
            
        except Exception as e:
            logger.error(f"Error training signal confidence model: {e}")
            return {"error": str(e)}
    
    async def train_channel_rating_model(self, db: Session) -> Dict[str, Any]:
        """
        Train ML model to predict channel ratings
        """
        try:
            logger.info("Starting channel rating model training...")
            
            # Get channels with sufficient data
            channels = db.query(Channel).all()
            
            channel_data = []
            for channel in channels:
                metrics = await channel_metrics_service.calculate_channel_metrics(
                    channel, db, period_days=90
                )
                
                if metrics['total_signals'] >= 10:  # Minimum signals for training
                    channel_data.append((channel, metrics))
            
            if len(channel_data) < 20:
                return {"error": "Insufficient channel data", "channels_count": len(channel_data)}
            
            # Extract features and labels
            features, labels = self._extract_channel_features(channel_data)
            
            # Split and scale
            X_train, X_test, y_train, y_test = train_test_split(
                features, labels, test_size=0.2, random_state=42
            )
            
            X_train_scaled = self.scalers['channel_features'].fit_transform(X_train)
            X_test_scaled = self.scalers['channel_features'].transform(X_test)
            
            # Train model
            model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            
            # Save model
            self.models['channel_rating'] = model
            self._save_model('channel_rating', model)
            self._save_scaler('channel_features', self.scalers['channel_features'])
            
            # Update metrics
            self.model_metrics['channel_rating'] = {
                'mse': mse,
                'last_trained': datetime.utcnow(),
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            logger.info(f"Channel rating model trained. MSE: {mse:.3f}")
            
            return {
                "success": True,
                "mse": mse,
                "training_samples": len(X_train),
                "test_samples": len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error training channel rating model: {e}")
            return {"error": str(e)}
    
    async def predict_signal_success(self, signal_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict signal success probability using trained model
        """
        try:
            if not self.models['signal_confidence']:
                await self._load_model('signal_confidence')
            
            if not self.models['signal_confidence']:
                return {"error": "Signal confidence model not available"}
            
            # Convert features to array
            feature_array = self._signal_features_to_array(signal_features)
            feature_scaled = self.scalers['signal_features'].transform([feature_array])
            
            # Predict
            success_probability = self.models['signal_confidence'].predict_proba(feature_scaled)[0]
            prediction = self.models['signal_confidence'].predict(feature_scaled)[0]
            
            return {
                "success_probability": float(success_probability[1]),  # Probability of success
                "predicted_outcome": bool(prediction),
                "confidence_score": float(max(success_probability)),
                "model_accuracy": self.model_metrics['signal_confidence'].get('accuracy', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error predicting signal success: {e}")
            return {"error": str(e)}
    
    async def predict_channel_rating(self, channel_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict channel rating using trained model
        """
        try:
            if not self.models['channel_rating']:
                await self._load_model('channel_rating')
            
            if not self.models['channel_rating']:
                return {"error": "Channel rating model not available"}
            
            # Convert features to array
            feature_array = self._channel_features_to_array(channel_features)
            feature_scaled = self.scalers['channel_features'].transform([feature_array])
            
            # Predict
            predicted_score = self.models['channel_rating'].predict(feature_scaled)[0]
            
            return {
                "predicted_score": float(predicted_score),
                "predicted_rating": self._score_to_rating(predicted_score),
                "model_mse": self.model_metrics['channel_rating'].get('mse', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error predicting channel rating: {e}")
            return {"error": str(e)}
    
    def _extract_signal_features(self, signals: List[Signal]) -> Tuple[List[List[float]], List[int]]:
        """Extract features from signals for ML training"""
        features = []
        labels = []
        
        for signal in signals:
            if signal.roi_percentage is None:
                continue
            
            # Extract features
            feature_vector = [
                signal.confidence or 0.5,
                len(signal.raw_message) if signal.raw_message else 0,
                1 if signal.signal_type == 'buy' else 0,
                signal.entry_price or 0,
                signal.target_price or 0,
                signal.stop_loss or 0,
                1 if signal.stop_loss else 0,  # Has stop loss
                self._calculate_risk_reward_ratio(signal),
                signal.created_at.hour,  # Hour of day
                signal.created_at.weekday(),  # Day of week
            ]
            
            # Label: 1 if profitable, 0 if not
            label = 1 if signal.roi_percentage > 0 else 0
            
            features.append(feature_vector)
            labels.append(label)
        
        return features, labels
    
    def _extract_channel_features(self, channel_data: List[Tuple[Channel, Dict]]) -> Tuple[List[List[float]], List[float]]:
        """Extract features from channels for ML training"""
        features = []
        labels = []
        
        for channel, metrics in channel_data:
            # Extract features
            feature_vector = [
                metrics['total_signals'],
                metrics['accuracy']['success_rate'],
                metrics['roi']['average_roi'],
                metrics['consistency']['consistency_score'],
                metrics['frequency']['signals_per_day'],
                metrics['risk_management']['risk_score'],
                len(metrics['symbol_performance']),  # Number of different symbols
                1 if channel.type == 'telegram' else 0,
                1 if channel.type == 'reddit' else 0,
                1 if channel.type == 'twitter' else 0,
            ]
            
            # Label: overall score
            label = metrics['overall_score']
            
            features.append(feature_vector)
            labels.append(label)
        
        return features, labels
    
    def _signal_features_to_array(self, features: Dict[str, Any]) -> List[float]:
        """Convert signal features dict to array"""
        return [
            features.get('confidence', 0.5),
            features.get('message_length', 0),
            1 if features.get('signal_type') == 'buy' else 0,
            features.get('entry_price', 0),
            features.get('target_price', 0),
            features.get('stop_loss', 0),
            1 if features.get('has_stop_loss', False) else 0,
            features.get('risk_reward_ratio', 0),
            features.get('hour_of_day', 12),
            features.get('day_of_week', 0),
        ]
    
    def _channel_features_to_array(self, features: Dict[str, Any]) -> List[float]:
        """Convert channel features dict to array"""
        return [
            features.get('total_signals', 0),
            features.get('success_rate', 0),
            features.get('average_roi', 0),
            features.get('consistency_score', 0),
            features.get('signals_per_day', 0),
            features.get('risk_score', 0),
            features.get('symbol_count', 0),
            1 if features.get('channel_type') == 'telegram' else 0,
            1 if features.get('channel_type') == 'reddit' else 0,
            1 if features.get('channel_type') == 'twitter' else 0,
        ]
    
    def _get_signal_feature_names(self) -> List[str]:
        """Get signal feature names for importance analysis"""
        return [
            'confidence', 'message_length', 'is_buy_signal', 'entry_price',
            'target_price', 'stop_loss', 'has_stop_loss', 'risk_reward_ratio',
            'hour_of_day', 'day_of_week'
        ]
    
    def _calculate_risk_reward_ratio(self, signal: Signal) -> float:
        """Calculate risk-reward ratio for a signal"""
        if not signal.entry_price or not signal.target_price or not signal.stop_loss:
            return 0.0
        
        if signal.signal_type == 'buy':
            potential_profit = signal.target_price - signal.entry_price
            potential_loss = signal.entry_price - signal.stop_loss
        else:
            potential_profit = signal.entry_price - signal.target_price
            potential_loss = signal.stop_loss - signal.entry_price
        
        if potential_loss <= 0:
            return 0.0
        
        return potential_profit / potential_loss
    
    def _score_to_rating(self, score: float) -> str:
        """Convert numeric score to letter rating"""
        if score >= 0.8:
            return 'S'
        elif score >= 0.7:
            return 'A'
        elif score >= 0.6:
            return 'B'
        elif score >= 0.5:
            return 'C'
        elif score >= 0.4:
            return 'D'
        else:
            return 'F'
    
    def _save_model(self, model_name: str, model):
        """Save trained model to disk"""
        try:
            model_path = os.path.join(self.models_dir, f"{model_name}.joblib")
            joblib.dump(model, model_path)
            logger.info(f"Model {model_name} saved to {model_path}")
        except Exception as e:
            logger.error(f"Error saving model {model_name}: {e}")
    
    def _save_scaler(self, scaler_name: str, scaler):
        """Save scaler to disk"""
        try:
            scaler_path = os.path.join(self.models_dir, f"{scaler_name}_scaler.joblib")
            joblib.dump(scaler, scaler_path)
            logger.info(f"Scaler {scaler_name} saved to {scaler_path}")
        except Exception as e:
            logger.error(f"Error saving scaler {scaler_name}: {e}")
    
    async def _load_model(self, model_name: str):
        """Load trained model from disk"""
        try:
            model_path = os.path.join(self.models_dir, f"{model_name}.joblib")
            scaler_path = os.path.join(self.models_dir, f"{model_name.split('_')[0]}_features_scaler.joblib")
            
            if os.path.exists(model_path):
                self.models[model_name] = joblib.load(model_path)
                logger.info(f"Model {model_name} loaded from {model_path}")
            
            if os.path.exists(scaler_path):
                scaler_key = f"{model_name.split('_')[0]}_features"
                self.scalers[scaler_key] = joblib.load(scaler_path)
                logger.info(f"Scaler {scaler_key} loaded from {scaler_path}")
                
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all ML models"""
        return {
            "models_available": {
                name: model is not None 
                for name, model in self.models.items()
            },
            "model_metrics": self.model_metrics,
            "feature_importance": self.feature_importance,
            "models_directory": self.models_dir
        }
    
    async def retrain_all_models(self, db: Session) -> Dict[str, Any]:
        """Retrain all ML models with latest data"""
        results = {}
        
        # Train signal confidence model
        signal_result = await self.train_signal_confidence_model(db)
        results['signal_confidence'] = signal_result
        
        # Train channel rating model
        channel_result = await self.train_channel_rating_model(db)
        results['channel_rating'] = channel_result
        
        return {
            "retrain_completed": datetime.utcnow().isoformat(),
            "results": results
        }


# Global advanced ML service instance
advanced_ml_service = AdvancedMLService()
