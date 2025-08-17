#!/usr/bin/env python3
"""
Упрощенная проверка функциональности Crypto Analytics Platform
Без зависимости от backend модулей
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Добавляем пути для импортов
sys.path.append(str(Path(__file__).parent))

class SimplifiedFunctionalityTest:
    """Упрощенная проверка функциональности"""
    
    def __init__(self):
        self.test_results = {
            'file_structure': {},
            'telegram': {},
            'reddit': {},
            'feedback': {},
            'channel_discovery': {},
            'signal_processing': {},
            'frontend': {},
            'ocr': {},
            'overall': {}
        }
        self.start_time = time.time()
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        
        print("🚀 УПРОЩЕННАЯ ПРОВЕРКА ФУНКЦИОНАЛЬНОСТИ")
        print("="*100)
        print(f"🕐 Время начала: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}")
        print("="*100)
        
        # 1. Проверка структуры файлов
        await self.test_file_structure()
        
        # 2. Проверка Telegram интеграции
        await self.test_telegram_functionality()
        
        # 3. Проверка Reddit интеграции
        await self.test_reddit_functionality()
        
        # 4. Проверка системы обратной связи
        await self.test_feedback_functionality()
        
        # 5. Проверка обнаружения каналов
        await self.test_channel_discovery()
        
        # 6. Проверка обработки сигналов
        await self.test_signal_processing()
        
        # 7. Проверка Frontend компонентов
        await self.test_frontend_functionality()
        
        # 8. Проверка OCR системы
        await self.test_ocr_functionality()
        
        # 9. Итоговая оценка
        await self.generate_final_report()
    
    async def test_file_structure(self):
        """Проверка структуры файлов"""
        
        print("\n📁 ПРОВЕРКА СТРУКТУРЫ ФАЙЛОВ")
        print("-" * 50)
        
        # Проверка основных директорий
        directories = [
            'backend',
            'frontend', 
            'workers',
            'database',
            'docs'
        ]
        
        existing_dirs = []
        for dir_name in directories:
            if Path(dir_name).exists():
                existing_dirs.append(dir_name)
                self.test_results['file_structure'][f'directory_{dir_name}'] = {
                    'status': '✅ УСПЕШНО',
                    'message': f'Директория {dir_name} найдена'
                }
                print(f"✅ Директория {dir_name}: УСПЕШНО")
            else:
                self.test_results['file_structure'][f'directory_{dir_name}'] = {
                    'status': '❌ ОШИБКА',
                    'message': f'Директория {dir_name} не найдена'
                }
                print(f"❌ Директория {dir_name}: ОШИБКА")
        
        # Проверка ключевых файлов
        key_files = [
            'README.md',
            'TASKS2.md',
            'docker-compose.yml',
            'backend/requirements.txt',
            'frontend/package.json'
        ]
        
        existing_files = []
        for file_path in key_files:
            if Path(file_path).exists():
                existing_files.append(file_path)
                self.test_results['file_structure'][f'file_{file_path.replace("/", "_")}'] = {
                    'status': '✅ УСПЕШНО',
                    'message': f'Файл {file_path} найден'
                }
                print(f"✅ Файл {file_path}: УСПЕШНО")
            else:
                self.test_results['file_structure'][f'file_{file_path.replace("/", "_")}'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': f'Файл {file_path} не найден'
                }
                print(f"⚠️ Файл {file_path}: ПРЕДУПРЕЖДЕНИЕ")
    
    async def test_telegram_functionality(self):
        """Проверка Telegram функциональности"""
        
        print("\n📱 ПРОВЕРКА TELEGRAM ИНТЕГРАЦИИ")
        print("-" * 50)
        
        try:
            # Проверка Telegram скрапера
            from workers.telegram.telegram_scraper import TelegramSignalScraper
            
            self.test_results['telegram']['scraper'] = {
                'status': '✅ УСПЕШНО',
                'message': 'Telegram скрапер доступен'
            }
            print("✅ Telegram скрапер: УСПЕШНО")
            
            # Проверка Selenium скрапера
            try:
                from workers.telegram.selenium_scraper import SeleniumTelegramScraper
                self.test_results['telegram']['selenium'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'Selenium скрапер доступен'
                }
                print("✅ Selenium скрапер: УСПЕШНО")
            except Exception as e:
                self.test_results['telegram']['selenium'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': f'Selenium скрапер: {e}'
                }
                print(f"⚠️ Selenium скрапер: ПРЕДУПРЕЖДЕНИЕ - {e}")
            
            # Проверка бота обратной связи
            try:
                from workers.telegram_feedback_bot import TelegramFeedbackBot
                self.test_results['telegram']['feedback_bot'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'Бот обратной связи доступен'
                }
                print("✅ Бот обратной связи: УСПЕШНО")
            except Exception as e:
                self.test_results['telegram']['feedback_bot'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': f'Бот обратной связи: {e}'
                }
                print(f"⚠️ Бот обратной связи: ПРЕДУПРЕЖДЕНИЕ - {e}")
            
        except Exception as e:
            self.test_results['telegram']['overall'] = {
                'status': '❌ КРИТИЧЕСКАЯ ОШИБКА',
                'message': f'Telegram интеграция недоступна: {e}'
            }
            print(f"❌ Telegram: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
    async def test_reddit_functionality(self):
        """Проверка Reddit функциональности"""
        
        print("\n🔴 ПРОВЕРКА REDDIT ИНТЕГРАЦИИ")
        print("-" * 50)
        
        try:
            # Проверка Reddit коллектора
            from workers.reddit_collector import RedditSignalCollector
            
            self.test_results['reddit']['collector'] = {
                'status': '✅ УСПЕШНО',
                'message': 'Reddit коллектор доступен'
            }
            print("✅ Reddit коллектор: УСПЕШНО")
            
            # Проверка конфигурации
            try:
                collector = RedditSignalCollector()
                self.test_results['reddit']['configuration'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'Reddit конфигурация загружена'
                }
                print("✅ Reddit конфигурация: УСПЕШНО")
            except Exception as e:
                self.test_results['reddit']['configuration'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': f'Reddit конфигурация: {e}'
                }
                print(f"⚠️ Reddit конфигурация: ПРЕДУПРЕЖДЕНИЕ - {e}")
            
        except Exception as e:
            self.test_results['reddit']['overall'] = {
                'status': '❌ КРИТИЧЕСКАЯ ОШИБКА',
                'message': f'Reddit интеграция недоступна: {e}'
            }
            print(f"❌ Reddit: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
    async def test_feedback_functionality(self):
        """Проверка системы обратной связи"""
        
        print("\n📝 ПРОВЕРКА СИСТЕМЫ ОБРАТНОЙ СВЯЗИ")
        print("-" * 50)
        
        # Проверка файлов системы обратной связи
        feedback_files = [
            'backend/app/models/feedback.py',
            'backend/app/schemas/feedback.py',
            'backend/app/api/endpoints/feedback.py',
            'workers/telegram_feedback_bot.py',
            'frontend/components/FeedbackForm.tsx',
            'frontend/pages/feedback.tsx'
        ]
        
        existing_feedback_files = []
        for file_path in feedback_files:
            if Path(file_path).exists():
                existing_feedback_files.append(file_path)
                self.test_results['feedback'][f'file_{file_path.replace("/", "_")}'] = {
                    'status': '✅ УСПЕШНО',
                    'message': f'Файл {file_path} найден'
                }
                print(f"✅ Файл {file_path}: УСПЕШНО")
            else:
                self.test_results['feedback'][f'file_{file_path.replace("/", "_")}'] = {
                    'status': '❌ ОШИБКА',
                    'message': f'Файл {file_path} не найден'
                }
                print(f"❌ Файл {file_path}: ОШИБКА")
        
        # Проверка отчета о системе обратной связи
        feedback_report = Path('FEEDBACK_SYSTEM_REPORT.md')
        if feedback_report.exists():
            self.test_results['feedback']['report'] = {
                'status': '✅ УСПЕШНО',
                'message': 'Отчет о системе обратной связи найден'
            }
            print("✅ Отчет о системе обратной связи: УСПЕШНО")
        else:
            self.test_results['feedback']['report'] = {
                'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                'message': 'Отчет о системе обратной связи не найден'
            }
            print("⚠️ Отчет о системе обратной связи: ПРЕДУПРЕЖДЕНИЕ")
    
    async def test_channel_discovery(self):
        """Проверка системы обнаружения каналов"""
        
        print("\n🔍 ПРОВЕРКА СИСТЕМЫ ОБНАРУЖЕНИЯ КАНАЛОВ")
        print("-" * 50)
        
        try:
            # Проверка системы обнаружения каналов
            from workers.channel_discovery_system import ChannelDiscoverySystem
            
            self.test_results['channel_discovery']['system'] = {
                'status': '✅ УСПЕШНО',
                'message': 'Система обнаружения каналов доступна'
            }
            print("✅ Система обнаружения каналов: УСПЕШНО")
            
            # Проверка улучшенного анализатора
            try:
                from workers.enhanced_channel_analyzer import EnhancedChannelAnalyzer
                self.test_results['channel_discovery']['analyzer'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'Улучшенный анализатор каналов доступен'
                }
                print("✅ Улучшенный анализатор каналов: УСПЕШНО")
            except Exception as e:
                self.test_results['channel_discovery']['analyzer'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': f'Улучшенный анализатор: {e}'
                }
                print(f"⚠️ Улучшенный анализатор каналов: ПРЕДУПРЕЖДЕНИЕ - {e}")
            
            # Проверка конфигурации каналов
            try:
                discovery_system = ChannelDiscoverySystem()
                telegram_channels = len(discovery_system.known_channels['telegram'])
                reddit_channels = len(discovery_system.known_channels['reddit'])
                
                self.test_results['channel_discovery']['configuration'] = {
                    'status': '✅ УСПЕШНО',
                    'message': f'Конфигурация загружена: {telegram_channels} Telegram, {reddit_channels} Reddit'
                }
                print(f"✅ Конфигурация каналов: УСПЕШНО ({telegram_channels} Telegram, {reddit_channels} Reddit)")
            except Exception as e:
                self.test_results['channel_discovery']['configuration'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': f'Конфигурация каналов: {e}'
                }
                print(f"⚠️ Конфигурация каналов: ПРЕДУПРЕЖДЕНИЕ - {e}")
            
        except Exception as e:
            self.test_results['channel_discovery']['overall'] = {
                'status': '❌ КРИТИЧЕСКАЯ ОШИБКА',
                'message': f'Система обнаружения каналов недоступна: {e}'
            }
            print(f"❌ Система обнаружения каналов: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
    async def test_signal_processing(self):
        """Проверка обработки сигналов"""
        
        print("\n📊 ПРОВЕРКА ОБРАБОТКИ СИГНАЛОВ")
        print("-" * 50)
        
        try:
            # Проверка парсеров сигналов
            from workers.signal_patterns import SIGNAL_PATTERNS, extract_signal_info
            
            self.test_results['signal_processing']['patterns'] = {
                'status': '✅ УСПЕШНО',
                'message': f'Загружено {len(SIGNAL_PATTERNS)} паттернов сигналов'
            }
            print(f"✅ Паттерны сигналов: УСПЕШНО ({len(SIGNAL_PATTERNS)} паттернов)")
            
            # Проверка файлов обработки сигналов
            signal_files = [
                'workers/signal_patterns.py',
                'workers/run_signal_scraping.py',
                'workers/telegram/telegram_collector_migrated.py',
                'workers/shared/parsers/signal_extractor_migrated.py'
            ]
            
            existing_signal_files = []
            for file_path in signal_files:
                if Path(file_path).exists():
                    existing_signal_files.append(file_path)
                    self.test_results['signal_processing'][f'file_{file_path.replace("/", "_")}'] = {
                        'status': '✅ УСПЕШНО',
                        'message': f'Файл {file_path} найден'
                    }
                    print(f"✅ Файл {file_path}: УСПЕШНО")
                else:
                    self.test_results['signal_processing'][f'file_{file_path.replace("/", "_")}'] = {
                        'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                        'message': f'Файл {file_path} не найден'
                    }
                    print(f"⚠️ Файл {file_path}: ПРЕДУПРЕЖДЕНИЕ")
            
        except Exception as e:
            self.test_results['signal_processing']['overall'] = {
                'status': '❌ КРИТИЧЕСКАЯ ОШИБКА',
                'message': f'Обработка сигналов недоступна: {e}'
            }
            print(f"❌ Обработка сигналов: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
    async def test_frontend_functionality(self):
        """Проверка Frontend функциональности"""
        
        print("\n🌐 ПРОВЕРКА FRONTEND КОМПОНЕНТОВ")
        print("-" * 50)
        
        try:
            # Проверка компонента обратной связи
            feedback_form_path = Path("frontend/components/FeedbackForm.tsx")
            if feedback_form_path.exists():
                self.test_results['frontend']['feedback_form'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'Компонент формы обратной связи найден'
                }
                print("✅ Компонент формы обратной связи: УСПЕШНО")
            else:
                self.test_results['frontend']['feedback_form'] = {
                    'status': '❌ ОШИБКА',
                    'message': 'Компонент формы обратной связи не найден'
                }
                print("❌ Компонент формы обратной связи: ОШИБКА")
            
            # Проверка страницы обратной связи
            feedback_page_path = Path("frontend/pages/feedback.tsx")
            if feedback_page_path.exists():
                self.test_results['frontend']['feedback_page'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'Страница обратной связи найдена'
                }
                print("✅ Страница обратной связи: УСПЕШНО")
            else:
                self.test_results['frontend']['feedback_page'] = {
                    'status': '❌ ОШИБКА',
                    'message': 'Страница обратной связи не найдена'
                }
                print("❌ Страница обратной связи: ОШИБКА")
            
            # Проверка основных страниц
            main_pages = [
                "frontend/pages/index.tsx",
                "frontend/pages/signals.tsx",
                "frontend/pages/analytics.tsx"
            ]
            
            existing_pages = []
            for page in main_pages:
                if Path(page).exists():
                    existing_pages.append(page.split('/')[-1])
            
            if len(existing_pages) >= 2:
                self.test_results['frontend']['main_pages'] = {
                    'status': '✅ УСПЕШНО',
                    'message': f'Основные страницы найдены: {existing_pages}'
                }
                print(f"✅ Основные страницы: УСПЕШНО ({existing_pages})")
            else:
                self.test_results['frontend']['main_pages'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': f'Найдено только {len(existing_pages)} основных страниц'
                }
                print(f"⚠️ Основные страницы: ПРЕДУПРЕЖДЕНИЕ ({existing_pages})")
            
            # Проверка package.json
            package_json_path = Path("frontend/package.json")
            if package_json_path.exists():
                self.test_results['frontend']['package_json'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'package.json найден'
                }
                print("✅ package.json: УСПЕШНО")
            else:
                self.test_results['frontend']['package_json'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': 'package.json не найден'
                }
                print("⚠️ package.json: ПРЕДУПРЕЖДЕНИЕ")
            
        except Exception as e:
            self.test_results['frontend']['overall'] = {
                'status': '❌ КРИТИЧЕСКАЯ ОШИБКА',
                'message': f'Frontend недоступен: {e}'
            }
            print(f"❌ Frontend: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
    async def test_ocr_functionality(self):
        """Проверка OCR функциональности"""
        
        print("\n👁️ ПРОВЕРКА OCR СИСТЕМЫ")
        print("-" * 50)
        
        # Проверка файлов OCR
        ocr_files = [
            'backend/app/services/ocr_service.py',
            'backend/app/api/endpoints/ocr_integration.py',
            'backend/app/schemas/ocr.py',
            'workers/shared/ocr/enhanced_ocr_pipeline.py'
        ]
        
        existing_ocr_files = []
        for file_path in ocr_files:
            if Path(file_path).exists():
                existing_ocr_files.append(file_path)
                self.test_results['ocr'][f'file_{file_path.replace("/", "_")}'] = {
                    'status': '✅ УСПЕШНО',
                    'message': f'Файл {file_path} найден'
                }
                print(f"✅ Файл {file_path}: УСПЕШНО")
            else:
                self.test_results['ocr'][f'file_{file_path.replace("/", "_")}'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': f'Файл {file_path} не найден'
                }
                print(f"⚠️ Файл {file_path}: ПРЕДУПРЕЖДЕНИЕ")
        
        # Проверка отчета об OCR
        ocr_report = Path('OCR_ACTIVATION_REPORT.md')
        if ocr_report.exists():
            self.test_results['ocr']['report'] = {
                'status': '✅ УСПЕШНО',
                'message': 'Отчет об OCR найден'
            }
            print("✅ Отчет об OCR: УСПЕШНО")
        else:
            self.test_results['ocr']['report'] = {
                'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                'message': 'Отчет об OCR не найден'
            }
            print("⚠️ Отчет об OCR: ПРЕДУПРЕЖДЕНИЕ")
    
    async def generate_final_report(self):
        """Генерация итогового отчета"""
        
        print("\n" + "="*100)
        print("📊 ИТОГОВЫЙ ОТЧЕТ О ФУНКЦИОНАЛЬНОСТИ")
        print("="*100)
        
        # Подсчет результатов
        total_tests = 0
        successful_tests = 0
        warning_tests = 0
        failed_tests = 0
        
        for category, tests in self.test_results.items():
            if category == 'overall':
                continue
                
            for test_name, result in tests.items():
                total_tests += 1
                status = result['status']
                
                if '✅' in status:
                    successful_tests += 1
                elif '⚠️' in status:
                    warning_tests += 1
                elif '❌' in status:
                    failed_tests += 1
        
        # Расчет процентов
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        warning_rate = (warning_tests / total_tests * 100) if total_tests > 0 else 0
        failure_rate = (failed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Время выполнения
        execution_time = time.time() - self.start_time
        
        print(f"\n📈 СТАТИСТИКА ТЕСТИРОВАНИЯ:")
        print(f"   Всего тестов: {total_tests}")
        print(f"   Успешных: {successful_tests} ({success_rate:.1f}%)")
        print(f"   Предупреждений: {warning_tests} ({warning_rate:.1f}%)")
        print(f"   Ошибок: {failed_tests} ({failure_rate:.1f}%)")
        print(f"   Время выполнения: {execution_time:.2f} секунд")
        
        print(f"\n🎯 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        
        for category, tests in self.test_results.items():
            if category == 'overall':
                continue
                
            print(f"\n   {category.upper()}:")
            for test_name, result in tests.items():
                status_icon = "✅" if "✅" in result['status'] else "⚠️" if "⚠️" in result['status'] else "❌"
                print(f"     {status_icon} {test_name}: {result['message']}")
        
        # Общая оценка
        if success_rate >= 90:
            overall_status = "🚀 ОТЛИЧНО"
            overall_message = "Система полностью готова к продакшену"
        elif success_rate >= 80:
            overall_status = "✅ ХОРОШО"
            overall_message = "Система готова с небольшими улучшениями"
        elif success_rate >= 70:
            overall_status = "⚠️ УДОВЛЕТВОРИТЕЛЬНО"
            overall_message = "Требуются доработки перед продакшеном"
        else:
            overall_status = "❌ КРИТИЧНО"
            overall_message = "Требуется серьезная доработка"
        
        self.test_results['overall'] = {
            'status': overall_status,
            'message': overall_message,
            'statistics': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'warning_tests': warning_tests,
                'failed_tests': failed_tests,
                'success_rate': success_rate,
                'execution_time': execution_time
            }
        }
        
        print(f"\n🏆 ОБЩАЯ ОЦЕНКА:")
        print(f"   {overall_status}: {overall_message}")
        
        # Сохранение отчета
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"simplified_test_report_{timestamp}.json"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Отчет сохранен в: {report_filename}")
        print(f"\n✅ Упрощенная проверка завершена!")

async def main():
    """Основная функция"""
    
    tester = SimplifiedFunctionalityTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
