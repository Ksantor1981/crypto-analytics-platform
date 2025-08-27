"""
Signal Quality Analyzer - Система анализа качества торговых сигналов
Включает расчет риск/прибыль, оценку качества и фильтрацию сигналов
"""

import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from improved_signal_parser import ImprovedSignal, SignalDirection, SignalQuality

class QualityScore(Enum):
    """Уровни качества сигналов"""
    EXCELLENT = "excellent"
    GOOD = "good"
    BASIC = "basic"
    POOR = "poor"
    UNRELIABLE = "unreliable"

@dataclass
class RiskRewardAnalysis:
    """Анализ риск/прибыль"""
    risk_reward_ratio: float
    potential_profit: float
    potential_loss: float
    profit_percent: float
    loss_percent: float
    risk_level: str
    reward_level: str

@dataclass
class QualityMetrics:
    """Метрики качества сигнала"""
    overall_score: float
    quality_level: QualityScore
    risk_reward_score: float
    technical_score: float
    confidence_score: float
    reliability_score: float
    recommendations: List[str]

class SignalQualityAnalyzer:
    """Анализатор качества сигналов"""
    
    def __init__(self):
        # Веса для расчета общего качества
        self.weights = {
            'risk_reward': 0.35,
            'technical': 0.25,
            'confidence': 0.25,
            'reliability': 0.15
        }
        
        # Пороги для уровней качества
        self.quality_thresholds = {
            QualityScore.EXCELLENT: 85.0,
            QualityScore.GOOD: 70.0,
            QualityScore.BASIC: 50.0,
            QualityScore.POOR: 30.0
        }
    
    def analyze_risk_reward(self, signal: ImprovedSignal) -> RiskRewardAnalysis:
        """Анализирует соотношение риск/прибыль"""
        if not signal.entry_price or not signal.target_price or not signal.stop_loss:
            return RiskRewardAnalysis(
                risk_reward_ratio=0.0,
                potential_profit=0.0,
                potential_loss=0.0,
                profit_percent=0.0,
                loss_percent=0.0,
                risk_level="unknown",
                reward_level="unknown"
            )
        
        entry = signal.entry_price
        target = signal.target_price
        stop = signal.stop_loss
        
        if signal.direction == SignalDirection.LONG:
            potential_profit = target - entry
            potential_loss = entry - stop
        else:  # SHORT
            potential_profit = entry - target
            potential_loss = stop - entry
        
        profit_percent = (potential_profit / entry) * 100
        loss_percent = (potential_loss / entry) * 100
        
        risk_reward_ratio = potential_profit / potential_loss if potential_loss > 0 else 0
        
        # Определяем уровни риска и награды
        risk_level = self._get_risk_level(loss_percent)
        reward_level = self._get_reward_level(profit_percent)
        
        return RiskRewardAnalysis(
            risk_reward_ratio=risk_reward_ratio,
            potential_profit=potential_profit,
            potential_loss=potential_loss,
            profit_percent=profit_percent,
            loss_percent=loss_percent,
            risk_level=risk_level,
            reward_level=reward_level
        )
    
    def _get_risk_level(self, loss_percent: float) -> str:
        """Определяет уровень риска"""
        if loss_percent <= 2.0:
            return "low"
        elif loss_percent <= 5.0:
            return "medium"
        elif loss_percent <= 10.0:
            return "high"
        else:
            return "very_high"
    
    def _get_reward_level(self, profit_percent: float) -> str:
        """Определяет уровень награды"""
        if profit_percent >= 10.0:
            return "excellent"
        elif profit_percent >= 5.0:
            return "good"
        elif profit_percent >= 2.0:
            return "moderate"
        else:
            return "low"
    
    def calculate_technical_score(self, signal: ImprovedSignal) -> float:
        """Рассчитывает технический скор сигнала"""
        score = 50.0  # Базовый скор
        
        # Оценка качества извлечения
        if signal.signal_quality == SignalQuality.EXCELLENT:
            score += 20
        elif signal.signal_quality == SignalQuality.GOOD:
            score += 15
        elif signal.signal_quality == SignalQuality.BASIC:
            score += 10
        elif signal.signal_quality == SignalQuality.POOR:
            score -= 10
        
        # Оценка валидности
        if signal.is_valid:
            score += 15
        else:
            score -= 20
        
        # Оценка доступности на Bybit
        if signal.bybit_available:
            score += 10
        else:
            score -= 15
        
        # Оценка наличия всех необходимых данных
        if signal.entry_price and signal.target_price and signal.stop_loss:
            score += 15
        elif signal.entry_price and (signal.target_price or signal.stop_loss):
            score += 5
        else:
            score -= 10
        
        # Оценка leverage
        if signal.leverage:
            if 1 <= signal.leverage <= 20:
                score += 5
            elif signal.leverage > 50:
                score -= 10
        
        return max(0.0, min(100.0, score))
    
    def calculate_confidence_score(self, signal: ImprovedSignal) -> float:
        """Рассчитывает скор уверенности"""
        score = 50.0  # Базовый скор
        
        # Используем реальную уверенность если доступна
        confidence = signal.real_confidence or signal.calculated_confidence or 50.0
        
        # Нормализуем уверенность к 100-балльной шкале
        score = confidence
        
        # Дополнительные модификаторы
        if signal.validation_errors:
            error_count = len(signal.validation_errors)
            score -= min(error_count * 5, 30)  # Максимум -30 за ошибки
        
        return max(0.0, min(100.0, score))
    
    def calculate_reliability_score(self, signal: ImprovedSignal) -> float:
        """Рассчитывает скор надежности"""
        score = 50.0  # Базовый скор
        
        # Оценка качества исходного текста
        if signal.original_text and len(signal.original_text) > 50:
            score += 10
        elif not signal.original_text:
            score -= 20
        
        # Оценка очищенного текста
        if signal.cleaned_text and len(signal.cleaned_text) > 20:
            score += 10
        
        # Оценка временных меток
        if signal.timestamp and signal.extraction_time:
            score += 10
        
        # Оценка уникальности ID
        if signal.id and len(signal.id) >= 8:
            score += 5
        
        return max(0.0, min(100.0, score))
    
    def calculate_risk_reward_score(self, risk_reward: RiskRewardAnalysis) -> float:
        """Рассчитывает скор риск/прибыль"""
        score = 50.0  # Базовый скор
        
        # Оценка соотношения риск/прибыль
        if risk_reward.risk_reward_ratio >= 3.0:
            score += 30
        elif risk_reward.risk_reward_ratio >= 2.0:
            score += 20
        elif risk_reward.risk_reward_ratio >= 1.5:
            score += 10
        elif risk_reward.risk_reward_ratio >= 1.0:
            score += 5
        elif risk_reward.risk_reward_ratio < 0.5:
            score -= 20
        elif risk_reward.risk_reward_ratio < 1.0:
            score -= 10
        
        # Оценка потенциальной прибыли
        if risk_reward.profit_percent >= 10.0:
            score += 15
        elif risk_reward.profit_percent >= 5.0:
            score += 10
        elif risk_reward.profit_percent >= 2.0:
            score += 5
        elif risk_reward.profit_percent < 1.0:
            score -= 10
        
        # Оценка риска
        if risk_reward.risk_level == "low":
            score += 10
        elif risk_reward.risk_level == "very_high":
            score -= 15
        
        return max(0.0, min(100.0, score))
    
    def get_quality_level(self, overall_score: float) -> QualityScore:
        """Определяет уровень качества на основе общего скора"""
        if overall_score >= self.quality_thresholds[QualityScore.EXCELLENT]:
            return QualityScore.EXCELLENT
        elif overall_score >= self.quality_thresholds[QualityScore.GOOD]:
            return QualityScore.GOOD
        elif overall_score >= self.quality_thresholds[QualityScore.BASIC]:
            return QualityScore.BASIC
        elif overall_score >= self.quality_thresholds[QualityScore.POOR]:
            return QualityScore.POOR
        else:
            return QualityScore.UNRELIABLE
    
    def generate_recommendations(self, signal: ImprovedSignal, metrics: QualityMetrics, risk_reward: RiskRewardAnalysis) -> List[str]:
        """Генерирует рекомендации по улучшению сигнала"""
        recommendations = []
        
        # Рекомендации по риск/прибыль
        if risk_reward.risk_reward_ratio < 1.5:
            recommendations.append("Низкое соотношение риск/прибыль - рассмотрите другие сигналы")
        
        if risk_reward.risk_level == "very_high":
            recommendations.append("Очень высокий риск - используйте меньший размер позиции")
        
        if risk_reward.profit_percent < 2.0:
            recommendations.append("Низкая потенциальная прибыль - может не стоить риска")
        
        # Рекомендации по качеству
        if metrics.technical_score < 60:
            recommendations.append("Низкое техническое качество - проверьте данные сигнала")
        
        if metrics.confidence_score < 50:
            recommendations.append("Низкая уверенность - дождитесь лучших сигналов")
        
        if not signal.bybit_available:
            recommendations.append("Актив недоступен на Bybit - проверьте альтернативы")
        
        if signal.validation_errors:
            recommendations.append(f"Найдены ошибки валидации: {len(signal.validation_errors)}")
        
        # Рекомендации по leverage
        if signal.leverage and signal.leverage > 20:
            recommendations.append("Высокий leverage - используйте с осторожностью")
        
        # Положительные рекомендации
        if metrics.overall_score >= 80:
            recommendations.append("Отличное качество сигнала - рекомендуется к исполнению")
        elif metrics.overall_score >= 70:
            recommendations.append("Хорошее качество сигнала - подходит для торговли")
        
        return recommendations
    
    def analyze_signal_quality(self, signal: ImprovedSignal) -> Tuple[QualityMetrics, RiskRewardAnalysis]:
        """Полный анализ качества сигнала"""
        # Анализ риск/прибыль
        risk_reward = self.analyze_risk_reward(signal)
        
        # Расчет отдельных скоров
        risk_reward_score = self.calculate_risk_reward_score(risk_reward)
        technical_score = self.calculate_technical_score(signal)
        confidence_score = self.calculate_confidence_score(signal)
        reliability_score = self.calculate_reliability_score(signal)
        
        # Общий скор
        overall_score = (
            risk_reward_score * self.weights['risk_reward'] +
            technical_score * self.weights['technical'] +
            confidence_score * self.weights['confidence'] +
            reliability_score * self.weights['reliability']
        )
        
        # Определяем уровень качества
        quality_level = self.get_quality_level(overall_score)
        
        # Создаем метрики
        metrics = QualityMetrics(
            overall_score=overall_score,
            quality_level=quality_level,
            risk_reward_score=risk_reward_score,
            technical_score=technical_score,
            confidence_score=confidence_score,
            reliability_score=reliability_score,
            recommendations=[]
        )
        
        # Генерируем рекомендации
        metrics.recommendations = self.generate_recommendations(signal, metrics, risk_reward)
        
        return metrics, risk_reward
    
    def filter_signals_by_quality(self, signals: List[ImprovedSignal], min_quality: QualityScore = QualityScore.BASIC) -> List[ImprovedSignal]:
        """Фильтрует сигналы по качеству"""
        filtered_signals = []
        
        for signal in signals:
            metrics, _ = self.analyze_signal_quality(signal)
            
            # Проверяем минимальный уровень качества
            quality_values = {
                QualityScore.EXCELLENT: 4,
                QualityScore.GOOD: 3,
                QualityScore.BASIC: 2,
                QualityScore.POOR: 1,
                QualityScore.UNRELIABLE: 0
            }
            
            if quality_values[metrics.quality_level] >= quality_values[min_quality]:
                filtered_signals.append(signal)
        
        return filtered_signals
    
    def get_quality_summary(self, signals: List[ImprovedSignal]) -> Dict:
        """Получает сводку по качеству сигналов"""
        if not signals:
            return {
                'total_signals': 0,
                'quality_distribution': {},
                'avg_overall_score': 0.0,
                'avg_risk_reward_ratio': 0.0,
                'high_quality_count': 0,
                'low_quality_count': 0
            }
        
        quality_distribution = {}
        total_score = 0.0
        total_risk_reward = 0.0
        high_quality_count = 0
        low_quality_count = 0
        
        for signal in signals:
            metrics, risk_reward = self.analyze_signal_quality(signal)
            
            # Распределение по качеству
            quality = metrics.quality_level.value
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
            
            # Суммируем скоры
            total_score += metrics.overall_score
            total_risk_reward += risk_reward.risk_reward_ratio
            
            # Подсчитываем высокое/низкое качество
            if metrics.quality_level in [QualityScore.EXCELLENT, QualityScore.GOOD]:
                high_quality_count += 1
            elif metrics.quality_level in [QualityScore.POOR, QualityScore.UNRELIABLE]:
                low_quality_count += 1
        
        return {
            'total_signals': len(signals),
            'quality_distribution': quality_distribution,
            'avg_overall_score': total_score / len(signals),
            'avg_risk_reward_ratio': total_risk_reward / len(signals),
            'high_quality_count': high_quality_count,
            'low_quality_count': low_quality_count
        }

