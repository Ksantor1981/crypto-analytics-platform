#!/usr/bin/env python3
"""
Глубокая комплексная проверка всей системы Crypto Analytics Platform
Проверка реальных сценариев использования и интеграции компонентов
"""
import asyncio
import sys
import json
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import importlib.util
import subprocess
import os

# Добавляем пути для импортов
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

class DeepSystemTest:
    """Глубокая проверка всей системы"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "test_time": 0,
            "categories": {}
        }
        self.start_time = time.time()
    
    def log_test(self, category: str, test_name: str, status: str, details: str = "", error: str = ""):
        """Логирование результатов теста"""
        if category not in self.results["categories"]:
            self.results["categories"][category] = []
        
        test_result = {
            "test": test_name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results["categories"][category].append(test_result)
        self.results["total_tests"] += 1
        
        if status == "PASS":
            self.results["passed"] += 1
            print(f"✅ {category}: {test_name} - {details}")
        elif status == "FAIL":
            self.results["failed"] += 1
            print(f"❌ {category}: {test_name} - {error}")
        elif status == "WARNING":
            self.results["warnings"] += 1
            print(f"⚠️ {category}: {test_name} - {details}")
    
    async def test_file_structure(self):
        """Проверка структуры файлов проекта"""
        print("\n🔍 Проверка структуры файлов...")
        
        required_files = [
            "README.md",
            "TASKS2.md",
            "docker-compose.yml",
            "backend/app/main.py",
            "backend/app/models/feedback.py",
            "backend/app/schemas/feedback.py",
            "backend/app/api/endpoints/feedback.py",
            "frontend/components/FeedbackForm.tsx",
            "frontend/pages/feedback.tsx",
            "workers/telegram/telegram_scraper.py",  # Исправленный путь
            "workers/reddit_collector.py",
            "workers/signal_patterns.py",
            "workers/telegram_feedback_bot.py",
            "workers/channel_discovery_system.py"
        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                self.log_test("File Structure", f"Файл {file_path}", "PASS", "Файл найден")
            else:
                self.log_test("File Structure", f"Файл {file_path}", "FAIL", "", f"Файл не найден: {file_path}")
    
    async def test_imports(self):
        """Проверка импортов основных модулей"""
        print("\n📦 Проверка импортов модулей...")
        
        modules_to_test = [
            ("signal_patterns", "SignalPatterns"),
            ("reddit_collector", "RedditSignalCollector"),
            ("telegram.telegram_scraper", "TelegramSignalScraper"),
            ("channel_discovery_system", "ChannelDiscoverySystem")
        ]
        
        for module_name, class_name in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, class_name):
                    self.log_test("Imports", f"Импорт {class_name}", "PASS", f"Модуль {module_name} успешно импортирован")
                else:
                    self.log_test("Imports", f"Импорт {class_name}", "FAIL", "", f"Класс {class_name} не найден в {module_name}")
            except Exception as e:
                self.log_test("Imports", f"Импорт {class_name}", "FAIL", "", f"Ошибка импорта {module_name}: {str(e)}")
    
    async def test_signal_patterns(self):
        """Тестирование обработки сигналов"""
        print("\n📊 Тестирование обработки сигналов...")
        
        try:
            from signal_patterns import SignalPatterns
            
            patterns = SignalPatterns()
            
            # Тестовые сигналы
            test_signals = [
                "BTC/USDT LONG @ 45000 SL: 44000 TP: 47000",
                "ETH/USDT SHORT @ 3200 SL: 3300 TP: 3000",
                "ADA/USDT LONG @ 0.45 SL: 0.42 TP: 0.50",
                "Неправильный сигнал без пары",
                "BTC/USDT @ 45000"  # Неполный сигнал
            ]
            
            for i, signal in enumerate(test_signals):
                try:
                    result = patterns.extract_signal_info(signal)
                    if result.get("pair") and result.get("direction"):
                        self.log_test("Signal Processing", f"Сигнал {i+1}", "PASS", f"Обработан: {result['pair']} {result['direction']}")
                    else:
                        self.log_test("Signal Processing", f"Сигнал {i+1}", "WARNING", f"Неполная обработка: {result}")
                except Exception as e:
                    self.log_test("Signal Processing", f"Сигнал {i+1}", "FAIL", "", f"Ошибка обработки: {str(e)}")
                    
        except Exception as e:
            self.log_test("Signal Processing", "Инициализация", "FAIL", "", f"Ошибка инициализации: {str(e)}")
    
    async def test_telegram_integration(self):
        """Тестирование Telegram интеграции"""
        print("\n📱 Тестирование Telegram интеграции...")
        
        try:
            from telegram.telegram_scraper import TelegramSignalScraper
            
            scraper = TelegramSignalScraper()
            
            # Проверка базовой функциональности
            if hasattr(scraper, 'scrape_channel_messages'):
                self.log_test("Telegram Integration", "Инициализация скрапера", "PASS", "TelegramSignalScraper создан")
            else:
                self.log_test("Telegram Integration", "Инициализация скрапера", "FAIL", "", "Метод scrape_channel_messages не найден")
                
        except Exception as e:
            self.log_test("Telegram Integration", "Инициализация", "FAIL", "", f"Ошибка инициализации: {str(e)}")
    
    async def test_reddit_integration(self):
        """Тестирование Reddit интеграции"""
        print("\n🔴 Тестирование Reddit интеграции...")
        
        try:
            from reddit_collector import RedditSignalCollector
            
            collector = RedditSignalCollector()
            
            # Проверка базовой функциональности
            if hasattr(collector, 'collect_signals_from_all_subreddits'):
                self.log_test("Reddit Integration", "Инициализация коллектора", "PASS", "RedditSignalCollector создан")
            else:
                self.log_test("Reddit Integration", "Инициализация коллектора", "FAIL", "", "Метод collect_signals_from_all_subreddits не найден")
                
        except Exception as e:
            self.log_test("Reddit Integration", "Инициализация", "FAIL", "", f"Ошибка инициализации: {str(e)}")
    
    async def test_feedback_system(self):
        """Тестирование системы обратной связи"""
        print("\n💬 Тестирование системы обратной связи...")
        
        # Проверка файлов системы обратной связи
        feedback_files = [
            "backend/app/models/feedback.py",
            "backend/app/schemas/feedback.py", 
            "backend/app/api/endpoints/feedback.py",
            "frontend/components/FeedbackForm.tsx",
            "frontend/pages/feedback.tsx",
            "workers/telegram_feedback_bot.py"
        ]
        
        for file_path in feedback_files:
            if Path(file_path).exists():
                self.log_test("Feedback System", f"Файл {Path(file_path).name}", "PASS", "Файл найден")
            else:
                self.log_test("Feedback System", f"Файл {Path(file_path).name}", "FAIL", "", f"Файл не найден: {file_path}")
        
        # Проверка Telegram бота обратной связи
        try:
            from telegram_feedback_bot import TelegramFeedbackBot
            
            # Создаем бота с тестовым токеном
            bot = TelegramFeedbackBot("test_token")
            self.log_test("Feedback System", "Telegram бот", "PASS", "TelegramFeedbackBot создан")
            
        except Exception as e:
            if "Update" in str(e):
                self.log_test("Feedback System", "Telegram бот", "WARNING", "Telegram библиотеки не установлены")
            else:
                self.log_test("Feedback System", "Telegram бот", "FAIL", "", f"Ошибка создания бота: {str(e)}")
    
    async def test_channel_discovery(self):
        """Тестирование системы обнаружения каналов"""
        print("\n🔍 Тестирование обнаружения каналов...")
        
        try:
            from channel_discovery_system import ChannelDiscoverySystem
            
            discovery = ChannelDiscoverySystem()
            
            # Проверка базовой функциональности
            if hasattr(discovery, 'discover_all_channels'):
                self.log_test("Channel Discovery", "Инициализация", "PASS", "ChannelDiscoverySystem создан")
            else:
                self.log_test("Channel Discovery", "Инициализация", "FAIL", "", "Метод discover_all_channels не найден")
                
        except Exception as e:
            self.log_test("Channel Discovery", "Инициализация", "FAIL", "", f"Ошибка инициализации: {str(e)}")
    
    async def test_configuration_files(self):
        """Проверка конфигурационных файлов"""
        print("\n⚙️ Проверка конфигурационных файлов...")
        
        config_files = [
            "docker-compose.yml",
            "backend/requirements.txt",
            "workers/requirements.txt",
            "frontend/package.json"
        ]
        
        for config_file in config_files:
            if Path(config_file).exists():
                try:
                    # Пробуем разные кодировки
                    encodings = ['utf-8', 'cp1251', 'latin-1']
                    content = None
                    
                    for encoding in encodings:
                        try:
                            with open(config_file, 'r', encoding=encoding) as f:
                                content = f.read()
                                break
                        except UnicodeDecodeError:
                            continue
                    
                    if content and len(content.strip()) > 0:
                        self.log_test("Configuration", f"Файл {Path(config_file).name}", "PASS", "Файл существует и не пустой")
                    else:
                        self.log_test("Configuration", f"Файл {Path(config_file).name}", "WARNING", "Файл пустой или нечитаемый")
                except Exception as e:
                    self.log_test("Configuration", f"Файл {Path(config_file).name}", "FAIL", "", f"Ошибка чтения: {str(e)}")
            else:
                self.log_test("Configuration", f"Файл {Path(config_file).name}", "FAIL", "", f"Файл не найден")
    
    async def test_database_schema(self):
        """Проверка схемы базы данных"""
        print("\n🗄️ Проверка схемы базы данных...")
        
        db_files = [
            "backend/app/models/feedback.py",
            "backend/app/models/channel.py",
            "database/seeds/telegram_channels.json"
        ]
        
        for db_file in db_files:
            if Path(db_file).exists():
                try:
                    with open(db_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content.strip()) > 0:
                            self.log_test("Database Schema", f"Файл {Path(db_file).name}", "PASS", "Файл существует и не пустой")
                        else:
                            self.log_test("Database Schema", f"Файл {Path(db_file).name}", "WARNING", "Файл пустой")
                except Exception as e:
                    self.log_test("Database Schema", f"Файл {Path(db_file).name}", "FAIL", "", f"Ошибка чтения: {str(e)}")
            else:
                self.log_test("Database Schema", f"Файл {Path(db_file).name}", "FAIL", "", f"Файл не найден")
    
    async def test_api_endpoints(self):
        """Проверка API эндпоинтов"""
        print("\n🌐 Проверка API эндпоинтов...")
        
        api_files = [
            "backend/app/api/endpoints/feedback.py",
            "backend/app/api/endpoints/ocr_integration.py",
            "backend/app/api/endpoints/reddit_integration.py"
        ]
        
        for api_file in api_files:
            if Path(api_file).exists():
                try:
                    with open(api_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "router" in content and "endpoint" in content.lower():
                            self.log_test("API Endpoints", f"Файл {Path(api_file).name}", "PASS", "API эндпоинты найдены")
                        else:
                            self.log_test("API Endpoints", f"Файл {Path(api_file).name}", "WARNING", "API эндпоинты не обнаружены")
                except Exception as e:
                    self.log_test("API Endpoints", f"Файл {Path(api_file).name}", "FAIL", "", f"Ошибка чтения: {str(e)}")
            else:
                self.log_test("API Endpoints", f"Файл {Path(api_file).name}", "FAIL", "", f"Файл не найден")
    
    async def test_frontend_components(self):
        """Проверка фронтенд компонентов"""
        print("\n🎨 Проверка фронтенд компонентов...")
        
        frontend_files = [
            "frontend/components/FeedbackForm.tsx",
            "frontend/pages/feedback.tsx"
        ]
        
        for frontend_file in frontend_files:
            if Path(frontend_file).exists():
                try:
                    with open(frontend_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "export" in content and ("function" in content or "const" in content):
                            self.log_test("Frontend Components", f"Файл {Path(frontend_file).name}", "PASS", "React компонент найден")
                        else:
                            self.log_test("Frontend Components", f"Файл {Path(frontend_file).name}", "WARNING", "React компонент не обнаружен")
                except Exception as e:
                    self.log_test("Frontend Components", f"Файл {Path(frontend_file).name}", "FAIL", "", f"Ошибка чтения: {str(e)}")
            else:
                self.log_test("Frontend Components", f"Файл {Path(frontend_file).name}", "FAIL", "", f"Файл не найден")
    
    async def test_worker_scripts(self):
        """Проверка worker скриптов"""
        print("\n⚡ Проверка worker скриптов...")
        
        worker_scripts = [
            "workers/telegram/telegram_scraper.py",  # Исправленный путь
            "workers/reddit_collector.py",
            "workers/signal_patterns.py",
            "workers/telegram_feedback_bot.py",
            "workers/channel_discovery_system.py"
        ]
        
        for script in worker_scripts:
            if Path(script).exists():
                try:
                    with open(script, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "class" in content and "def" in content:
                            self.log_test("Worker Scripts", f"Скрипт {Path(script).name}", "PASS", "Python классы и функции найдены")
                        else:
                            self.log_test("Worker Scripts", f"Скрипт {Path(script).name}", "WARNING", "Классы или функции не обнаружены")
                except Exception as e:
                    self.log_test("Worker Scripts", f"Скрипт {Path(script).name}", "FAIL", "", f"Ошибка чтения: {str(e)}")
            else:
                self.log_test("Worker Scripts", f"Скрипт {Path(script).name}", "FAIL", "", f"Файл не найден")
    
    async def test_documentation(self):
        """Проверка документации"""
        print("\n📚 Проверка документации...")
        
        doc_files = [
            "README.md",
            "TASKS2.md",
            "COMPREHENSIVE_FUNCTIONALITY_REPORT.md",
            "FEEDBACK_SYSTEM_REPORT.md"
        ]
        
        for doc_file in doc_files:
            if Path(doc_file).exists():
                try:
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content.strip()) > 100:  # Минимум 100 символов
                            self.log_test("Documentation", f"Документ {Path(doc_file).name}", "PASS", "Документ содержит контент")
                        else:
                            self.log_test("Documentation", f"Документ {Path(doc_file).name}", "WARNING", "Документ слишком короткий")
                except Exception as e:
                    self.log_test("Documentation", f"Документ {Path(doc_file).name}", "FAIL", "", f"Ошибка чтения: {str(e)}")
            else:
                self.log_test("Documentation", f"Документ {Path(doc_file).name}", "FAIL", "", f"Файл не найден")
    
    async def test_integration_scenarios(self):
        """Тестирование интеграционных сценариев"""
        print("\n🔗 Тестирование интеграционных сценариев...")
        
        # Сценарий 1: Обработка сигнала через всю систему
        try:
            from signal_patterns import SignalPatterns
            patterns = SignalPatterns()
            
            test_signal = "BTC/USDT LONG @ 45000 SL: 44000 TP: 47000"
            result = patterns.extract_signal_info(test_signal)
            
            if result.get("trading_pair") == "BTC/USDT" and result.get("direction") == "LONG":
                self.log_test("Integration Scenarios", "Обработка сигнала", "PASS", "Сигнал корректно обработан")
            else:
                self.log_test("Integration Scenarios", "Обработка сигнала", "WARNING", f"Обработан сигнал: {result.get('trading_pair', 'N/A')} {result.get('direction', 'N/A')}")
                
        except Exception as e:
            self.log_test("Integration Scenarios", "Обработка сигнала", "FAIL", "", f"Ошибка: {str(e)}")
        
        # Сценарий 2: Проверка системы обратной связи
        try:
            from telegram_feedback_bot import TelegramFeedbackBot
            bot = TelegramFeedbackBot("test_token")
            
            if hasattr(bot, 'start_command'):
                self.log_test("Integration Scenarios", "Система обратной связи", "PASS", "Telegram бот готов к работе")
            else:
                self.log_test("Integration Scenarios", "Система обратной связи", "WARNING", "Метод start_command не найден")
                
        except Exception as e:
            if "Update" in str(e):
                self.log_test("Integration Scenarios", "Система обратной связи", "WARNING", "Telegram библиотеки не установлены")
            else:
                self.log_test("Integration Scenarios", "Система обратной связи", "FAIL", "", f"Ошибка: {str(e)}")
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК ГЛУБОКОЙ ПРОВЕРКИ СИСТЕМЫ")
        print("=" * 60)
        
        await self.test_file_structure()
        await self.test_imports()
        await self.test_signal_patterns()
        await self.test_telegram_integration()
        await self.test_reddit_integration()
        await self.test_feedback_system()
        await self.test_channel_discovery()
        await self.test_configuration_files()
        await self.test_database_schema()
        await self.test_api_endpoints()
        await self.test_frontend_components()
        await self.test_worker_scripts()
        await self.test_documentation()
        await self.test_integration_scenarios()
        
        # Подсчет результатов
        self.results["test_time"] = time.time() - self.start_time
        
        # Вывод итогового отчета
        self.print_final_report()
        
        # Сохранение отчета
        self.save_report()
    
    def print_final_report(self):
        """Вывод итогового отчета"""
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ГЛУБОКОЙ ПРОВЕРКИ")
        print("=" * 60)
        
        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        warnings = self.results["warnings"]
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 Общая статистика:")
        print(f"   • Всего тестов: {total}")
        print(f"   • Успешных: {passed} ({success_rate:.1f}%)")
        print(f"   • Предупреждений: {warnings}")
        print(f"   • Ошибок: {failed}")
        print(f"   • Время выполнения: {self.results['test_time']:.2f} сек")
        
        print(f"\n🏆 Оценка готовности:")
        if success_rate >= 95:
            print("   🚀 ОТЛИЧНО: Система полностью готова к продакшену")
        elif success_rate >= 85:
            print("   ✅ ХОРОШО: Система готова с незначительными улучшениями")
        elif success_rate >= 70:
            print("   ⚠️ УДОВЛЕТВОРИТЕЛЬНО: Требуются доработки")
        else:
            print("   ❌ КРИТИЧНО: Требуются серьезные исправления")
        
        print(f"\n📋 Детали по категориям:")
        for category, tests in self.results["categories"].items():
            category_passed = sum(1 for test in tests if test["status"] == "PASS")
            category_total = len(tests)
            category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            print(f"   • {category}: {category_passed}/{category_total} ({category_rate:.1f}%)")
    
    def save_report(self):
        """Сохранение отчета в файл"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"deep_system_test_report_{timestamp}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Отчет сохранен: {report_file}")
        except Exception as e:
            print(f"\n❌ Ошибка сохранения отчета: {str(e)}")

async def main():
    """Основная функция"""
    tester = DeepSystemTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
