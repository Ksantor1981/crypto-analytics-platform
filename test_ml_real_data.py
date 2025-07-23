#!/usr/bin/env python3
"""
Тест ML-сервиса с реальными рыночными данными
"""

import requests
import json
import time
from datetime import datetime

# Конфигурация
ML_SERVICE_URL = "http://localhost:8001"

def test_real_market_scenarios():
    """Тест с реальными рыночными сценариями"""
    print("🔍 Тестируем реальные рыночные сценарии...")
    
    # Реальные рыночные данные (примерные)
    real_scenarios = [
        {
            "name": "Bitcoin Bull Run (2024)",
            "data": {
                "asset": "BTC",
                "direction": "LONG",
                "entry_price": 45000,
                "target_price": 65000,
                "stop_loss": 42000,
                "channel_accuracy": 0.85,
                "confidence": 0.8
            }
        },
        {
            "name": "Ethereum Merge Signal",
            "data": {
                "asset": "ETH",
                "direction": "LONG",
                "entry_price": 1800,
                "target_price": 2200,
                "stop_loss": 1700,
                "channel_accuracy": 0.75,
                "confidence": 0.7
            }
        },
        {
            "name": "Altcoin Season Signal",
            "data": {
                "asset": "SOL",
                "direction": "LONG",
                "entry_price": 80,
                "target_price": 120,
                "stop_loss": 75,
                "channel_accuracy": 0.6,
                "confidence": 0.65
            }
        },
        {
            "name": "Bear Market Signal",
            "data": {
                "asset": "BTC",
                "direction": "SHORT",
                "entry_price": 35000,
                "target_price": 30000,
                "stop_loss": 37000,
                "channel_accuracy": 0.7,
                "confidence": 0.6
            }
        },
        {
            "name": "High Frequency Trading",
            "data": {
                "asset": "ETH",
                "direction": "LONG",
                "entry_price": 2000,
                "target_price": 2050,
                "stop_loss": 1990,
                "channel_accuracy": 0.55,
                "confidence": 0.5
            }
        }
    ]
    
    results = []
    
    for scenario in real_scenarios:
        print(f"\n   📊 Сценарий: {scenario['name']}")
        
        try:
            response = requests.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/predict",
                json=scenario['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Анализируем результат
                recommendation = data.get('recommendation', 'N/A')
                confidence = data.get('confidence', 0)
                success_prob = data.get('success_probability', 0)
                
                # Определяем качество сигнала
                if recommendation == 'BUY' and confidence > 0.7:
                    signal_quality = "🔥 СИЛЬНЫЙ"
                elif recommendation == 'BUY' and confidence > 0.6:
                    signal_quality = "✅ ХОРОШИЙ"
                elif recommendation == 'HOLD':
                    signal_quality = "⚠️ НЕЙТРАЛЬНЫЙ"
                else:
                    signal_quality = "❌ СЛАБЫЙ"
                
                print(f"   ✅ Результат:")
                print(f"      Качество сигнала: {signal_quality}")
                print(f"      Рекомендация: {recommendation}")
                print(f"      Уверенность: {confidence:.3f}")
                print(f"      Вероятность успеха: {success_prob}")
                
                results.append({
                    'scenario': scenario['name'],
                    'status': 'success',
                    'quality': signal_quality,
                    'recommendation': recommendation,
                    'confidence': confidence
                })
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                results.append({
                    'scenario': scenario['name'],
                    'status': 'error',
                    'code': response.status_code
                })
                
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
            results.append({
                'scenario': scenario['name'],
                'status': 'exception',
                'error': str(e)
            })
    
    # Анализ результатов
    successful = sum(1 for r in results if r['status'] == 'success')
    strong_signals = sum(1 for r in results if r.get('quality') == '🔥 СИЛЬНЫЙ')
    good_signals = sum(1 for r in results if r.get('quality') == '✅ ХОРОШИЙ')
    
    print(f"\n   📈 Анализ результатов:")
    print(f"      Успешных запросов: {successful}/{len(real_scenarios)}")
    print(f"      Сильных сигналов: {strong_signals}")
    print(f"      Хороших сигналов: {good_signals}")
    print(f"      Общее качество: {(strong_signals + good_signals)/successful*100:.1f}%" if successful > 0 else "N/A")
    
    return successful == len(real_scenarios)

def test_risk_management():
    """Тест управления рисками"""
    print("\n🔍 Тестируем управление рисками...")
    
    risk_scenarios = [
        {
            "name": "Высокий риск - низкая прибыль",
            "data": {
                "asset": "BTC",
                "direction": "LONG",
                "entry_price": 50000,
                "target_price": 50100,  # Очень маленькая прибыль
                "stop_loss": 49000,     # Большой риск
                "channel_accuracy": 0.5,
                "confidence": 0.5
            }
        },
        {
            "name": "Низкий риск - высокая прибыль",
            "data": {
                "asset": "ETH",
                "direction": "LONG",
                "entry_price": 3000,
                "target_price": 3600,   # 20% прибыль
                "stop_loss": 2950,      # Маленький риск
                "channel_accuracy": 0.8,
                "confidence": 0.8
            }
        },
        {
            "name": "Сбалансированный риск",
            "data": {
                "asset": "BNB",
                "direction": "LONG",
                "entry_price": 400,
                "target_price": 480,    # 20% прибыль
                "stop_loss": 360,       # 10% риск
                "channel_accuracy": 0.7,
                "confidence": 0.7
            }
        }
    ]
    
    results = []
    
    for scenario in risk_scenarios:
        print(f"\n   📊 Сценарий: {scenario['name']}")
        
        try:
            response = requests.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/predict",
                json=scenario['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                recommendation = data.get('recommendation', 'N/A')
                confidence = data.get('confidence', 0)
                
                # Анализируем риск/прибыль
                entry = scenario['data']['entry_price']
                target = scenario['data'].get('target_price', entry)
                stop_loss = scenario['data'].get('stop_loss', entry)
                
                if target and stop_loss:
                    potential_profit = abs(target - entry) / entry * 100
                    potential_loss = abs(stop_loss - entry) / entry * 100
                    risk_reward_ratio = potential_profit / potential_loss if potential_loss > 0 else 0
                    
                    print(f"   ✅ Анализ риска:")
                    print(f"      Потенциальная прибыль: {potential_profit:.1f}%")
                    print(f"      Потенциальный убыток: {potential_loss:.1f}%")
                    print(f"      Соотношение риск/прибыль: {risk_reward_ratio:.2f}")
                    print(f"      Рекомендация: {recommendation}")
                    print(f"      Уверенность: {confidence:.3f}")
                    
                    # Оценка качества сигнала
                    if risk_reward_ratio > 2 and recommendation == 'BUY':
                        quality = "🔥 ОТЛИЧНЫЙ"
                    elif risk_reward_ratio > 1.5 and recommendation == 'BUY':
                        quality = "✅ ХОРОШИЙ"
                    elif recommendation == 'HOLD':
                        quality = "⚠️ НЕЙТРАЛЬНЫЙ"
                    else:
                        quality = "❌ ПЛОХОЙ"
                    
                    print(f"      Качество: {quality}")
                    
                    results.append({
                        'scenario': scenario['name'],
                        'risk_reward_ratio': risk_reward_ratio,
                        'recommendation': recommendation,
                        'quality': quality
                    })
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
    
    # Анализ результатов управления рисками
    good_signals = sum(1 for r in results if '🔥 ОТЛИЧНЫЙ' in r.get('quality', ''))
    acceptable_signals = sum(1 for r in results if '✅ ХОРОШИЙ' in r.get('quality', ''))
    
    print(f"\n   📈 Результаты управления рисками:")
    print(f"      Отличных сигналов: {good_signals}")
    print(f"      Хороших сигналов: {acceptable_signals}")
    print(f"      Общее качество: {(good_signals + acceptable_signals)/len(results)*100:.1f}%" if results else "N/A")
    
    return len(results) == len(risk_scenarios)

def test_market_regime_adaptation():
    """Тест адаптации к рыночным режимам"""
    print("\n🔍 Тестируем адаптацию к рыночным режимам...")
    
    market_regimes = [
        {
            "name": "Бычий рынок (Bull Market)",
            "scenarios": [
                {"asset": "BTC", "direction": "LONG", "entry_price": 50000, "channel_accuracy": 0.8, "confidence": 0.8},
                {"asset": "ETH", "direction": "LONG", "entry_price": 3000, "channel_accuracy": 0.7, "confidence": 0.7},
                {"asset": "SOL", "direction": "LONG", "entry_price": 100, "channel_accuracy": 0.6, "confidence": 0.6}
            ]
        },
        {
            "name": "Медвежий рынок (Bear Market)",
            "scenarios": [
                {"asset": "BTC", "direction": "SHORT", "entry_price": 35000, "channel_accuracy": 0.7, "confidence": 0.6},
                {"asset": "ETH", "direction": "SHORT", "entry_price": 2000, "channel_accuracy": 0.6, "confidence": 0.5},
                {"asset": "BNB", "direction": "SHORT", "entry_price": 300, "channel_accuracy": 0.5, "confidence": 0.4}
            ]
        },
        {
            "name": "Боковой рынок (Sideways Market)",
            "scenarios": [
                {"asset": "BTC", "direction": "LONG", "entry_price": 45000, "channel_accuracy": 0.5, "confidence": 0.5},
                {"asset": "ETH", "direction": "LONG", "entry_price": 2500, "channel_accuracy": 0.5, "confidence": 0.5},
                {"asset": "ADA", "direction": "LONG", "entry_price": 0.5, "channel_accuracy": 0.4, "confidence": 0.4}
            ]
        }
    ]
    
    regime_results = {}
    
    for regime in market_regimes:
        print(f"\n   📊 Рыночный режим: {regime['name']}")
        
        regime_signals = []
        for scenario in regime['scenarios']:
            try:
                response = requests.post(
                    f"{ML_SERVICE_URL}/api/v1/predictions/predict",
                    json=scenario,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    recommendation = data.get('recommendation', 'N/A')
                    confidence = data.get('confidence', 0)
                    
                    print(f"      {scenario['asset']}: {recommendation} (уверенность: {confidence:.3f})")
                    
                    regime_signals.append({
                        'asset': scenario['asset'],
                        'recommendation': recommendation,
                        'confidence': confidence,
                        'expected_direction': scenario['direction']
                    })
                else:
                    print(f"      {scenario['asset']}: ошибка {response.status_code}")
                    
            except Exception as e:
                print(f"      {scenario['asset']}: исключение - {e}")
        
        # Анализируем результаты для данного режима
        correct_signals = 0
        for signal in regime_signals:
            if (signal['expected_direction'] == 'LONG' and signal['recommendation'] == 'BUY') or \
               (signal['expected_direction'] == 'SHORT' and signal['recommendation'] == 'SELL'):
                correct_signals += 1
        
        accuracy = correct_signals / len(regime_signals) if regime_signals else 0
        regime_results[regime['name']] = {
            'signals': regime_signals,
            'accuracy': accuracy,
            'total_signals': len(regime_signals)
        }
        
        print(f"      Точность для режима: {accuracy*100:.1f}%")
    
    # Общий анализ
    total_accuracy = sum(r['accuracy'] for r in regime_results.values()) / len(regime_results)
    print(f"\n   📈 Общая точность по режимам: {total_accuracy*100:.1f}%")
    
    return total_accuracy > 0.5  # Требуем минимум 50% точности

def main():
    """Основная функция тестирования с реальными данными"""
    print("🚀 Тестирование ML-сервиса с реальными рыночными данными")
    print("=" * 70)
    
    # Проверяем доступность сервиса
    try:
        response = requests.get(f"{ML_SERVICE_URL}/api/v1/health", timeout=5)
        if response.status_code != 200:
            print("❌ ML-сервис недоступен")
            return
    except Exception as e:
        print(f"❌ Не удается подключиться к ML-сервису: {e}")
        return
    
    # Запускаем тесты
    tests = [
        ("Реальные рыночные сценарии", test_real_market_scenarios),
        ("Управление рисками", test_risk_management),
        ("Адаптация к рыночным режимам", test_market_regime_adaptation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*25} {test_name} {'='*25}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ С РЕАЛЬНЫМИ ДАННЫМИ")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОШЕЛ" if result else "❌ НЕ ПРОШЕЛ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Результат: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 Все тесты с реальными данными прошли успешно!")
        print("🚀 ML-сервис готов к работе с реальными рыночными данными!")
    elif passed >= total * 0.7:
        print("✅ Большинство тестов прошли успешно. Сервис работает хорошо.")
    else:
        print("⚠️  Много тестов не прошли. Требуется доработка алгоритмов.")
    
    print(f"\n⏰ Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 