#!/usr/bin/env python3
"""
Комплексный тест работы с реальными данными Bybit
Тестирует: цены, свечи, рыночные данные, интеграцию с ML-сервисом
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import logging
import sys
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Добавляем путь к workers для импорта
workers_path = os.path.join(os.path.dirname(__file__), 'workers')
sys.path.insert(0, workers_path)

# Импорты из нашего проекта
try:
    from exchange.bybit_client import BybitClient, bybit_client
    from real_data_config import CRYPTO_SYMBOLS, SYMBOL_METADATA
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Проверьте, что файлы bybit_client.py и real_data_config.py существуют в папке workers")
    sys.exit(1)

class RealDataTester:
    """Тестер для работы с реальными данными Bybit"""
    
    def __init__(self):
        self.bybit_client = None
        self.ml_service_url = "http://localhost:8001"
        self.test_results = {}
        
    async def __aenter__(self):
        self.bybit_client = BybitClient()
        await self.bybit_client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.bybit_client:
            await self.bybit_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def test_bybit_connection(self) -> bool:
        """Тест подключения к Bybit API"""
        print("🔌 Тестирование подключения к Bybit...")
        
        try:
            connection_ok = await self.bybit_client.test_connection()
            if connection_ok:
                print("   ✅ Подключение к Bybit успешно")
                self.test_results['connection'] = True
                return True
            else:
                print("   ❌ Ошибка подключения к Bybit")
                self.test_results['connection'] = False
                return False
        except Exception as e:
            print(f"   ❌ Ошибка при тестировании подключения: {e}")
            self.test_results['connection'] = False
            return False
    
    async def test_current_prices(self) -> Dict[str, Decimal]:
        """Тест получения текущих цен"""
        print("\n💰 Тестирование получения текущих цен...")
        
        try:
            # Тестируем основные пары
            test_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOGEUSDT"]
            prices = await self.bybit_client.get_current_prices(test_symbols)
            
            if prices:
                print(f"   ✅ Получено цен для {len(prices)} пар:")
                for symbol, price in prices.items():
                    print(f"      {symbol}: ${price:,.4f}")
                
                self.test_results['prices'] = {
                    'count': len(prices),
                    'symbols': list(prices.keys()),
                    'sample_price': str(prices.get('BTCUSDT', 0))
                }
                return prices
            else:
                print("   ❌ Не удалось получить цены")
                self.test_results['prices'] = False
                return {}
                
        except Exception as e:
            print(f"   ❌ Ошибка при получении цен: {e}")
            self.test_results['prices'] = False
            return {}
    
    async def test_klines_data(self) -> Dict[str, List]:
        """Тест получения данных свечей"""
        print("\n📊 Тестирование получения данных свечей...")
        
        try:
            klines_data = {}
            # Используем правильные интервалы для Bybit API
            intervals = ["1", "5", "15", "60", "240", "D"]  # 1m, 5m, 15m, 1h, 4h, 1d
            
            for interval in intervals:
                klines = await self.bybit_client.get_klines("BTCUSDT", interval, 24)
                if klines:
                    klines_data[interval] = klines
                    print(f"   ✅ {interval}: {len(klines)} свечей")
                    
                    # Показываем последнюю свечу
                    if klines:
                        last_kline = klines[-1]
                        print(f"      Последняя свеча: O:{last_kline['open']:.2f} H:{last_kline['high']:.2f} L:{last_kline['low']:.2f} C:{last_kline['close']:.2f}")
                else:
                    print(f"   ❌ {interval}: не удалось получить данные")
            
            self.test_results['klines'] = {
                'intervals': list(klines_data.keys()),
                'total_klines': sum(len(klines) for klines in klines_data.values())
            }
            return klines_data
            
        except Exception as e:
            print(f"   ❌ Ошибка при получении свечей: {e}")
            self.test_results['klines'] = False
            return {}
    
    async def test_market_data(self) -> Dict[str, Dict]:
        """Тест получения рыночных данных"""
        print("\n📈 Тестирование получения рыночных данных...")
        
        try:
            test_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
            market_data = await self.bybit_client.get_market_data(test_symbols)
            
            if market_data:
                print(f"   ✅ Получены рыночные данные для {len(market_data)} пар:")
                
                for symbol, data in market_data.items():
                    print(f"      {symbol}:")
                    print(f"        Цена: ${data['current_price']:,.4f}")
                    print(f"        Изменение 24ч: {data.get('change_24h', 0):+.2f}%")
                    print(f"        Объем 24ч: {data.get('volume_24h', 0):,.0f}")
                    print(f"        High 24ч: ${data.get('high_24h', 0):,.4f}")
                    print(f"        Low 24ч: ${data.get('low_24h', 0):,.4f}")
                
                self.test_results['market_data'] = {
                    'count': len(market_data),
                    'symbols': list(market_data.keys())
                }
                return market_data
            else:
                print("   ❌ Не удалось получить рыночные данные")
                self.test_results['market_data'] = False
                return {}
                
        except Exception as e:
            print(f"   ❌ Ошибка при получении рыночных данных: {e}")
            self.test_results['market_data'] = False
            return {}
    
    async def test_ml_service_integration(self, market_data: Dict) -> bool:
        """Тест интеграции с ML-сервисом"""
        print("\n🤖 Тестирование интеграции с ML-сервисом...")
        
        try:
            # Проверяем доступность ML-сервиса
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{self.ml_service_url}/api/v1/health/", timeout=5) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            print("   ✅ ML-сервис доступен")
                            print(f"      Статус: {health_data.get('status', 'unknown')}")
                            print(f"      Версия: {health_data.get('version', 'unknown')}")
                            print(f"      Модель: {health_data.get('model_info', {}).get('type', 'unknown')}")
                        else:
                            print(f"   ⚠️ ML-сервис отвечает с кодом {response.status}")
                            return False
                except Exception as e:
                    print(f"   ❌ ML-сервис недоступен: {e}")
                    return False
            
            # Подготавливаем данные для ML-сервиса
            if not market_data:
                print("   ⚠️ Нет рыночных данных для ML-сервиса")
                return False
            
            # Берем данные BTCUSDT для анализа
            btc_data = market_data.get("BTCUSDT")
            if not btc_data:
                print("   ⚠️ Нет данных BTCUSDT для анализа")
                return False
            
            # Формируем запрос к ML-сервису
            ml_request = {
                "asset": "BTCUSDT",
                "entry_price": float(btc_data['current_price']),
                "target_price": float(btc_data['current_price']) * 1.02,  # +2% target
                "stop_loss": float(btc_data['current_price']) * 0.98,    # -2% stop loss
                "direction": "LONG"
            }
            
            # Отправляем запрос к ML-сервису
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{self.ml_service_url}/api/v1/predictions/predict",
                        json=ml_request,
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            ml_response = await response.json()
                            print("   ✅ ML-сервис обработал запрос")
                            print(f"      Прогноз: {ml_response.get('prediction', 'N/A')}")
                            print(f"      Уверенность: {ml_response.get('confidence', 'N/A')}")
                            
                            self.test_results['ml_integration'] = True
                            return True
                        else:
                            print(f"   ❌ ML-сервис вернул ошибку: {response.status}")
                            self.test_results['ml_integration'] = False
                            return False
                            
                except Exception as e:
                    print(f"   ❌ Ошибка при обращении к ML-сервису: {e}")
                    self.test_results['ml_integration'] = False
                    return False
                    
        except Exception as e:
            print(f"   ❌ Общая ошибка интеграции с ML: {e}")
            self.test_results['ml_integration'] = False
            return False
    
    async def test_performance_metrics(self) -> Dict:
        """Тест производительности"""
        print("\n⚡ Тестирование производительности...")
        
        try:
            performance_data = {}
            
            # Тест скорости получения цен
            start_time = time.time()
            prices = await self.bybit_client.get_current_prices(["BTCUSDT", "ETHUSDT"])
            price_time = time.time() - start_time
            
            # Тест скорости получения свечей
            start_time = time.time()
            klines = await self.bybit_client.get_klines("BTCUSDT", "1h", 24)
            kline_time = time.time() - start_time
            
            # Тест скорости получения рыночных данных
            start_time = time.time()
            market_data = await self.bybit_client.get_market_data(["BTCUSDT"])
            market_time = time.time() - start_time
            
            performance_data = {
                'price_request_time': price_time,
                'kline_request_time': kline_time,
                'market_data_time': market_time,
                'total_requests': 3
            }
            
            print(f"   ✅ Время запроса цен: {price_time:.3f}с")
            print(f"   ✅ Время запроса свечей: {kline_time:.3f}с")
            print(f"   ✅ Время запроса рыночных данных: {market_time:.3f}с")
            print(f"   ✅ Общее время: {sum([price_time, kline_time, market_time]):.3f}с")
            
            self.test_results['performance'] = performance_data
            return performance_data
            
        except Exception as e:
            print(f"   ❌ Ошибка при тестировании производительности: {e}")
            self.test_results['performance'] = False
            return {}
    
    async def test_data_quality(self, market_data: Dict) -> Dict:
        """Тест качества данных"""
        print("\n🔍 Тестирование качества данных...")
        
        try:
            quality_report = {
                'total_symbols': len(market_data),
                'valid_prices': 0,
                'valid_volumes': 0,
                'valid_changes': 0,
                'issues': []
            }
            
            for symbol, data in market_data.items():
                # Проверяем цену
                if data.get('current_price', 0) > 0:
                    quality_report['valid_prices'] += 1
                else:
                    quality_report['issues'].append(f"{symbol}: неверная цена")
                
                # Проверяем объем
                if data.get('volume_24h', 0) >= 0:
                    quality_report['valid_volumes'] += 1
                else:
                    quality_report['issues'].append(f"{symbol}: неверный объем")
                
                # Проверяем изменение цены
                change = data.get('change_24h', 0)
                if -100 <= change <= 1000:  # Реалистичные пределы
                    quality_report['valid_changes'] += 1
                else:
                    quality_report['issues'].append(f"{symbol}: неверное изменение цены {change}%")
            
            print(f"   ✅ Проверено символов: {quality_report['total_symbols']}")
            print(f"   ✅ Валидных цен: {quality_report['valid_prices']}")
            print(f"   ✅ Валидных объемов: {quality_report['valid_volumes']}")
            print(f"   ✅ Валидных изменений: {quality_report['valid_changes']}")
            
            if quality_report['issues']:
                print("   ⚠️ Найдены проблемы:")
                for issue in quality_report['issues']:
                    print(f"      - {issue}")
            else:
                print("   ✅ Проблем с качеством данных не найдено")
            
            self.test_results['data_quality'] = quality_report
            return quality_report
            
        except Exception as e:
            print(f"   ❌ Ошибка при проверке качества данных: {e}")
            self.test_results['data_quality'] = False
            return {}
    
    def print_summary(self):
        """Вывод итогового отчета"""
        print("\n" + "="*60)
        print("📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if result is not False and result is not None)
        
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено успешно: {passed_tests}")
        print(f"Успешность: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nДетали по тестам:")
        for test_name, result in self.test_results.items():
            status = "✅ ПРОЙДЕН" if result and result is not False else "❌ ПРОВАЛЕН"
            print(f"  {test_name}: {status}")
            
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, (int, float, str)):
                        print(f"    {key}: {value}")
        
        print("\n" + "="*60)
        
        if passed_tests == total_tests:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print("⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        
        return passed_tests == total_tests

async def main():
    """Основная функция тестирования"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ РЕАЛЬНЫХ ДАННЫХ BYBIT")
    print("="*60)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    async with RealDataTester() as tester:
        # Последовательное выполнение тестов
        connection_ok = await tester.test_bybit_connection()
        
        if not connection_ok:
            print("❌ Тестирование прервано из-за проблем с подключением")
            return False
        
        # Тестируем получение данных
        prices = await tester.test_current_prices()
        klines = await tester.test_klines_data()
        market_data = await tester.test_market_data()
        
        # Тестируем интеграцию с ML-сервисом
        await tester.test_ml_service_integration(market_data)
        
        # Тестируем производительность
        await tester.test_performance_metrics()
        
        # Тестируем качество данных
        await tester.test_data_quality(market_data)
        
        # Выводим итоговый отчет
        success = tester.print_summary()
        
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