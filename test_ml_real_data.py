#!/usr/bin/env python3
"""
Тест ML-модели на реальных данных Bybit
Оценивает точность на реальных рыночных условиях
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import statistics
import sys
import os

# Добавляем путь к workers для импорта
workers_path = os.path.join(os.path.dirname(__file__), 'workers')
sys.path.insert(0, workers_path)

from exchange.bybit_client import BybitClient

class RealDataMLTester:
    """Тестер ML-модели на реальных данных"""
    
    def __init__(self):
        self.ml_service_url = "http://localhost:8001"
        self.bybit_client = None
        self.test_results = []
        
    async def __aenter__(self):
        self.bybit_client = BybitClient()
        await self.bybit_client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.bybit_client:
            await self.bybit_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_real_market_data(self) -> Dict[str, Dict]:
        """Получение реальных рыночных данных"""
        print("📊 Получение реальных рыночных данных...")
        
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOGEUSDT"]
        market_data = await self.bybit_client.get_market_data(symbols)
        
        if market_data:
            print(f"   ✅ Получены данные для {len(market_data)} пар")
            for symbol, data in market_data.items():
                print(f"      {symbol}: ${data['current_price']:,.4f} ({data.get('change_24h', 0):+.2f}%)")
        else:
            print("   ❌ Не удалось получить рыночные данные")
            
        return market_data
    
    def create_realistic_test_cases(self, market_data: Dict) -> List[Dict]:
        """Создание реалистичных тестовых случаев на основе реальных данных"""
        test_cases = []
        
        for symbol, data in market_data.items():
            current_price = float(data['current_price'])
            change_24h = float(data.get('change_24h', 0))
            
            # Тест 1: Консервативная LONG позиция (2% прибыль, 1% риск)
            test_cases.append({
                'name': f'{symbol}_Conservative_Long',
                'request': {
                    'asset': symbol,
                    'entry_price': current_price,
                    'target_price': current_price * 1.02,  # +2%
                    'stop_loss': current_price * 0.99,     # -1%
                    'direction': 'LONG'
                },
                'expected_behavior': 'buy',
                'description': 'Консервативная LONG позиция с хорошим соотношением риск/прибыль'
            })
            
            # Тест 2: Агрессивная LONG позиция (10% прибыль, 5% риск)
            test_cases.append({
                'name': f'{symbol}_Aggressive_Long',
                'request': {
                    'asset': symbol,
                    'entry_price': current_price,
                    'target_price': current_price * 1.10,  # +10%
                    'stop_loss': current_price * 0.95,     # -5%
                    'direction': 'LONG'
                },
                'expected_behavior': 'strong_buy',
                'description': 'Агрессивная LONG позиция с отличным соотношением риск/прибыль'
            })
            
            # Тест 3: Плохая сделка (2% прибыль, 10% риск)
            test_cases.append({
                'name': f'{symbol}_Poor_RR',
                'request': {
                    'asset': symbol,
                    'entry_price': current_price,
                    'target_price': current_price * 1.02,  # +2%
                    'stop_loss': current_price * 0.90,     # -10%
                    'direction': 'LONG'
                },
                'expected_behavior': 'caution',
                'description': 'Плохое соотношение риск/прибыль'
            })
            
            # Тест 4: SHORT позиция (если рынок падает)
            if change_24h < -1:  # Если падение более 1%
                test_cases.append({
                    'name': f'{symbol}_Short_Down',
                    'request': {
                        'asset': symbol,
                        'entry_price': current_price,
                        'target_price': current_price * 0.95,  # -5%
                        'stop_loss': current_price * 1.02,     # +2%
                        'direction': 'SHORT'
                    },
                    'expected_behavior': 'sell',
                    'description': 'SHORT позиция на падающем рынке'
                })
            
            # Тест 5: Нейтральная сделка (1% прибыль, 1% риск)
            test_cases.append({
                'name': f'{symbol}_Neutral',
                'request': {
                    'asset': symbol,
                    'entry_price': current_price,
                    'target_price': current_price * 1.01,  # +1%
                    'stop_loss': current_price * 0.99,     # -1%
                    'direction': 'LONG'
                },
                'expected_behavior': 'neutral',
                'description': 'Нейтральная сделка с равным соотношением'
            })
        
        return test_cases
    
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
                            'description': test_case['description'],
                            'request': test_case['request'],
                            'response': result,
                            'success': True,
                            'prediction': result.get('prediction', 'UNKNOWN'),
                            'confidence': result.get('confidence', 0.0),
                            'success_probability': result.get('success_probability', 0.0),
                            'expected_behavior': test_case.get('expected_behavior', 'neutral')
                        }
                    else:
                        return {
                            'test_case': test_case['name'],
                            'description': test_case['description'],
                            'request': test_case['request'],
                            'success': False,
                            'error': f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                'test_case': test_case['name'],
                'description': test_case['description'],
                'request': test_case['request'],
                'success': False,
                'error': str(e)
            }
    
    def analyze_realistic_results(self, results: List[Dict]) -> Dict:
        """Анализ результатов на реалистичных данных"""
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
        
        # Статистика по уверенности и вероятности успеха
        confidences = [r['confidence'] for r in successful_tests]
        probabilities = [r['success_probability'] for r in successful_tests]
        
        # Распределение предсказаний
        prediction_counts = {}
        for result in successful_tests:
            pred = result['prediction']
            prediction_counts[pred] = prediction_counts.get(pred, 0) + 1
        
        # Анализ по типам сделок
        trade_type_analysis = {}
        for result in successful_tests:
            trade_type = result['expected_behavior']
            if trade_type not in trade_type_analysis:
                trade_type_analysis[trade_type] = {
                    'total': 0, 'correct': 0, 'avg_confidence': 0.0, 'avg_probability': 0.0
                }
            
            analysis = trade_type_analysis[trade_type]
            analysis['total'] += 1
            analysis['avg_confidence'] += result['confidence']
            analysis['avg_probability'] += result['success_probability']
            
            # Проверяем соответствие ожидаемому поведению
            direction = result['request'].get('direction', 'LONG')
            actual = result['prediction']
            is_correct = False
            
            if trade_type == 'strong_buy' and direction == 'LONG' and 'СИЛЬНАЯ ПОКУПКА' in actual:
                is_correct = True
            elif trade_type == 'buy' and direction == 'LONG' and 'ПОКУПКА' in actual:
                is_correct = True
            elif trade_type == 'sell' and direction == 'SHORT' and 'ПРОДАЖА' in actual:
                is_correct = True
            elif trade_type == 'neutral' and 'НЕЙТРАЛЬНО' in actual:
                is_correct = True
            elif trade_type == 'caution' and ('ОСТОРОЖНО' in actual or 'ИЗБЕГАТЬ' in actual):
                is_correct = True
            
            if is_correct:
                analysis['correct'] += 1
        
        # Нормализуем средние значения
        for trade_type in trade_type_analysis:
            analysis = trade_type_analysis[trade_type]
            if analysis['total'] > 0:
                analysis['avg_confidence'] /= analysis['total']
                analysis['avg_probability'] /= analysis['total']
        
        # Общая точность
        total_expected = sum(analysis['total'] for analysis in trade_type_analysis.values())
        total_correct = sum(analysis['correct'] for analysis in trade_type_analysis.values())
        overall_accuracy = (total_correct / total_expected * 100) if total_expected > 0 else 0
        
        return {
            'total_tests': len(results),
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'success_rate': (len(successful_tests) / len(results)) * 100,
            'overall_accuracy': overall_accuracy,
            'average_confidence': round(statistics.mean(confidences), 3),
            'average_probability': round(statistics.mean(probabilities), 3),
            'min_confidence': round(min(confidences), 3),
            'max_confidence': round(max(confidences), 3),
            'confidence_std': round(statistics.stdev(confidences), 3) if len(confidences) > 1 else 0,
            'prediction_distribution': prediction_counts,
            'trade_type_analysis': trade_type_analysis,
            'errors': [r.get('error', 'Unknown error') for r in failed_tests]
        }
    
    def print_realistic_analysis(self, analysis: Dict):
        """Вывод анализа реалистичных результатов"""
        print("\n" + "="*70)
        print("📊 АНАЛИЗ ML-МОДЕЛИ НА РЕАЛЬНЫХ ДАННЫХ")
        print("="*70)
        
        print(f"Всего тестов: {analysis['total_tests']}")
        print(f"Успешных тестов: {analysis['successful_tests']}")
        print(f"Проваленных тестов: {analysis['failed_tests']}")
        print(f"Успешность запросов: {analysis['success_rate']:.1f}%")
        print(f"Общая точность предсказаний: {analysis['overall_accuracy']:.1f}%")
        
        print(f"\n📈 Статистика модели:")
        print(f"  Средняя уверенность: {analysis['average_confidence']}")
        print(f"  Средняя вероятность успеха: {analysis['average_probability']}")
        print(f"  Диапазон уверенности: {analysis['min_confidence']} - {analysis['max_confidence']}")
        print(f"  Стандартное отклонение: {analysis['confidence_std']}")
        
        print(f"\n🎯 Распределение предсказаний:")
        for pred, count in analysis['prediction_distribution'].items():
            percentage = (count / analysis['successful_tests']) * 100
            print(f"  {pred}: {count} ({percentage:.1f}%)")
        
        print(f"\n✅ Анализ по типам сделок:")
        for trade_type, stats in analysis['trade_type_analysis'].items():
            accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {trade_type}:")
            print(f"    Точность: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
            print(f"    Средняя уверенность: {stats['avg_confidence']:.3f}")
            print(f"    Средняя вероятность: {stats['avg_probability']:.3f}")
        
        if analysis['errors']:
            print(f"\n❌ Ошибки:")
            for error in analysis['errors']:
                print(f"  - {error}")
        
        print("\n" + "="*70)
        
        # Оценка качества модели
        if analysis['overall_accuracy'] >= 70:
            print("🎉 ОТЛИЧНАЯ ТОЧНОСТЬ МОДЕЛИ НА РЕАЛЬНЫХ ДАННЫХ!")
        elif analysis['overall_accuracy'] >= 50:
            print("✅ ХОРОШАЯ ТОЧНОСТЬ МОДЕЛИ НА РЕАЛЬНЫХ ДАННЫХ")
        elif analysis['overall_accuracy'] >= 30:
            print("⚠️ СРЕДНЯЯ ТОЧНОСТЬ МОДЕЛИ НА РЕАЛЬНЫХ ДАННЫХ")
        else:
            print("❌ НИЗКАЯ ТОЧНОСТЬ МОДЕЛИ НА РЕАЛЬНЫХ ДАННЫХ")
        
        print("="*70)
        
        return analysis['overall_accuracy'] >= 50

async def main():
    """Основная функция тестирования на реальных данных"""
    print("🧪 ТЕСТИРОВАНИЕ ML-МОДЕЛИ НА РЕАЛЬНЫХ ДАННЫХ BYBIT")
    print("="*70)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    async with RealDataMLTester() as tester:
        # Получаем реальные рыночные данные
        market_data = await tester.get_real_market_data()
        
        if not market_data:
            print("❌ Не удалось получить рыночные данные для тестирования")
            return False
        
        # Создаем реалистичные тестовые случаи
        test_cases = tester.create_realistic_test_cases(market_data)
        print(f"\nСоздано {len(test_cases)} реалистичных тестовых случаев")
        
        # Выполняем тесты
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}/{len(test_cases)} Тестируем: {test_case['name']}")
            print(f"   {test_case['description']}")
            result = await tester.test_single_prediction(test_case)
            results.append(result)
            
            if result['success']:
                print(f"   ✅ {result['prediction']} (уверенность: {result['confidence']:.3f}, вероятность: {result['success_probability']:.3f})")
            else:
                print(f"   ❌ Ошибка: {result.get('error', 'Unknown')}")
        
        # Анализируем результаты
        analysis = tester.analyze_realistic_results(results)
        success = tester.print_realistic_analysis(analysis)
        
        return success

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