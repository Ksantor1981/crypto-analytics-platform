"""
Улучшенный ML предиктор с гибкой логикой оценки рисков
"""

import json
from typing import Dict, Any, List
from datetime import datetime
import math

class SimplePredictor:
    """
    Улучшенная модель предсказания с гибкой логикой
    """
    
    def __init__(self):
        self.model_version = "2.0.0-improved"
        self.is_trained = True
        self.feature_names = [
            'asset_volatility',
            'direction_score',
            'risk_reward_ratio',
            'market_conditions',
            'position_size_risk',
            'technical_indicators',
            'base_confidence'
        ]
        
        # Базовые параметры для оценки
        self.risk_thresholds = {
            'low_risk': 0.3,
            'medium_risk': 0.6,
            'high_risk': 0.8
        }
        
        # Веса факторов
        self.factor_weights = {
            'risk_reward_ratio': 0.30,  # Увеличили с 0.25 - самый важный фактор
            'asset_volatility': 0.20,   # Оставили как есть
            'direction_score': 0.15,    # Оставили как есть
            'market_conditions': 0.15,  # Оставили как есть
            'position_size_risk': 0.10, # Оставили как есть
            'technical_indicators': 0.05, # Уменьшили с 0.10
            'base_confidence': 0.05     # Оставили как есть
        }
    
    def calculate_asset_volatility(self, asset: str, entry_price: float, 
                                 target_price: float, stop_loss: float) -> float:
        """Расчет волатильности актива на основе цен"""
        if not all([entry_price, target_price, stop_loss]) or entry_price <= 0:
            return 0.5  # Средняя волатильность по умолчанию
        
        # Расчет потенциального движения
        potential_gain = abs(target_price - entry_price) / entry_price
        potential_loss = abs(stop_loss - entry_price) / entry_price
        
        # Волатильность = среднее движение
        volatility = (potential_gain + potential_loss) / 2
        
        # Нормализация к 0-1 шкале
        return min(1.0, max(0.0, volatility * 10))  # Умножаем на 10 для нормализации
    
    def calculate_risk_reward_ratio(self, entry_price: float, target_price: float, 
                                  stop_loss: float, direction: str) -> float:
        """Расчет соотношения риск/прибыль"""
        if not all([entry_price, target_price, stop_loss]) or entry_price <= 0:
            return 0.5  # Нейтральное соотношение
        
        try:
            if direction.upper() == 'LONG':
                if target_price > entry_price and stop_loss < entry_price:
                    risk = entry_price - stop_loss
                    reward = target_price - entry_price
                else:
                    return 0.3  # Плохое соотношение
            else:  # SHORT
                if target_price < entry_price and stop_loss > entry_price:
                    risk = stop_loss - entry_price
                    reward = entry_price - target_price
                else:
                    return 0.3  # Плохое соотношение
            
            if risk <= 0:
                return 0.3
            
            ratio = reward / risk
            
            # Улучшенная нормализация для лучшего распознавания отличных сделок
            if ratio >= 4.0:  # Отличное соотношение 4:1 и выше
                return 1.0
            elif ratio >= 3.0:  # Очень хорошее соотношение 3:1
                return 0.9
            elif ratio >= 2.0:  # Хорошее соотношение 2:1
                return 0.8
            elif ratio >= 1.5:  # Удовлетворительное соотношение 1.5:1
                return 0.7
            elif ratio >= 1.0:  # Нейтральное соотношение 1:1
                return 0.6
            elif ratio >= 0.5:  # Плохое соотношение 0.5:1
                return 0.4
            else:  # Очень плохое соотношение
                return 0.2
            
        except (ValueError, ZeroDivisionError):
            return 0.3
    
    def calculate_direction_score(self, direction: str, market_trend: str = 'neutral') -> float:
        """Оценка направления с учетом рыночного тренда"""
        direction = direction.upper()
        
        # Базовые оценки направлений
        direction_scores = {
            'LONG': 0.6,  # LONG обычно более консервативен
            'SHORT': 0.4   # SHORT более рискован
        }
        
        base_score = direction_scores.get(direction, 0.5)
        
        # Корректировка по рыночному тренду
        if market_trend == 'bullish' and direction == 'LONG':
            base_score += 0.1
        elif market_trend == 'bearish' and direction == 'SHORT':
            base_score += 0.1
        elif market_trend == 'bullish' and direction == 'SHORT':
            base_score -= 0.1
        elif market_trend == 'bearish' and direction == 'LONG':
            base_score -= 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def calculate_market_conditions(self, asset: str, entry_price: float) -> float:
        """Оценка рыночных условий (упрощенная)"""
        # В реальной системе здесь была бы интеграция с рыночными данными
        # Пока используем эвристику на основе цены
        
        if entry_price <= 0:
            return 0.5
        
        # Чем выше цена, тем более зрелый рынок (обычно менее волатильный)
        if entry_price > 10000:  # Высокие цены (BTC, ETH)
            return 0.7  # Более стабильные условия
        elif entry_price > 100:  # Средние цены
            return 0.6
        elif entry_price > 1:  # Низкие цены
            return 0.5
        else:  # Очень низкие цены (мемкоины)
            return 0.3  # Высокая волатильность
    
    def calculate_position_size_risk(self, entry_price: float, target_price: float, 
                                   stop_loss: float) -> float:
        """Оценка риска размера позиции"""
        if not all([entry_price, target_price, stop_loss]) or entry_price <= 0:
            return 0.5
        
        # Расчет потенциального убытка в процентах
        potential_loss_pct = abs(stop_loss - entry_price) / entry_price
        
        # Оценка риска
        if potential_loss_pct <= 0.02:  # До 2%
            return 0.8  # Низкий риск
        elif potential_loss_pct <= 0.05:  # До 5%
            return 0.6  # Средний риск
        elif potential_loss_pct <= 0.10:  # До 10%
            return 0.4  # Высокий риск
        else:  # Более 10%
            return 0.2  # Очень высокий риск
    
    def calculate_technical_indicators(self, asset: str, entry_price: float) -> float:
        """Упрощенная оценка технических индикаторов"""
        # В реальной системе здесь была бы интеграция с техническим анализом
        # Пока используем эвристику
        
        # Чем больше цифр в цене, тем более "технически продвинутый" актив
        price_str = str(entry_price)
        decimal_places = len(price_str.split('.')[-1]) if '.' in price_str else 0
        
        if decimal_places <= 2:  # Целые числа или до центов
            return 0.7  # Более стабильные активы
        elif decimal_places <= 4:  # До 4 знаков после запятой
            return 0.6
        elif decimal_places <= 6:  # До 6 знаков
            return 0.5
        else:  # Много знаков после запятой
            return 0.3  # Высокая волатильность
    
    def predict(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Улучшенное предсказание с множественными факторами
        """
        # Безопасное извлечение данных
        asset = str(signal_data.get('asset', 'UNKNOWN')).upper()
        direction = str(signal_data.get('direction', 'LONG')).upper()
        entry_price = float(signal_data.get('entry_price', 1.0)) or 1.0
        target_price = signal_data.get('target_price')
        stop_loss = signal_data.get('stop_loss')
        channel_accuracy = float(signal_data.get('channel_accuracy', 0.5)) or 0.5
        confidence = float(signal_data.get('confidence', 0.5)) or 0.5
        
        # Расчет всех факторов
        asset_volatility = self.calculate_asset_volatility(asset, entry_price, target_price, stop_loss)
        risk_reward_ratio = self.calculate_risk_reward_ratio(entry_price, target_price, stop_loss, direction)
        direction_score = self.calculate_direction_score(direction)
        market_conditions = self.calculate_market_conditions(asset, entry_price)
        position_size_risk = self.calculate_position_size_risk(entry_price, target_price, stop_loss)
        technical_indicators = self.calculate_technical_indicators(asset, entry_price)
        base_confidence = confidence
        
        # Взвешенная оценка успешности
        factors = {
            'risk_reward_ratio': risk_reward_ratio,
            'asset_volatility': 1.0 - asset_volatility,  # Инвертируем (меньше волатильность = лучше)
            'direction_score': direction_score,
            'market_conditions': market_conditions,
            'position_size_risk': position_size_risk,
            'technical_indicators': technical_indicators,
            'base_confidence': base_confidence
        }
        
        # Взвешенная сумма
        success_probability = sum(
            factors[factor] * self.factor_weights[factor] 
            for factor in self.factor_weights
        )
        
        # Ограничиваем результат
        success_probability = max(0.05, min(0.95, success_probability))
        
        # Определяем рекомендацию на основе вероятности успеха
        if success_probability >= 0.70:  # Снизили с 0.75
            recommendation = "СИЛЬНАЯ ПОКУПКА" if direction == "LONG" else "СИЛЬНАЯ ПРОДАЖА"
        elif success_probability >= 0.60:  # Снизили с 0.65
            recommendation = "ПОКУПКА" if direction == "LONG" else "ПРОДАЖА"
        elif success_probability >= 0.45:  # Снизили с 0.45
            recommendation = "НЕЙТРАЛЬНО"
        elif success_probability >= 0.30:  # Снизили с 0.25
            recommendation = "ОСТОРОЖНО"
        else:
            recommendation = "ИЗБЕГАТЬ"
        
        # Уверенность модели (выше для крайних значений)
        model_confidence = 0.6 + abs(success_probability - 0.5) * 0.8
        model_confidence = max(0.5, min(0.95, model_confidence))
        
        # Оценка риска
        risk_score = max(0.05, min(0.95, 1.0 - success_probability))
        
        # Важность признаков (динамическая)
        features_importance = {
            'risk_reward_ratio': round(risk_reward_ratio * 0.3, 3),
            'asset_volatility': round((1.0 - asset_volatility) * 0.25, 3),
            'direction_score': round(direction_score * 0.15, 3),
            'market_conditions': round(market_conditions * 0.15, 3),
            'position_size_risk': round(position_size_risk * 0.10, 3),
            'technical_indicators': round(technical_indicators * 0.05, 3)
        }
        
        return {
            "success_probability": round(success_probability, 3),
            "confidence": round(model_confidence, 3),
            "recommendation": recommendation,
            "risk_score": round(risk_score, 3),
            "features_importance": features_importance,
            "model_version": self.model_version,
            "prediction_timestamp": datetime.now().isoformat(),
            "analysis_details": {
                "asset_volatility": round(asset_volatility, 3),
                "risk_reward_ratio": round(risk_reward_ratio, 3),
                "direction_score": round(direction_score, 3),
                "market_conditions": round(market_conditions, 3),
                "position_size_risk": round(position_size_risk, 3),
                "technical_indicators": round(technical_indicators, 3)
            }
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Информация о модели
        """
        return {
            "model_version": self.model_version,
            "model_type": "improved_rule_based",
            "is_trained": self.is_trained,
            "feature_names": self.feature_names,
            "factor_weights": self.factor_weights,
            "risk_thresholds": self.risk_thresholds,
            "created_at": datetime.now().isoformat()
        } 