def main():
    """Тестирование анализатора качества"""
    from improved_signal_parser import ImprovedSignal, SignalDirection, SignalQuality
    
    analyzer = SignalQualityAnalyzer()
    
    # Создаем тестовый сигнал
    test_signal = ImprovedSignal(
        id="quality_test_001",
        asset="BTC",
        direction=SignalDirection.LONG,
        entry_price=50000,
        target_price=55000,
        stop_loss=48000,
        leverage=10,
        channel="test_channel",
        message_id="msg_001",
        original_text="Test signal for quality analysis",
        cleaned_text="Test signal for quality analysis",
        timestamp="2025-08-24T15:00:00",
        extraction_time="2025-08-24T15:00:01",
        signal_quality=SignalQuality.GOOD,
        real_confidence=75.0,
        bybit_available=True,
        is_valid=True,
        validation_errors=[]
    )
    
    # Анализируем качество
    metrics, risk_reward = analyzer.analyze_signal_quality(test_signal)
    
    print("=== Анализ качества сигнала ===")
    print(f"Актив: {test_signal.asset}")
    print(f"Направление: {test_signal.direction.value}")
    print(f"Вход: {test_signal.entry_price}")
    print(f"Цель: {test_signal.target_price}")
    print(f"Стоп: {test_signal.stop_loss}")
    print()
    
    print("=== Анализ риск/прибыль ===")
    print(f"Соотношение риск/прибыль: {risk_reward.risk_reward_ratio:.2f}")
    print(f"Потенциальная прибыль: {risk_reward.profit_percent:.2f}%")
    print(f"Потенциальный убыток: {risk_reward.loss_percent:.2f}%")
    print(f"Уровень риска: {risk_reward.risk_level}")
    print(f"Уровень награды: {risk_reward.reward_level}")
    print()
    
    print("=== Метрики качества ===")
    print(f"Общий скор: {metrics.overall_score:.1f}")
    print(f"Уровень качества: {metrics.quality_level.value}")
    print(f"Скор риск/прибыль: {metrics.risk_reward_score:.1f}")
    print(f"Технический скор: {metrics.technical_score:.1f}")
    print(f"Скор уверенности: {metrics.confidence_score:.1f}")
    print(f"Скор надежности: {metrics.reliability_score:.1f}")
    print()
    
    print("=== Рекомендации ===")
    for rec in metrics.recommendations:
        print(f"- {rec}")

if __name__ == "__main__":
    main()
