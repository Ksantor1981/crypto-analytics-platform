#!/usr/bin/env python3
"""
Система мониторинга здоровья сервисов
"""

import asyncio
import httpx
import redis
import psycopg2
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class HealthChecker:
    """Класс для проверки здоровья всех сервисов"""
    
    def __init__(self):
        self.services = {
            'backend': 'http://localhost:8000/health',
            'ml-service': 'http://localhost:8001/health',
            'frontend': 'http://localhost:3000',
            'redis': 'redis://localhost:6379/0',
            'postgres': 'postgresql://crypto_analytics_user:secure_postgres_password_2024!@localhost:5432/crypto_analytics'
        }
        
    async def check_http_service(self, name: str, url: str) -> Dict:
        """Проверка HTTP сервиса"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return {
                        'service': name,
                        'status': 'healthy',
                        'response_time': response.elapsed.total_seconds(),
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'service': name,
                        'status': 'unhealthy',
                        'error': f'HTTP {response.status_code}',
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                'service': name,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_redis(self) -> Dict:
        """Проверка Redis"""
        try:
            r = redis.from_url(self.services['redis'])
            r.ping()
            return {
                'service': 'redis',
                'status': 'healthy',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'service': 'redis',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_postgres(self) -> Dict:
        """Проверка PostgreSQL"""
        try:
            conn = psycopg2.connect(self.services['postgres'])
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return {
                'service': 'postgres',
                'status': 'healthy',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'service': 'postgres',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_all_services(self) -> Dict:
        """Проверка всех сервисов"""
        results = []
        
        # Проверяем HTTP сервисы
        http_tasks = []
        for name, url in self.services.items():
            if name in ['backend', 'ml-service', 'frontend']:
                http_tasks.append(self.check_http_service(name, url))
        
        http_results = await asyncio.gather(*http_tasks, return_exceptions=True)
        results.extend([r for r in http_results if isinstance(r, dict)])
        
        # Проверяем базы данных
        results.append(self.check_redis())
        results.append(self.check_postgres())
        
        # Общая статистика
        healthy_count = sum(1 for r in results if r.get('status') == 'healthy')
        total_count = len(results)
        
        return {
            'overall_status': 'healthy' if healthy_count == total_count else 'degraded',
            'healthy_services': healthy_count,
            'total_services': total_count,
            'services': results,
            'timestamp': datetime.now().isoformat()
        }

class AlertManager:
    """Менеджер алертов"""
    
    def __init__(self):
        self.alert_history = []
    
    def check_alerts(self, health_data: Dict) -> List[Dict]:
        """Проверка необходимости отправки алертов"""
        alerts = []
        
        for service in health_data.get('services', []):
            if service.get('status') == 'unhealthy':
                alert = {
                    'type': 'service_down',
                    'service': service.get('service'),
                    'message': f"Сервис {service.get('service')} недоступен: {service.get('error', 'Unknown error')}",
                    'severity': 'high',
                    'timestamp': datetime.now().isoformat()
                }
                alerts.append(alert)
        
        # Проверяем общий статус
        if health_data.get('overall_status') == 'degraded':
            alert = {
                'type': 'system_degraded',
                'message': f"Система работает в деградированном режиме: {health_data.get('healthy_services')}/{health_data.get('total_services')} сервисов работают",
                'severity': 'medium',
                'timestamp': datetime.now().isoformat()
            }
            alerts.append(alert)
        
        return alerts
    
    def send_alert(self, alert: Dict):
        """Отправка алерта (заглушка для демонстрации)"""
        logger.warning(f"ALERT: {alert['message']}")
        self.alert_history.append(alert)
        
        # В реальном проекте здесь будет отправка в Slack/Telegram/Email
        # self.send_to_slack(alert)
        # self.send_to_telegram(alert)
        # self.send_email(alert)

async def main():
    """Основная функция мониторинга"""
    health_checker = HealthChecker()
    alert_manager = AlertManager()
    
    logger.info("🔍 Запуск проверки здоровья сервисов...")
    
    # Проверяем все сервисы
    health_data = await health_checker.check_all_services()
    
    # Выводим результаты
    print("\n📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ ЗДОРОВЬЯ:")
    print("=" * 50)
    print(f"Общий статус: {health_data['overall_status'].upper()}")
    print(f"Работающих сервисов: {health_data['healthy_services']}/{health_data['total_services']}")
    print(f"Время проверки: {health_data['timestamp']}")
    print("\nДетали по сервисам:")
    
    for service in health_data['services']:
        status_icon = "✅" if service['status'] == 'healthy' else "❌"
        print(f"  {status_icon} {service['service']}: {service['status']}")
        if service.get('error'):
            print(f"      Ошибка: {service['error']}")
        if service.get('response_time'):
            print(f"      Время отклика: {service['response_time']:.3f}с")
    
    # Проверяем алерты
    alerts = alert_manager.check_alerts(health_data)
    
    if alerts:
        print(f"\n🚨 АЛЕРТЫ ({len(alerts)}):")
        for alert in alerts:
            print(f"  {alert['severity'].upper()}: {alert['message']}")
            alert_manager.send_alert(alert)
    else:
        print("\n✅ Алертов нет - все сервисы работают нормально")
    
    print("=" * 50)
    
    return health_data

if __name__ == "__main__":
    asyncio.run(main())
