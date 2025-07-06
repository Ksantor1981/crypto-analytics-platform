"""
Полная интеграция Telegram коллектора с Backend API
Объединяет сбор сигналов и отправку в основную систему
"""
import asyncio
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Добавляем путь для импортов
sys.path.append(str(Path(__file__).parent))

from real_telegram_collector import RealTelegramCollector, TELETHON_AVAILABLE
from backend_integration import TelegramToBackendBridge

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FullTelegramIntegration:
    """Полная интеграция Telegram коллектора с Backend"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.collector = RealTelegramCollector(use_real_config=True)
        self.bridge = TelegramToBackendBridge(backend_url)
        self.running = False
        
    async def initialize(self) -> bool:
        """Инициализация всех компонентов"""
        logger.info("🚀 Инициализация полной Telegram интеграции...")
        
        if not TELETHON_AVAILABLE:
            logger.error("❌ Telethon не установлен!")
            return False
        
        # Инициализируем коллектор
        if not await self.collector.initialize():
            logger.error("❌ Не удалось инициализировать Telegram коллектор")
            return False
            
        logger.info("✅ Инициализация завершена успешно")
        return True
    
    async def collect_and_send_batch(self, limit: int = 100) -> Dict:
        """Сбор пакета сообщений и отправка в backend"""
        logger.info(f"📡 Начинаем сбор последних {limit} сообщений...")
        
        # Собираем сигналы
        signals = await self.collector.collect_recent_messages(limit=limit)
        
        if not signals:
            logger.warning("⚠️ Сигналы не найдены")
            return {"error": "Сигналы не найдены"}
        
        logger.info(f"📊 Найдено {len(signals)} сигналов")
        
        # Отправляем в backend
        results = await self.bridge.process_signals(signals)
        
        # Логируем результаты
        if 'error' not in results:
            logger.info(f"✅ Отправлено {results['success']}/{results['total']} сигналов")
            if results['failed'] > 0:
                logger.warning(f"⚠️ Не удалось отправить {results['failed']} сигналов")
        else:
            logger.error(f"❌ Ошибка обработки: {results['error']}")
            
        return results
    
    async def start_real_time_integration(self):
        """Запуск интеграции в реальном времени"""
        logger.info("🔄 Запуск интеграции в реальном времени...")
        self.running = True
        
        try:
            await self.bridge.start_real_time_bridge(self.collector)
        except KeyboardInterrupt:
            logger.info("⏹️ Остановка по запросу пользователя")
        except Exception as e:
            logger.error(f"❌ Ошибка в real-time режиме: {e}")
        finally:
            self.running = False
            await self.cleanup()
    
    async def run_periodic_collection(self, interval_minutes: int = 15):
        """Периодический сбор и отправка сигналов"""
        logger.info(f"⏰ Запуск периодического сбора каждые {interval_minutes} минут")
        self.running = True
        
        try:
            while self.running:
                logger.info("🔄 Начинаем периодический сбор...")
                
                try:
                    results = await self.collect_and_send_batch(limit=50)
                    logger.info(f"📊 Результаты сбора: {results}")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка в периодическом сборе: {e}")
                
                # Ждем до следующего цикла
                logger.info(f"💤 Ожидание {interval_minutes} минут до следующего сбора...")
                await asyncio.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Остановка периодического сбора")
        finally:
            self.running = False
            await self.cleanup()
    
    async def get_integration_status(self) -> Dict:
        """Получение статуса интеграции"""
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "running": self.running,
            "telethon_available": TELETHON_AVAILABLE,
            "collector_initialized": self.collector.client is not None,
            "backend_url": self.backend_url
        }
        
        # Проверяем доступность backend
        try:
            async with self.bridge.integration as api:
                backend_available = await api.test_connection()
                status["backend_available"] = backend_available
        except:
            status["backend_available"] = False
        
        # Статистика коллектора
        if self.collector.collected_signals:
            status["collector_stats"] = self.collector.get_statistics()
        
        return status
    
    async def test_full_integration(self) -> Dict:
        """Полное тестирование интеграции"""
        logger.info("🧪 Запуск полного тестирования интеграции...")
        
        test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {}
        }
        
        # Тест 1: Инициализация
        try:
            init_success = await self.initialize()
            test_results["tests"]["initialization"] = {
                "success": init_success,
                "message": "Инициализация прошла успешно" if init_success else "Ошибка инициализации"
            }
        except Exception as e:
            test_results["tests"]["initialization"] = {
                "success": False,
                "error": str(e)
            }
        
        if not test_results["tests"]["initialization"]["success"]:
            return test_results
        
        # Тест 2: Проверка каналов
        try:
            channels_info = await self.collector.get_channel_info()
            accessible_channels = sum(1 for c in channels_info.values() if c.get('accessible', False))
            test_results["tests"]["channels"] = {
                "success": accessible_channels > 0,
                "accessible_channels": accessible_channels,
                "total_channels": len(channels_info),
                "details": channels_info
            }
        except Exception as e:
            test_results["tests"]["channels"] = {
                "success": False,
                "error": str(e)
            }
        
        # Тест 3: Сбор сигналов
        try:
            signals = await self.collector.collect_recent_messages(limit=20)
            test_results["tests"]["signal_collection"] = {
                "success": len(signals) >= 0,  # Успех даже если сигналов нет
                "signals_found": len(signals),
                "sample_signal": signals[0] if signals else None
            }
        except Exception as e:
            test_results["tests"]["signal_collection"] = {
                "success": False,
                "error": str(e)
            }
        
        # Тест 4: Backend интеграция
        try:
            async with self.bridge.integration as api:
                backend_available = await api.test_connection()
                test_results["tests"]["backend_integration"] = {
                    "success": backend_available,
                    "message": "Backend доступен" if backend_available else "Backend недоступен"
                }
        except Exception as e:
            test_results["tests"]["backend_integration"] = {
                "success": False,
                "error": str(e)
            }
        
        # Общий результат
        all_tests_passed = all(test.get("success", False) for test in test_results["tests"].values())
        test_results["overall_success"] = all_tests_passed
        
        logger.info(f"🏁 Тестирование завершено. Успех: {all_tests_passed}")
        return test_results
    
    async def cleanup(self):
        """Очистка ресурсов"""
        logger.info("🧹 Очистка ресурсов...")
        
        if self.collector:
            await self.collector.disconnect()
        
        logger.info("✅ Очистка завершена")

# Утилиты для запуска различных режимов
async def run_batch_mode(limit: int = 100):
    """Запуск в режиме пакетного сбора"""
    integration = FullTelegramIntegration()
    
    if await integration.initialize():
        results = await integration.collect_and_send_batch(limit=limit)
        print(f"📊 Результаты: {json.dumps(results, indent=2, ensure_ascii=False)}")
    
    await integration.cleanup()

async def run_real_time_mode():
    """Запуск в режиме реального времени"""
    integration = FullTelegramIntegration()
    
    if await integration.initialize():
        await integration.start_real_time_integration()
    
    await integration.cleanup()

async def run_periodic_mode(interval: int = 15):
    """Запуск в периодическом режиме"""
    integration = FullTelegramIntegration()
    
    if await integration.initialize():
        await integration.run_periodic_collection(interval_minutes=interval)
    
    await integration.cleanup()

async def run_test_mode():
    """Запуск тестирования"""
    integration = FullTelegramIntegration()
    
    results = await integration.test_full_integration()
    print(f"🧪 Результаты тестирования:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    await integration.cleanup()

# Главная функция
async def main():
    """Главная функция с выбором режима"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Telegram Integration with Backend")
    parser.add_argument("--mode", choices=["batch", "realtime", "periodic", "test"], 
                       default="test", help="Режим работы")
    parser.add_argument("--limit", type=int, default=100, 
                       help="Лимит сообщений для пакетного режима")
    parser.add_argument("--interval", type=int, default=15,
                       help="Интервал в минутах для периодического режима")
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Запуск Telegram интеграции в режиме: {args.mode}")
    
    if args.mode == "batch":
        await run_batch_mode(limit=args.limit)
    elif args.mode == "realtime":
        await run_real_time_mode()
    elif args.mode == "periodic":
        await run_periodic_mode(interval=args.interval)
    elif args.mode == "test":
        await run_test_mode()

if __name__ == "__main__":
    if not TELETHON_AVAILABLE:
        print("❌ Telethon не установлен! Установите: pip install telethon")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1) 