#!/usr/bin/env python3
"""
PagerDuty Integration для Crypto Analytics Platform
Интеграция с PagerDuty для отправки критических алертов
"""

import os
import json
import httpx
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PagerDutyIntegration:
    """Интеграция с PagerDuty для отправки алертов"""
    
    def __init__(self, api_key: Optional[str] = None, service_id: Optional[str] = None):
        """
        Инициализация PagerDuty интеграции
        
        Args:
            api_key: PagerDuty API ключ
            service_id: ID сервиса в PagerDuty
        """
        self.api_key = api_key or os.getenv('PAGERDUTY_API_KEY')
        self.service_id = service_id or os.getenv('PAGERDUTY_SERVICE_ID')
        self.base_url = "https://api.pagerduty.com"
        
        if not self.api_key:
            logger.warning("PagerDuty API ключ не настроен")
        if not self.service_id:
            logger.warning("PagerDuty Service ID не настроен")
    
    def create_incident(self, 
                       summary: str, 
                       severity: str = "warning",
                       details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Создание инцидента в PagerDuty
        
        Args:
            summary: Краткое описание проблемы
            severity: Уровень критичности (info, warning, error, critical)
            details: Дополнительные детали
            
        Returns:
            bool: True если инцидент создан успешно
        """
        if not self.api_key or not self.service_id:
            logger.error("PagerDuty не настроен - пропускаем создание инцидента")
            return False
        
        try:
            payload = {
                "incident": {
                    "type": "incident",
                    "title": summary,
                    "service": {
                        "id": self.service_id,
                        "type": "service_reference"
                    },
                    "urgency": "high" if severity in ["error", "critical"] else "low",
                    "body": {
                        "type": "incident_body",
                        "details": json.dumps(details or {}, indent=2)
                    }
                }
            }
            
            headers = {
                "Accept": "application/vnd.pagerduty+json;version=2",
                "Authorization": f"Token token={self.api_key}",
                "Content-Type": "application/json"
            }
            
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/incidents",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 201:
                    incident_data = response.json()
                    incident_id = incident_data['incident']['id']
                    logger.info(f"PagerDuty инцидент создан: {incident_id}")
                    return True
                else:
                    logger.error(f"Ошибка создания PagerDuty инцидента: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при создании PagerDuty инцидента: {e}")
            return False
    
    def resolve_incident(self, incident_id: str) -> bool:
        """
        Разрешение инцидента в PagerDuty
        
        Args:
            incident_id: ID инцидента для разрешения
            
        Returns:
            bool: True если инцидент разрешен успешно
        """
        if not self.api_key:
            logger.error("PagerDuty API ключ не настроен")
            return False
        
        try:
            payload = {
                "incident": {
                    "type": "incident",
                    "status": "resolved"
                }
            }
            
            headers = {
                "Accept": "application/vnd.pagerduty+json;version=2",
                "Authorization": f"Token token={self.api_key}",
                "Content-Type": "application/json"
            }
            
            with httpx.Client() as client:
                response = client.put(
                    f"{self.base_url}/incidents/{incident_id}",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    logger.info(f"PagerDuty инцидент разрешен: {incident_id}")
                    return True
                else:
                    logger.error(f"Ошибка разрешения PagerDuty инцидента: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при разрешении PagerDuty инцидента: {e}")
            return False


class AlertManager:
    """Менеджер алертов с интеграцией PagerDuty"""
    
    def __init__(self):
        """Инициализация менеджера алертов"""
        self.pagerduty = PagerDutyIntegration()
        self.active_incidents = {}
    
    def send_critical_alert(self, 
                          service: str, 
                          message: str, 
                          details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправка критического алерта
        
        Args:
            service: Название сервиса
            message: Сообщение об ошибке
            details: Дополнительные детали
            
        Returns:
            bool: True если алерт отправлен успешно
        """
        summary = f"[CRITICAL] {service}: {message}"
        
        alert_details = {
            "service": service,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv('ENVIRONMENT', 'development'),
            "details": details or {}
        }
        
        # Создаем инцидент в PagerDuty
        success = self.pagerduty.create_incident(
            summary=summary,
            severity="critical",
            details=alert_details
        )
        
        if success:
            logger.info(f"Критический алерт отправлен: {summary}")
        else:
            logger.error(f"Не удалось отправить критический алерт: {summary}")
        
        return success
    
    def send_warning_alert(self, 
                          service: str, 
                          message: str, 
                          details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправка предупреждающего алерта
        
        Args:
            service: Название сервиса
            message: Сообщение об ошибке
            details: Дополнительные детали
            
        Returns:
            bool: True если алерт отправлен успешно
        """
        summary = f"[WARNING] {service}: {message}"
        
        alert_details = {
            "service": service,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv('ENVIRONMENT', 'development'),
            "details": details or {}
        }
        
        # Создаем инцидент в PagerDuty
        success = self.pagerduty.create_incident(
            summary=summary,
            severity="warning",
            details=alert_details
        )
        
        if success:
            logger.info(f"Предупреждающий алерт отправлен: {summary}")
        else:
            logger.error(f"Не удалось отправить предупреждающий алерт: {summary}")
        
        return success


# Пример использования
if __name__ == "__main__":
    # Тестирование PagerDuty интеграции
    alert_manager = AlertManager()
    
    # Тестовый критический алерт
    alert_manager.send_critical_alert(
        service="Backend API",
        message="Сервис недоступен более 5 минут",
        details={
            "response_time": "timeout",
            "last_check": "2025-08-16T16:30:00Z",
            "attempts": 3
        }
    )
    
    # Тестовый предупреждающий алерт
    alert_manager.send_warning_alert(
        service="ML Service",
        message="Высокое потребление памяти",
        details={
            "memory_usage": "85%",
            "cpu_usage": "70%",
            "recommendation": "Рассмотрите возможность масштабирования"
        }
    )
