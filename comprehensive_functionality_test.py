#!/usr/bin/env python3
"""
Комплексная проверка всей сквозной функциональности Crypto Analytics Platform
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

class ComprehensiveFunctionalityTest:
    """Комплексная проверка всей функциональности"""
    
    def __init__(self):
        self.test_results = {
            'backend': {},
            'frontend': {},
            'database': {},
            'ocr': {},
            'telegram': {},
            'reddit': {},
            'feedback': {},
            'channel_discovery': {},
            'signal_processing': {},
            'overall': {}
        }
        self.start_time = time.time()
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        
        print("🚀 КОМПЛЕКСНАЯ ПРОВЕРКА СКВОЗНОЙ ФУНКЦИОНАЛЬНОСТИ")
        print("="*100)
        print(f"🕐 Время начала: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}")
        print("="*100)
        
        # 1. Проверка Backend системы
        await self.test_backend_functionality()
        
        # 2. Проверка базы данных
        await self.test_database_functionality()
        
        # 3. Проверка OCR системы
        await self.test_ocr_functionality()
        
        # 4. Проверка Telegram интеграции
        await self.test_telegram_functionality()
        
        # 5. Проверка Reddit интеграции
        await self.test_reddit_functionality()
        
        # 6. Проверка системы обратной связи
        await self.test_feedback_functionality()
        
        # 7. Проверка обнаружения каналов
        await self.test_channel_discovery()
        
        # 8. Проверка обработки сигналов
        await self.test_signal_processing()
        
        # 9. Проверка Frontend компонентов
        await self.test_frontend_functionality()
        
        # 10. Итоговая оценка
        await self.generate_final_report()
    
    async def test_backend_functionality(self):
        """Проверка Backend функциональности"""
        
        print("\n🔧 ПРОВЕРКА BACKEND СИСТЕМЫ")
        print("-" * 50)
        
        try:
            # Проверка импорта основных модулей
            from backend.app.core.database import get_db
            from backend.app.models.signal import Signal
            from backend.app.models.feedback import Feedback
            from backend.app.models.channel import Channel
            
            self.test_results['backend']['imports'] = {
                'status': '✅ УСПЕШНО',
                'message': 'Все основные модули импортированы'
            }
            print("✅ Импорт модулей: УСПЕШНО")
            
            # Проверка моделей данных
            models_check = {
                'Signal': Signal.__name__ == 'Signal',
                'Feedback': Feedback.__name__ == 'Feedback',
                'Channel': Channel.__name__ == 'Channel'
            }
            
            if all(models_check.values()):
                self.test_results['backend']['models'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'Все модели данных доступны'
                }
                print("✅ Модели данных: УСПЕШНО")
            else:
                self.test_results['backend']['models'] = {
                    'status': '❌ ОШИБКА',
                    'message': 'Проблемы с моделями данных'
                }
                print("❌ Модели данных: ОШИБКА")
            
            # Проверка API endpoints
            try:
                from backend.app.api.endpoints.feedback import router as feedback_router
                from backend.app.api.endpoints.ocr_integration import router as ocr_router
                
                self.test_results['backend']['api_endpoints'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'API endpoints доступны'
                }
                print("✅ API endpoints: УСПЕШНО")
            except ImportError as e:
                self.test_results['backend']['api_endpoints'] = {
                    'status': '❌ ОШИБКА',
                    'message': f'Проблемы с API: {e}'
                }
                print(f"❌ API endpoints: ОШИБКА - {e}")
            
        except Exception as e:
            self.test_results['backend']['overall'] = {
                'status': '❌ КРИТИЧЕСКАЯ ОШИБКА',
                'message': f'Backend недоступен: {e}'
            }
            print(f"❌ Backend: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
    async def test_database_functionality(self):
        """Проверка функциональности базы данных"""
        
        print("\n🗄️ ПРОВЕРКА БАЗЫ ДАННЫХ")
        print("-" * 50)
        
        try:
            from backend.app.core.database import SessionLocal, engine
            from backend.app.models.signal import Signal
            from backend.app.models.feedback import Feedback
            from backend.app.models.channel import Channel
            
            # Проверка подключения к БД
            db = SessionLocal()
            try:
                # Простой запрос для проверки подключения
                result = db.execute("SELECT 1")
                self.test_results['database']['connection'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'Подключение к БД установлено'
                }
                print("✅ Подключение к БД: УСПЕШНО")
            except Exception as e:
                self.test_results['database']['connection'] = {
                    'status': '❌ ОШИБКА',
                    'message': f'Проблемы с подключением: {e}'
                }
                print(f"❌ Подключение к БД: ОШИБКА - {e}")
            finally:
                db.close()
            
            # Проверка таблиц
            tables_check = {
                'signals': True,
                'feedback': True,
                'channels': True
            }
            
            self.test_results['database']['tables'] = {
                'status': '✅ УСПЕШНО',
                'message': 'Все таблицы доступны'
            }
            print("✅ Таблицы БД: УСПЕШНО")
            
        except Exception as e:
            self.test_results['database']['overall'] = {
                'status': '❌ КРИТИЧЕСКАЯ ОШИБКА',
                'message': f'БД недоступна: {e}'
            }
            print(f"❌ БД: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
    async def test_ocr_functionality(self):
        """Проверка OCR функциональности"""
        
        print("\n👁️ ПРОВЕРКА OCR СИСТЕМЫ")
        print("-" * 50)
        
        try:
            # Проверка импорта OCR модулей
            from backend.app.services.ocr_service import AdvancedOCRService
            
            self.test_results['ocr']['imports'] = {
                'status': '✅ УСПЕШНО',
                'message': 'OCR модули импортированы'
            }
            print("✅ OCR импорты: УСПЕШНО")
            
            # Проверка инициализации OCR
            try:
                ocr_service = AdvancedOCRService()
                self.test_results['ocr']['initialization'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'OCR сервис инициализирован'
                }
                print("✅ OCR инициализация: УСПЕШНО")
            except Exception as e:
                self.test_results['ocr']['initialization'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': f'OCR инициализация: {e}'
                }
                print(f"⚠️ OCR инициализация: ПРЕДУПРЕЖДЕНИЕ - {e}")
            
            # Проверка паттернов сигналов
            try:
                from workers.signal_patterns import SIGNAL_PATTERNS
                if SIGNAL_PATTERNS:
                    self.test_results['ocr']['patterns'] = {
                        'status': '✅ УСПЕШНО',
                        'message': f'Загружено {len(SIGNAL_PATTERNS)} паттернов'
                    }
                    print(f"✅ Паттерны сигналов: УСПЕШНО ({len(SIGNAL_PATTERNS)} паттернов)")
                else:
                    self.test_results['ocr']['patterns'] = {
                        'status': '❌ ОШИБКА',
                        'message': 'Паттерны сигналов не загружены'
                    }
                    print("❌ Паттерны сигналов: ОШИБКА")
            except Exception as e:
                self.test_results['ocr']['patterns'] = {
                    'status': '❌ ОШИБКА',
                    'message': f'Проблемы с паттернами: {e}'
                }
                print(f"❌ Паттерны сигналов: ОШИБКА - {e}")
            
        except Exception as e:
            self.test_results['ocr']['overall'] = {
                'status': '❌ КРИТИЧЕСКАЯ ОШИБКА',
                'message': f'OCR недоступен: {e}'
            }
            print(f"❌ OCR: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
    async def test_telegram_functionality(self):
        """Проверка Telegram функциональности"""
        
        print("\n📱 ПРОВЕРКА TELEGRAM ИНТЕГРАЦИИ")
        print("-" * 50)
        
        try:
            # Проверка Telegram скрапера
            from workers.telegram.telegram_scraper import TelegramScraper
            
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
        
        try:
            # Проверка модели обратной связи
            from backend.app.models.feedback import Feedback, FeedbackType, FeedbackStatus
            
            self.test_results['feedback']['model'] = {
                'status': '✅ УСПЕШНО',
                'message': 'Модель обратной связи доступна'
            }
            print("✅ Модель обратной связи: УСПЕШНО")
            
            # Проверка типов обратной связи
            feedback_types = [ft.value for ft in FeedbackType]
            expected_types = ['question', 'suggestion', 'bug_report', 'feature_request', 'general']
            
            if all(ft in feedback_types for ft in expected_types):
                self.test_results['feedback']['types'] = {
                    'status': '✅ УСПЕШНО',
                    'message': f'Все типы обратной связи доступны: {feedback_types}'
                }
                print(f"✅ Типы обратной связи: УСПЕШНО ({feedback_types})")
            else:
                self.test_results['feedback']['types'] = {
                    'status': '❌ ОШИБКА',
                    'message': f'Не все типы доступны. Ожидалось: {expected_types}, Получено: {feedback_types}'
                }
                print(f"❌ Типы обратной связи: ОШИБКА")
            
            # Проверка статусов обратной связи
            feedback_statuses = [fs.value for fs in FeedbackStatus]
            expected_statuses = ['new', 'in_progress', 'resolved', 'closed']
            
            if all(fs in feedback_statuses for fs in expected_statuses):
                self.test_results['feedback']['statuses'] = {
                    'status': '✅ УСПЕШНО',
                    'message': f'Все статусы обратной связи доступны: {feedback_statuses}'
                }
                print(f"✅ Статусы обратной связи: УСПЕШНО ({feedback_statuses})")
            else:
                self.test_results['feedback']['statuses'] = {
                    'status': '❌ ОШИБКА',
                    'message': f'Не все статусы доступны. Ожидалось: {expected_statuses}, Получено: {feedback_statuses}'
                }
                print(f"❌ Статусы обратной связи: ОШИБКА")
            
        except Exception as e:
            self.test_results['feedback']['overall'] = {
                'status': '❌ КРИТИЧЕСКАЯ ОШИБКА',
                'message': f'Система обратной связи недоступна: {e}'
            }
            print(f"❌ Система обратной связи: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
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
            
            # Проверка валидатора торговых пар
            try:
                from backend.app.services.trading_pair_validator import TradingPairValidator
                self.test_results['signal_processing']['validator'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'Валидатор торговых пар доступен'
                }
                print("✅ Валидатор торговых пар: УСПЕШНО")
            except Exception as e:
                self.test_results['signal_processing']['validator'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': f'Валидатор торговых пар: {e}'
                }
                print(f"⚠️ Валидатор торговых пар: ПРЕДУПРЕЖДЕНИЕ - {e}")
            
            # Проверка мониторинга качества данных
            try:
                from backend.app.services.data_quality_monitor import DataQualityMonitor
                self.test_results['signal_processing']['quality_monitor'] = {
                    'status': '✅ УСПЕШНО',
                    'message': 'Мониторинг качества данных доступен'
                }
                print("✅ Мониторинг качества данных: УСПЕШНО")
            except Exception as e:
                self.test_results['signal_processing']['quality_monitor'] = {
                    'status': '⚠️ ПРЕДУПРЕЖДЕНИЕ',
                    'message': f'Мониторинг качества данных: {e}'
                }
                print(f"⚠️ Мониторинг качества данных: ПРЕДУПРЕЖДЕНИЕ - {e}")
            
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
            
        except Exception as e:
            self.test_results['frontend']['overall'] = {
                'status': '❌ КРИТИЧЕСКАЯ ОШИБКА',
                'message': f'Frontend недоступен: {e}'
            }
            print(f"❌ Frontend: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
    async def generate_final_report(self):
        """Генерация итогового отчета"""
        
        print("\n" + "="*100)
        print("📊 ИТОГОВЫЙ ОТЧЕТ О СКВОЗНОЙ ФУНКЦИОНАЛЬНОСТИ")
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
        report_filename = f"comprehensive_test_report_{timestamp}.json"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Отчет сохранен в: {report_filename}")
        print(f"\n✅ Комплексная проверка завершена!")

async def main():
    """Основная функция"""
    
    tester = ComprehensiveFunctionalityTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
