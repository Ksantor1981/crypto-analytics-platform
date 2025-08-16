#!/usr/bin/env python3
"""
Главный скрипт мониторинга и алертов
"""

import asyncio
import time
import logging
import json
from datetime import datetime
from typing import Dict, List
import os

# Импортируем наши модули
from health_check import HealthChecker, AlertManager
from performance_metrics import PerformanceMetrics

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("monitoring.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MonitoringSystem:
    """Главная система мониторинга"""
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
        self.performance_metrics = PerformanceMetrics()
        self.monitoring_data = []
        
    async def run_health_check(self) -> Dict:
        """Запуск проверки здоровья сервисов"""
        logger.info("🔍 Запуск проверки здоровья...")
        
        health_data = await self.health_checker.check_all_services()
        
        # Проверяем алерты
        alerts = self.alert_manager.check_alerts(health_data)
        for alert in alerts:
            self.alert_manager.send_alert(alert)
        
        return health_data
    
    async def run_performance_check(self) -> Dict:
        """Запуск сбора метрик производительности"""
        logger.info("📊 Запуск сбора метрик производительности...")
        
        # Собираем метрики
        system_metrics = self.performance_metrics.get_system_metrics()
        api_metrics = await self.performance_metrics.get_api_metrics()
        db_metrics = self.performance_metrics.get_database_metrics()
        
        # Сохраняем метрики
        self.performance_metrics.save_metrics(system_metrics, api_metrics, db_metrics)
        
        # Получаем сводку
        summary = self.performance_metrics.get_metrics_summary(hours=1)
        
        return {
            'system_metrics': system_metrics,
            'api_metrics': api_metrics,
            'db_metrics': db_metrics,
            'summary': summary
        }
    
    def generate_report(self, health_data: Dict, performance_data: Dict) -> Dict:
        """Генерация отчета"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'health': health_data,
            'performance': performance_data,
            'alerts': self.alert_manager.alert_history[-10:],  # Последние 10 алертов
            'status': 'healthy' if health_data.get('overall_status') == 'healthy' else 'degraded'
        }
        
        # Сохраняем отчет
        self.monitoring_data.append(report)
        
        # Ограничиваем историю
        if len(self.monitoring_data) > 100:
            self.monitoring_data = self.monitoring_data[-100:]
        
        return report
    
    def print_report(self, report: Dict):
        """Вывод отчета в консоль"""
        print("\n" + "="*60)
        print("📊 ОТЧЕТ МОНИТОРИНГА")
        print("="*60)
        print(f"Время: {report['timestamp']}")
        print(f"Общий статус: {report['status'].upper()}")
        
        # Здоровье сервисов
        health = report['health']
        print(f"\n🏥 ЗДОРОВЬЕ СЕРВИСОВ:")
        print(f"  Статус: {health.get('overall_status', 'unknown')}")
        print(f"  Работающих: {health.get('healthy_services', 0)}/{health.get('total_services', 0)}")
        
        for service in health.get('services', []):
            status_icon = "✅" if service['status'] == 'healthy' else "❌"
            print(f"    {status_icon} {service['service']}: {service['status']}")
            if service.get('response_time'):
                print(f"      Время отклика: {service['response_time']:.3f}с")
        
        # Метрики производительности
        perf = report['performance']
        if perf.get('system_metrics'):
            sys_metrics = perf['system_metrics']
            print(f"\n💻 СИСТЕМНЫЕ МЕТРИКИ:")
            print(f"  CPU: {sys_metrics.get('cpu_percent', 0):.1f}%")
            print(f"  Память: {sys_metrics.get('memory_percent', 0):.1f}%")
            print(f"  Диск: {sys_metrics.get('disk_usage_percent', 0):.1f}%")
        
        if perf.get('api_metrics'):
            print(f"\n🌐 API МЕТРИКИ:")
            for metric in perf['api_metrics']:
                endpoint = metric['endpoint'].split('/')[-1]
                status = "✅" if metric.get('status_code') == 200 else "❌"
                response_time = metric.get('response_time', 0)
                print(f"  {status} {endpoint}: {response_time:.3f}с")
        
        # Алерты
        alerts = report.get('alerts', [])
        if alerts:
            print(f"\n🚨 ПОСЛЕДНИЕ АЛЕРТЫ ({len(alerts)}):")
            for alert in alerts[-5:]:  # Последние 5 алертов
                print(f"  {alert['severity'].upper()}: {alert['message']}")
        else:
            print(f"\n✅ Алертов нет")
        
        print("="*60)
    
    async def run_monitoring_cycle(self):
        """Один цикл мониторинга"""
        try:
            # Проверяем здоровье
            health_data = await self.run_health_check()
            
            # Собираем метрики производительности
            performance_data = await self.run_performance_check()
            
            # Генерируем отчет
            report = self.generate_report(health_data, performance_data)
            
            # Выводим отчет
            self.print_report(report)
            
            # Сохраняем отчет в файл
            self.save_report_to_file(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка в цикле мониторинга: {e}")
            return None
    
    def save_report_to_file(self, report: Dict):
        """Сохранение отчета в файл"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Отчет сохранен в {filename}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения отчета: {e}")
    
    async def run_continuous_monitoring(self, interval_seconds: int = 60):
        """Непрерывный мониторинг"""
        logger.info(f"🚀 Запуск непрерывного мониторинга (интервал: {interval_seconds}с)")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                logger.info(f"🔄 Цикл мониторинга #{cycle_count}")
                
                await self.run_monitoring_cycle()
                
                logger.info(f"⏳ Ожидание {interval_seconds} секунд до следующего цикла...")
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("🛑 Мониторинг остановлен пользователем")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в непрерывном мониторинге: {e}")
                await asyncio.sleep(10)  # Ждем 10 секунд перед повтором

async def main():
    """Основная функция"""
    print("🚀 ЗАПУСК СИСТЕМЫ МОНИТОРИНГА")
    print("="*50)
    
    # Создаем директорию для мониторинга
    os.makedirs(".", exist_ok=True)
    
    monitoring_system = MonitoringSystem()
    
    # Запускаем один цикл мониторинга
    report = await monitoring_system.run_monitoring_cycle()
    
    if report:
        print("\n✅ Мониторинг завершен успешно!")
    else:
        print("\n❌ Ошибка в мониторинге")

if __name__ == "__main__":
    asyncio.run(main())
