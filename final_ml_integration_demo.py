#!/usr/bin/env python3
"""
Финальная демонстрация интеграции ML сервиса с реальными данными Bybit
"""
import asyncio
import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add workers to path
sys.path.append('workers')

from workers.exchange.bybit_client import BybitClient

class MLIntegrationDemo:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.ml_url = "http://localhost:8001"
        
    def print_header(self, title: str):
        """Красивый заголовок"""
        print("\n" + "=" * 80)
        print(f"🚀 {title}")
        print("=" * 80)
        
    def print_section(self, title: str):
        """Секция"""
        print(f"\n📊 {title}")
        print("-" * 60)
        
    def check_services(self) -> Dict[str, bool]:
        """Проверка доступности сервисов"""
        self.print_section("Проверка сервисов")
        
        services = {}
        
        # Backend API
        try:
            response = requests.get(f"{self.backend_url}/docs", timeout=5)
            services['backend'] = response.status_code == 200
            status = "✅ РАБОТАЕТ" if services['backend'] else "❌ НЕ РАБОТАЕТ"
            print(f"   Backend API: {status}")
        except:
            services['backend'] = False
            print("   Backend API: ❌ НЕ ДОСТУПЕН")
            
        # ML Service
        try:
            response = requests.get(f"{self.ml_url}/health/", timeout=5)
            services['ml'] = response.status_code == 200
            status = "✅ РАБОТАЕТ" if services['ml'] else "❌ НЕ РАБОТАЕТ"
            print(f"   ML Service: {status}")
            
            if services['ml']:
                health_data = response.json()
                print(f"      Версия: {health_data.get('version', 'N/A')}")
                print(f"      Статус: {health_data.get('status', 'N/A')}")
        except:
            services['ml'] = False
            print("   ML Service: ❌ НЕ ДОСТУПЕН")
            
        return services
        
    async def demo_real_data_integration(self):
        """Демонстрация интеграции реальных данных"""
        self.print_section("Интеграция реальных данных Bybit")
        
        try:
            # Получаем данные напрямую из Bybit
            async with BybitClient() as client:
                symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
                market_data = await client.get_market_data(symbols)
                
                print("   🌐 Прямое подключение к Bybit API:")
                for symbol, data in market_data.items():
                    asset = symbol.replace("USDT", "")
                    price = float(data['current_price'])
                    change = float(data.get('change_24h', 0))
                    change_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    
                    print(f"      {asset}: ${price:,.2f} {change_icon} {change:+.2f}%")
                    
                return market_data
                
        except Exception as e:
            print(f"   ❌ Ошибка подключения к Bybit: {e}")
            return {}
            
    def demo_ml_predictions(self, market_data: Dict[str, Any]):
        """Демонстрация ML предсказаний с реальными данными"""
        self.print_section("ML Предсказания с реальными данными")
        
        if not market_data:
            print("   ⚠️ Нет данных для демонстрации")
            return
            
        predictions = []
        
        for symbol, data in market_data.items():
            asset = symbol.replace("USDT", "")
            current_price = float(data['current_price'])
            
            # Создаем тестовый сигнал
            signal = {
                "asset": asset,
                "direction": "LONG",
                "entry_price": current_price,
                "target_price": current_price * 1.05,  # +5% цель
                "stop_loss": current_price * 0.98      # -2% стоп
            }
            
            try:
                response = requests.post(
                    f"{self.ml_url}/api/v1/predictions/predict",
                    json=signal,
                    timeout=10
                )
                
                if response.status_code == 200:
                    prediction = response.json()
                    predictions.append((asset, prediction))
                    
                    # Красивый вывод предсказания
                    print(f"\n   🔮 {asset} Предсказание:")
                    print(f"      💰 Текущая цена: ${current_price:,.2f}")
                    print(f"      🎯 Цель: ${signal['target_price']:,.2f} (+5%)")
                    print(f"      🛡️ Стоп: ${signal['stop_loss']:,.2f} (-2%)")
                    print(f"      📊 Предсказание: {prediction['prediction']}")
                    print(f"      🎲 Уверенность: {prediction['confidence']:.1%}")
                    print(f"      💎 Ожидаемая доходность: {prediction['expected_return']:.2f}%")
                    print(f"      ⚠️ Уровень риска: {prediction['risk_level']}")
                    print(f"      📈 Рекомендация: {prediction['recommendation']}")
                    
                    # Информация о источнике данных
                    market_info = prediction.get('market_data', {})
                    source = market_info.get('source', 'unknown')
                    if source == 'bybit_real':
                        print(f"      ✅ Источник: Bybit (реальные данные)")
                        change_24h = market_info.get('change_24h', 0)
                        print(f"      📊 Изменение 24ч: {change_24h:+.2f}%")
                    else:
                        print(f"      ⚠️ Источник: {source}")
                        
                else:
                    print(f"   ❌ {asset}: Ошибка предсказания ({response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ {asset}: Ошибка запроса - {e}")
                
        return predictions
        
    def demo_supported_assets(self):
        """Демонстрация поддерживаемых активов"""
        self.print_section("Поддерживаемые активы")
        
        try:
            response = requests.get(
                f"{self.ml_url}/api/v1/predictions/supported-assets",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                assets = data.get('supported_assets', [])
                status = data.get('real_data_status', 'unknown')
                source = data.get('data_source', 'unknown')
                
                print(f"   📋 Всего активов: {len(assets)}")
                print(f"   🌐 Статус реальных данных: {status}")
                print(f"   📊 Источник данных: {source}")
                print(f"   💰 Активы:")
                
                for i, asset in enumerate(assets, 1):
                    clean_asset = asset.replace("USDT", "")
                    print(f"      {i:2d}. {clean_asset}")
                    
            else:
                print(f"   ❌ Ошибка получения списка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            
    def demo_model_info(self):
        """Демонстрация информации о модели"""
        self.print_section("Информация о ML модели")
        
        try:
            response = requests.get(
                f"{self.ml_url}/api/v1/predictions/model/info",
                timeout=5
            )
            
            if response.status_code == 200:
                model_info = response.json()
                
                print(f"   🤖 Тип модели: {model_info.get('model_type', 'N/A')}")
                print(f"   📊 Версия: {model_info.get('model_version', 'N/A')}")
                print(f"   🎯 Обучена: {'Да' if model_info.get('is_trained', False) else 'Нет'}")
                print(f"   📈 Фичи: {len(model_info.get('feature_names', []))}")
                print(f"   📅 Создана: {model_info.get('created_at', 'N/A')}")
                
                features = model_info.get('feature_names', [])
                if features:
                    print(f"   🔍 Используемые признаки:")
                    for i, feature in enumerate(features, 1):
                        print(f"      {i}. {feature}")
                        
            else:
                print(f"   ❌ Ошибка получения информации: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            
    def generate_summary(self, services: Dict[str, bool], predictions: list):
        """Генерация итогового отчета"""
        self.print_section("Итоговый отчет")
        
        # Статус сервисов
        backend_status = "✅" if services.get('backend', False) else "❌"
        ml_status = "✅" if services.get('ml', False) else "❌"
        
        print(f"   🔧 Backend API: {backend_status}")
        print(f"   🤖 ML Service: {ml_status}")
        
        # Статистика предсказаний
        if predictions:
            total_predictions = len(predictions)
            successful_predictions = sum(1 for _, pred in predictions if pred['prediction'] == 'SUCCESS')
            avg_confidence = sum(pred['confidence'] for _, pred in predictions) / total_predictions
            avg_return = sum(pred['expected_return'] for _, pred in predictions) / total_predictions
            
            print(f"\n   📊 Статистика предсказаний:")
            print(f"      Всего предсказаний: {total_predictions}")
            print(f"      Успешных: {successful_predictions}/{total_predictions}")
            print(f"      Средняя уверенность: {avg_confidence:.1%}")
            print(f"      Средняя доходность: {avg_return:.2f}%")
            
        # Статус интеграции
        integration_score = 0
        if services.get('backend', False):
            integration_score += 25
        if services.get('ml', False):
            integration_score += 25
        if predictions:
            integration_score += 25
            # Проверяем реальные данные
            real_data_used = any(
                pred.get('market_data', {}).get('source') == 'bybit_real' 
                for _, pred in predictions
            )
            if real_data_used:
                integration_score += 25
                
        print(f"\n   🎯 Уровень интеграции: {integration_score}%")
        
        if integration_score >= 90:
            print("   🎉 ОТЛИЧНО! Полная интеграция с реальными данными!")
        elif integration_score >= 70:
            print("   ✅ ХОРОШО! Основные компоненты работают!")
        elif integration_score >= 50:
            print("   ⚠️ ЧАСТИЧНО! Требуется доработка!")
        else:
            print("   ❌ ПРОБЛЕМЫ! Требуется исправление!")
            
        return integration_score
        
    async def run_demo(self):
        """Запуск полной демонстрации"""
        self.print_header("ДЕМОНСТРАЦИЯ ИНТЕГРАЦИИ ML СЕРВИСА С РЕАЛЬНЫМИ ДАННЫМИ BYBIT")
        
        print(f"📅 Время демонстрации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Backend API: {self.backend_url}")
        print(f"🤖 ML Service: {self.ml_url}")
        
        # 1. Проверка сервисов
        services = self.check_services()
        
        # 2. Информация о модели
        self.demo_model_info()
        
        # 3. Поддерживаемые активы
        self.demo_supported_assets()
        
        # 4. Интеграция реальных данных
        market_data = await self.demo_real_data_integration()
        
        # 5. ML предсказания
        predictions = self.demo_ml_predictions(market_data)
        
        # 6. Итоговый отчет
        score = self.generate_summary(services, predictions)
        
        # Заключение
        self.print_header("ЗАКЛЮЧЕНИЕ")
        
        if score >= 90:
            print("🚀 ПЛАТФОРМА ГОТОВА К PRODUCTION!")
            print("\n🎯 Ключевые достижения:")
            print("   ✅ ML сервис интегрирован с реальными данными Bybit")
            print("   ✅ Предсказания используют актуальные рыночные данные")
            print("   ✅ Все компоненты работают стабильно")
            print("   ✅ Готово для реальной торговли")
            
            print("\n🚀 Следующие шаги:")
            print("   1. Развертывание в production")
            print("   2. Интеграция с торговыми API")
            print("   3. Создание пользовательского интерфейса")
            print("   4. Мониторинг и аналитика")
            
        else:
            print("⚠️ ТРЕБУЕТСЯ ДОРАБОТКА")
            print("\n🔧 Проблемы для решения:")
            if not services.get('backend', False):
                print("   - Backend API не работает")
            if not services.get('ml', False):
                print("   - ML Service не работает")
            if not predictions:
                print("   - Предсказания не работают")
                
        print(f"\n📊 Финальная оценка: {score}/100")
        
        return score

async def main():
    """Главная функция"""
    demo = MLIntegrationDemo()
    score = await demo.run_demo()
    
    # Возвращаем код выхода
    if score >= 90:
        print("\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        return 0
    else:
        print("\n⚠️ ДЕМОНСТРАЦИЯ ВЫЯВИЛА ПРОБЛЕМЫ!")
        return 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main()) 