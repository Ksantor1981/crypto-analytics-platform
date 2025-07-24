#!/usr/bin/env python3
"""
Тест точности ML-модели
Проверяет различные сценарии и оценивает качество предсказаний
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import statistics

class MLAccuracyTester:
    """Тестер точности ML-модели"""
    
    def __init__(self):
        self.ml_service_url = "http://localhost:8001"
        self.test_results = []
        
    async def test_single_prediction(self, test_case: Dict) -> Dict:
        """Тест одного предсказания"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ml_service_url}/api/v1/predictions/predict",
                    json=test_case['request'],
                    timeout=10
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'test_case': test_case['name'],
                            'request': test_case['request'],
                            'response': result,
                            'success': True,
                            'prediction': result.get('prediction', 'UNKNOWN'),
                            'confidence': result.get('confidence', 0.0),
                            'expected_behavior': test_case.get('expected_behavior', 'neutral')
                        }
                    else:
                        return {
                            'test_case': test_case['name'],
                            'request': test_case['request'],
                            'success': False,
                            'error': f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                'test_case': test_case['name'],
                'request': test_case['request'],
                'success': False,
                'error': str(e)
            }
    
    def create_test_cases(self) -> List[Dict]:
        """Создание тестовых случаев"""
        return [
            # Тест 1: BTC с отличным соотношением риск/прибыль
            {
                'name': 'BTC_Excellent_RR',
                'request': {
                    'asset': 'BTCUSDT',
                    'entry_price': 50000.0,
                    'target_price': 60000.0,  # +20%
                    'stop_loss': 47500.0,     # -5%
                    'direction': 'LONG'
                },
                'expected_behavior': 'strong_buy'
            },
            
            # Тест 2: ETH с хорошим соотношением
            {
                'name': 'ETH_Good_RR',
                'request': {
                    'asset': 'ETHUSDT',
                    'entry_price': 3000.0,
                    'target_price': 3300.0,   # +10%
                    'stop_loss': 2850.0,      # -5%
                    'direction': 'LONG'
                },
                'expected_behavior': 'buy'
            },
            
            # Тест 3: ADA с плохим соотношением риск/прибыль
            {
                'name': 'ADA_Poor_RR',
                'request': {
                    'asset': 'ADAUSDT',
                    'entry_price': 0.5,
                    'target_price': 0.51,     # +2%
                    'stop_loss': 0.45,        # -10%
                    'direction': 'LONG'
                },
                'expected_behavior': 'caution'
            },
            
            # Тест 4: SHORT позиция с хорошим соотношением
            {
                'name': 'BTC_Short_Good',
                'request': {
                    'asset': 'BTCUSDT',
                    'entry_price': 50000.0,
                    'target_price': 45000.0,  # -10%
                    'stop_loss': 52500.0,     # +5%
                    'direction': 'SHORT'
                },
                'expected_behavior': 'sell'
            },
            
            # Тест 5: Неизвестный актив с умеренными параметрами
            {
                'name': 'Unknown_Moderate',
                'request': {
                    'asset': 'UNKNOWNUSDT',
                    'entry_price': 100.0,
                    'target_price': 110.0,    # +10%
                    'stop_loss': 95.0,        # -5%
                    'direction': 'LONG'
                },
                'expected_behavior': 'neutral'
            },
            
            # Тест 6: Очень высокий риск
            {
                'name': 'High_Risk_Meme',
                'request': {
                    'asset': 'DOGEUSDT',
                    'entry_price': 0.1,
                    'target_price': 0.11,     # +10%
                    'stop_loss': 0.05,        # -50%
                    'direction': 'LONG'
                },
                'expected_behavior': 'caution'
            },
            
            # Тест 7: Отличное соотношение риск/прибыль для SHORT
            {
                'name': 'ETH_Short_Excellent',
                'request': {
                    'asset': 'ETHUSDT',
                    'entry_price': 3000.0,
                    'target_price': 2400.0,   # -20%
                    'stop_loss': 3150.0,      # +5%
                    'direction': 'SHORT'
                },
                'expected_behavior': 'strong_sell'
            },
            
            # Тест 8: Без target и stop_loss
            {
                'name': 'No_Target_SL',
                'request': {
                    'asset': 'BNBUSDT',
                    'entry_price': 400.0,
                    'direction': 'LONG'
                },
                'expected_behavior': 'neutral'
            },
            
            # Тест 9: Консервативная сделка
            {
                'name': 'Conservative_Trade',
                'request': {
                    'asset': 'BTCUSDT',
                    'entry_price': 50000.0,
                    'target_price': 51000.0,  # +2%
                    'stop_loss': 49500.0,     # -1%
                    'direction': 'LONG'
                },
                'expected_behavior': 'neutral'
            },
            
            # Тест 10: Агрессивная сделка
            {
                'name': 'Aggressive_Trade',
                'request': {
                    'asset': 'SOLUSDT',
                    'entry_price': 100.0,
                    'target_price': 150.0,    # +50%
                    'stop_loss': 80.0,        # -20%
                    'direction': 'LONG'
                },
                'expected_behavior': 'caution'
            }
        ]
    
    def analyze_results(self, results: List[Dict]) -> Dict:
        """Анализ результатов тестирования"""
        successful_tests = [r for r in results if r['success']]
        failed_tests = [r for r in results if not r['success']]
        
        if not successful_tests:
            return {
                'total_tests': len(results),
                'successful_tests': 0,
                'failed_tests': len(failed_tests),
                'success_rate': 0.0,
                'average_confidence': 0.0,
                'prediction_distribution': {},
                'errors': [r.get('error', 'Unknown error') for r in failed_tests]
            }
        
        # Статистика по уверенности
        confidences = [r['confidence'] for r in successful_tests]
        avg_confidence = statistics.mean(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)
        
        # Распределение предсказаний
        prediction_counts = {}
        for result in successful_tests:
            pred = result['prediction']
            prediction_counts[pred] = prediction_counts.get(pred, 0) + 1
        
        # Анализ соответствия ожидаемому поведению
        behavior_analysis = {}
        for result in successful_tests:
            expected = result.get('expected_behavior', 'neutral')
            actual = result['prediction']
            direction = result['request'].get('direction', 'LONG')
            
            if expected not in behavior_analysis:
                behavior_analysis[expected] = {'total': 0, 'correct': 0}
            
            behavior_analysis[expected]['total'] += 1
            
            # Проверяем соответствие с учетом направления
            is_correct = False
            
            if expected == 'strong_buy' and direction == 'LONG' and 'СИЛЬНАЯ ПОКУПКА' in actual:
                is_correct = True
            elif expected == 'buy' and direction == 'LONG' and 'ПОКУПКА' in actual:
                is_correct = True
            elif expected == 'strong_sell' and direction == 'SHORT' and 'СИЛЬНАЯ ПРОДАЖА' in actual:
                is_correct = True
            elif expected == 'sell' and direction == 'SHORT' and 'ПРОДАЖА' in actual:
                is_correct = True
            elif expected == 'neutral' and 'НЕЙТРАЛЬНО' in actual:
                is_correct = True
            elif expected == 'caution' and 'ОСТОРОЖНО' in actual:
                is_correct = True
            
            if is_correct:
                behavior_analysis[expected]['correct'] += 1
        
        # Общая точность
        total_expected = sum(analysis['total'] for analysis in behavior_analysis.values())
        total_correct = sum(analysis['correct'] for analysis in behavior_analysis.values())
        overall_accuracy = (total_correct / total_expected * 100) if total_expected > 0 else 0
        
        return {
            'total_tests': len(results),
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'success_rate': (len(successful_tests) / len(results)) * 100,
            'overall_accuracy': overall_accuracy,
            'average_confidence': round(avg_confidence, 3),
            'min_confidence': round(min_confidence, 3),
            'max_confidence': round(max_confidence, 3),
            'confidence_std': round(statistics.stdev(confidences), 3) if len(confidences) > 1 else 0,
            'prediction_distribution': prediction_counts,
            'behavior_analysis': behavior_analysis,
            'errors': [r.get('error', 'Unknown error') for r in failed_tests]
        }
    
    def print_analysis(self, analysis: Dict):
        """Вывод анализа результатов"""
        print("\n" + "="*60)
        print("📊 АНАЛИЗ ТОЧНОСТИ ML-МОДЕЛИ")
        print("="*60)
        
        print(f"Всего тестов: {analysis['total_tests']}")
        print(f"Успешных тестов: {analysis['successful_tests']}")
        print(f"Проваленных тестов: {analysis['failed_tests']}")
        print(f"Успешность запросов: {analysis['success_rate']:.1f}%")
        print(f"Общая точность предсказаний: {analysis['overall_accuracy']:.1f}%")
        
        print(f"\n📈 Статистика уверенности:")
        print(f"  Средняя уверенность: {analysis['average_confidence']}")
        print(f"  Минимальная уверенность: {analysis['min_confidence']}")
        print(f"  Максимальная уверенность: {analysis['max_confidence']}")
        print(f"  Стандартное отклонение: {analysis['confidence_std']}")
        
        print(f"\n🎯 Распределение предсказаний:")
        for pred, count in analysis['prediction_distribution'].items():
            percentage = (count / analysis['successful_tests']) * 100
            print(f"  {pred}: {count} ({percentage:.1f}%)")
        
        print(f"\n✅ Анализ соответствия ожидаемому поведению:")
        for behavior, stats in analysis['behavior_analysis'].items():
            accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {behavior}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
        
        if analysis['errors']:
            print(f"\n❌ Ошибки:")
            for error in analysis['errors']:
                print(f"  - {error}")
        
        print("\n" + "="*60)
        
        # Оценка качества модели
        if analysis['overall_accuracy'] >= 80:
            print("🎉 ОТЛИЧНАЯ ТОЧНОСТЬ МОДЕЛИ!")
        elif analysis['overall_accuracy'] >= 60:
            print("✅ ХОРОШАЯ ТОЧНОСТЬ МОДЕЛИ")
        elif analysis['overall_accuracy'] >= 40:
            print("⚠️ СРЕДНЯЯ ТОЧНОСТЬ МОДЕЛИ")
        else:
            print("❌ НИЗКАЯ ТОЧНОСТЬ МОДЕЛИ")
        
        print("="*60)

async def main():
    """Основная функция тестирования точности"""
    print("🧪 ТЕСТИРОВАНИЕ ТОЧНОСТИ ML-МОДЕЛИ")
    print("="*60)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    tester = MLAccuracyTester()
    test_cases = tester.create_test_cases()
    
    print(f"Создано {len(test_cases)} тестовых случаев")
    
    # Выполняем тесты
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}/{len(test_cases)} Тестируем: {test_case['name']}")
        result = await tester.test_single_prediction(test_case)
        results.append(result)
        
        if result['success']:
            print(f"   ✅ {result['prediction']} (уверенность: {result['confidence']:.3f})")
        else:
            print(f"   ❌ Ошибка: {result.get('error', 'Unknown')}")
    
    # Анализируем результаты
    analysis = tester.analyze_results(results)
    tester.print_analysis(analysis)
    
    return analysis['overall_accuracy'] >= 60

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        exit(1) 