"""
Простой ML предиктор без ошибок
"""

import json
from typing import Dict, Any
from datetime import datetime

class SimplePredictor:
    """
    Простая модель предсказания без проблем с None
    """
    
    def __init__(self):
        self.model_version = "1.0.0-simple"
        self.is_trained = True
        self.feature_names = [
            'asset_type',
            'direction_score',
            'price_ratio',
            'base_confidence'
        ]
    
    def predict(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Простое предсказание без ошибок
        """
        # Безопасное извлечение данных
        asset = str(signal_data.get('asset', 'BTC')).upper()
        direction = str(signal_data.get('direction', 'LONG')).upper()
        entry_price = float(signal_data.get('entry_price', 1.0)) or 1.0
        target_price = signal_data.get('target_price')
        stop_loss = signal_data.get('stop_loss')
        channel_accuracy = float(signal_data.get('channel_accuracy', 0.5)) or 0.5
        confidence = float(signal_data.get('confidence', 0.5)) or 0.5
        
        # Базовая вероятность успеха
        base_probability = 0.5
        
        # Корректировка по активу
        asset_bonus = {
            'BTC': 0.1,
            'ETH': 0.08,
            'BNB': 0.05,
            'ADA': 0.03,
            'SOL': 0.02
        }.get(asset, 0.0)
        
        # Корректировка по направлению (LONG обычно лучше в бычьем рынке)
        direction_bonus = 0.05 if direction == 'LONG' else 0.0
        
        # Корректировка по точности канала
        channel_bonus = (channel_accuracy - 0.5) * 0.3
        
        # Корректировка по уверенности
        confidence_bonus = (confidence - 0.5) * 0.2
        
        # Корректировка по соотношению риск/прибыль
        rr_bonus = 0.0
        if target_price and stop_loss and entry_price > 0:
            try:
                target_price = float(target_price)
                stop_loss = float(stop_loss)
                
                if direction == 'LONG' and target_price > entry_price and stop_loss < entry_price:
                    risk = entry_price - stop_loss
                    reward = target_price - entry_price
                    if risk > 0:
                        rr_ratio = reward / risk
                        if rr_ratio > 2:
                            rr_bonus = 0.1
                        elif rr_ratio > 1.5:
                            rr_bonus = 0.05
                elif direction == 'SHORT' and target_price < entry_price and stop_loss > entry_price:
                    risk = stop_loss - entry_price
                    reward = entry_price - target_price
                    if risk > 0:
                        rr_ratio = reward / risk
                        if rr_ratio > 2:
                            rr_bonus = 0.1
                        elif rr_ratio > 1.5:
                            rr_bonus = 0.05
            except (ValueError, ZeroDivisionError):
                pass
        
        # Итоговая вероятность
        success_probability = max(0.1, min(0.95, 
            base_probability + asset_bonus + direction_bonus + 
            channel_bonus + confidence_bonus + rr_bonus
        ))
        
        # Уверенность модели
        model_confidence = max(0.6, min(0.95, 
            0.7 + abs(success_probability - 0.5) * 0.5
        ))
        
        # Рекомендация
        if success_probability >= 0.7:
            recommendation = "СИЛЬНАЯ ПОКУПКА"
        elif success_probability >= 0.6:
            recommendation = "ПОКУПКА"
        elif success_probability >= 0.4:
            recommendation = "НЕЙТРАЛЬНО"
        else:
            recommendation = "ОСТОРОЖНО"
        
        # Оценка риска
        risk_score = max(0.05, min(0.95, 1.0 - success_probability))
        
        # Важность признаков
        features_importance = {
            'asset_type': 0.25,
            'direction_score': 0.20,
            'price_ratio': 0.30,
            'base_confidence': 0.25
        }
        
        return {
            "success_probability": round(success_probability, 3),
            "confidence": round(model_confidence, 3),
            "recommendation": recommendation,
            "risk_score": round(risk_score, 3),
            "features_importance": features_importance,
            "model_version": self.model_version,
            "prediction_timestamp": datetime.now().isoformat()
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Информация о модели
        """
        return {
            "model_version": self.model_version,
            "model_type": "simple_rule_based",
            "is_trained": self.is_trained,
            "feature_names": self.feature_names,
            "created_at": datetime.now().isoformat()
        } 