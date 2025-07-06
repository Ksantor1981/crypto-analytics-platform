#!/usr/bin/env python3
"""
Быстрый тест доступности реальных данных для ML сервиса
"""
import sys
import os
import asyncio

# Add workers to path
sys.path.append('workers')

def test_imports():
    """Тест импортов"""
    print("🔍 Проверка импортов...")
    
    try:
        from workers.exchange.bybit_client import BybitClient
        print("   ✅ BybitClient импортирован")
        
        from workers.real_data_config import CRYPTO_SYMBOLS
        print(f"   ✅ CRYPTO_SYMBOLS: {len(CRYPTO_SYMBOLS)} символов")
        
        return True, BybitClient
    except ImportError as e:
        print(f"   ❌ Ошибка импорта: {e}")
        return False, None

async def test_bybit_connection(BybitClient):
    """Тест соединения с Bybit"""
    print("\n🌐 Проверка соединения с Bybit...")
    
    try:
        async with BybitClient() as client:
            # Тест соединения
            connection_ok = await client.test_connection()
            print(f"   ✅ Соединение: {'OK' if connection_ok else 'FAILED'}")
            
            if connection_ok:
                # Получаем данные для BTC
                market_data = await client.get_market_data(["BTCUSDT"])
                if "BTCUSDT" in market_data:
                    btc_data = market_data["BTCUSDT"]
                    print(f"   ✅ BTC данные: ${btc_data.get('current_price', 'N/A')}")
                    return True
                else:
                    print("   ❌ Нет данных для BTC")
                    return False
            else:
                return False
                
    except Exception as e:
        print(f"   ❌ Ошибка соединения: {e}")
        return False

def test_ml_service_import_path():
    """Тест пути импорта как в ML сервисе"""
    print("\n📁 Проверка пути импорта ML сервиса...")
    
    # Имитируем путь как в ML сервисе
    ml_workers_path = os.path.join(os.path.dirname(__file__), 'workers')
    if ml_workers_path not in sys.path:
        sys.path.append(ml_workers_path)
    
    try:
        from workers.exchange.bybit_client import BybitClient
        from workers.real_data_config import CRYPTO_SYMBOLS
        print("   ✅ Импорт из ML сервиса пути работает")
        return True
    except ImportError as e:
        print(f"   ❌ Ошибка импорта ML пути: {e}")
        return False

async def main():
    """Основная функция"""
    print("🚀 БЫСТРЫЙ ТЕСТ ДОСТУПНОСТИ РЕАЛЬНЫХ ДАННЫХ")
    print("=" * 50)
    
    # Тест 1: Базовые импорты
    imports_ok, BybitClient = test_imports()
    
    # Тест 2: Путь ML сервиса
    ml_path_ok = test_ml_service_import_path()
    
    # Тест 3: Соединение с Bybit
    if imports_ok and BybitClient:
        bybit_ok = await test_bybit_connection(BybitClient)
    else:
        bybit_ok = False
    
    # Результаты
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ:")
    print(f"   Импорты: {'✅' if imports_ok else '❌'}")
    print(f"   ML путь: {'✅' if ml_path_ok else '❌'}")
    print(f"   Bybit: {'✅' if bybit_ok else '❌'}")
    
    if imports_ok and ml_path_ok and bybit_ok:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОШЛИ!")
        print("   REAL_DATA_AVAILABLE должно быть True")
    else:
        print("\n⚠️ ЕСТЬ ПРОБЛЕМЫ!")
        print("   REAL_DATA_AVAILABLE будет False")
        
        if not imports_ok:
            print("   🔧 Проверьте структуру проекта")
        if not ml_path_ok:
            print("   🔧 Проверьте пути в ML сервисе")
        if not bybit_ok:
            print("   🔧 Проверьте API ключи Bybit")

if __name__ == "__main__":
    asyncio.run(main()) 