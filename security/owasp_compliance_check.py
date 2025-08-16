#!/usr/bin/env python3
"""
OWASP Compliance Check для Crypto Analytics Platform
Проверка соответствия стандартам безопасности OWASP Top 10
"""

import os
import json
import subprocess
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SecurityCheck:
    """Класс для хранения результатов проверки безопасности"""
    name: str
    description: str
    status: str  # PASS, FAIL, WARNING
    details: Dict[str, Any]
    recommendation: str


class OWASPComplianceChecker:
    """Проверка соответствия OWASP Top 10 стандартам"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Инициализация проверки безопасности
        
        Args:
            base_url: Базовый URL для тестирования
        """
        self.base_url = base_url
        self.results: List[SecurityCheck] = []
    
    def check_broken_access_control(self) -> SecurityCheck:
        """A01:2021 - Broken Access Control"""
        logger.info("Проверка A01:2021 - Broken Access Control")
        
        issues = []
        recommendations = []
        
        # Проверка JWT токенов
        try:
            # Тест без токена
            response = requests.get(f"{self.base_url}/api/users/me", timeout=5)
            if response.status_code != 401:
                issues.append("Endpoint доступен без аутентификации")
                recommendations.append("Добавить middleware для проверки JWT токенов")
            
            # Тест с неверным токеном
            headers = {"Authorization": "Bearer invalid_token"}
            response = requests.get(f"{self.base_url}/api/users/me", headers=headers, timeout=5)
            if response.status_code != 401:
                issues.append("Endpoint доступен с неверным токеном")
                recommendations.append("Улучшить валидацию JWT токенов")
                
        except Exception as e:
            issues.append(f"Ошибка при проверке: {e}")
        
        # Проверка CORS
        try:
            response = requests.options(f"{self.base_url}/api/users/me", timeout=5)
            if "Access-Control-Allow-Origin" in response.headers:
                if response.headers["Access-Control-Allow-Origin"] == "*":
                    issues.append("CORS настроен слишком широко")
                    recommendations.append("Ограничить CORS для production")
        except Exception as e:
            issues.append(f"Ошибка при проверке CORS: {e}")
        
        status = "PASS" if not issues else "FAIL"
        
        return SecurityCheck(
            name="A01:2021 - Broken Access Control",
            description="Проверка контроля доступа и авторизации",
            status=status,
            details={"issues": issues, "endpoints_tested": ["/api/users/me"]},
            recommendation="; ".join(recommendations) if recommendations else "Все проверки пройдены"
        )
    
    def check_cryptographic_failures(self) -> SecurityCheck:
        """A02:2021 - Cryptographic Failures"""
        logger.info("Проверка A02:2021 - Cryptographic Failures")
        
        issues = []
        recommendations = []
        
        # Проверка HTTPS
        if not self.base_url.startswith("https"):
            issues.append("HTTPS не используется")
            recommendations.append("Настроить SSL/TLS сертификаты")
        
        # Проверка заголовков безопасности
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            headers = response.headers
            
            if "Strict-Transport-Security" not in headers:
                issues.append("Отсутствует HSTS заголовок")
                recommendations.append("Добавить Strict-Transport-Security заголовок")
            
            if "X-Content-Type-Options" not in headers:
                issues.append("Отсутствует X-Content-Type-Options заголовок")
                recommendations.append("Добавить X-Content-Type-Options: nosniff")
                
        except Exception as e:
            issues.append(f"Ошибка при проверке заголовков: {e}")
        
        # Проверка переменных окружения
        env_vars = [
            "SECRET_KEY",
            "DATABASE_URL",
            "REDIS_URL",
            "STRIPE_SECRET_KEY"
        ]
        
        for var in env_vars:
            if os.getenv(var):
                if len(os.getenv(var, "")) < 32:
                    issues.append(f"Слишком короткий {var}")
                    recommendations.append(f"Увеличить длину {var}")
            else:
                issues.append(f"Отсутствует {var}")
                recommendations.append(f"Добавить {var} в переменные окружения")
        
        status = "PASS" if not issues else "FAIL"
        
        return SecurityCheck(
            name="A02:2021 - Cryptographic Failures",
            description="Проверка криптографических настроек",
            status=status,
            details={"issues": issues, "headers_checked": ["HSTS", "X-Content-Type-Options"]},
            recommendation="; ".join(recommendations) if recommendations else "Все проверки пройдены"
        )
    
    def check_injection(self) -> SecurityCheck:
        """A03:2021 - Injection"""
        logger.info("Проверка A03:2021 - Injection")
        
        issues = []
        recommendations = []
        
        # Проверка SQL Injection
        try:
            # Тест с потенциально опасными символами
            test_payloads = [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "1' UNION SELECT * FROM users --"
            ]
            
            for payload in test_payloads:
                response = requests.get(
                    f"{self.base_url}/api/signals?search={payload}",
                    timeout=5
                )
                # Проверяем, что нет ошибок SQL
                if "sql" in response.text.lower() or "database" in response.text.lower():
                    issues.append(f"Возможная SQL injection: {payload}")
                    recommendations.append("Использовать параметризованные запросы")
                    
        except Exception as e:
            issues.append(f"Ошибка при проверке SQL injection: {e}")
        
        # Проверка XSS
        try:
            xss_payload = "<script>alert('XSS')</script>"
            response = requests.post(
                f"{self.base_url}/api/channels",
                json={"name": xss_payload, "url": "https://t.me/test"},
                timeout=5
            )
            # Проверяем, что скрипт не выполняется
            if xss_payload in response.text:
                issues.append("Возможная XSS уязвимость")
                recommendations.append("Экранировать пользовательский ввод")
                
        except Exception as e:
            issues.append(f"Ошибка при проверке XSS: {e}")
        
        status = "PASS" if not issues else "FAIL"
        
        return SecurityCheck(
            name="A03:2021 - Injection",
            description="Проверка уязвимостей инъекций",
            status=status,
            details={"issues": issues, "payloads_tested": len(test_payloads)},
            recommendation="; ".join(recommendations) if recommendations else "Все проверки пройдены"
        )
    
    def check_insecure_design(self) -> SecurityCheck:
        """A04:2021 - Insecure Design"""
        logger.info("Проверка A04:2021 - Insecure Design")
        
        issues = []
        recommendations = []
        
        # Проверка архитектуры
        try:
            # Проверка rate limiting
            for i in range(100):
                response = requests.get(f"{self.base_url}/api/health", timeout=5)
                if response.status_code == 429:
                    break
            else:
                issues.append("Отсутствует rate limiting")
                recommendations.append("Добавить rate limiting для API endpoints")
                
        except Exception as e:
            issues.append(f"Ошибка при проверке rate limiting: {e}")
        
        # Проверка валидации входных данных
        try:
            # Тест с неверными данными
            invalid_data = {
                "email": "invalid-email",
                "password": "123",  # слишком короткий
                "channel_url": "not-a-url"
            }
            
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json=invalid_data,
                timeout=5
            )
            
            if response.status_code == 200:
                issues.append("Недостаточная валидация входных данных")
                recommendations.append("Улучшить валидацию с помощью Pydantic")
                
        except Exception as e:
            issues.append(f"Ошибка при проверке валидации: {e}")
        
        status = "PASS" if not issues else "FAIL"
        
        return SecurityCheck(
            name="A04:2021 - Insecure Design",
            description="Проверка архитектурной безопасности",
            status=status,
            details={"issues": issues, "architecture_checks": ["rate_limiting", "validation"]},
            recommendation="; ".join(recommendations) if recommendations else "Все проверки пройдены"
        )
    
    def check_security_misconfiguration(self) -> SecurityCheck:
        """A05:2021 - Security Misconfiguration"""
        logger.info("Проверка A05:2021 - Security Misconfiguration")
        
        issues = []
        recommendations = []
        
        # Проверка заголовков безопасности
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            headers = response.headers
            
            security_headers = {
                "X-Frame-Options": "Защита от clickjacking",
                "X-XSS-Protection": "Защита от XSS",
                "X-Content-Type-Options": "Защита от MIME sniffing",
                "Referrer-Policy": "Контроль referrer",
                "Content-Security-Policy": "CSP политика"
            }
            
            for header, description in security_headers.items():
                if header not in headers:
                    issues.append(f"Отсутствует {header}")
                    recommendations.append(f"Добавить {header} заголовок")
                    
        except Exception as e:
            issues.append(f"Ошибка при проверке заголовков: {e}")
        
        # Проверка информации об ошибках
        try:
            response = requests.get(f"{self.base_url}/api/nonexistent", timeout=5)
            if "traceback" in response.text.lower() or "error" in response.text.lower():
                issues.append("Раскрытие информации об ошибках")
                recommendations.append("Настроить обработку ошибок в production")
                
        except Exception as e:
            issues.append(f"Ошибка при проверке ошибок: {e}")
        
        status = "PASS" if not issues else "FAIL"
        
        return SecurityCheck(
            name="A05:2021 - Security Misconfiguration",
            description="Проверка конфигурации безопасности",
            status=status,
            details={"issues": issues, "headers_checked": list(security_headers.keys())},
            recommendation="; ".join(recommendations) if recommendations else "Все проверки пройдены"
        )
    
    def check_vulnerable_components(self) -> SecurityCheck:
        """A06:2021 - Vulnerable and Outdated Components"""
        logger.info("Проверка A06:2021 - Vulnerable and Outdated Components")
        
        issues = []
        recommendations = []
        
        # Проверка зависимостей Python
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                vulnerabilities = json.loads(result.stdout)
                for vuln in vulnerabilities:
                    issues.append(f"Уязвимость в {vuln['package']}: {vuln['description']}")
                recommendations.append("Обновить уязвимые зависимости")
            else:
                logger.info("Уязвимостей в Python зависимостях не найдено")
                
        except Exception as e:
            issues.append(f"Ошибка при проверке Python зависимостей: {e}")
            recommendations.append("Установить и настроить safety")
        
        # Проверка версий основных компонентов
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if "server" in response.headers:
                server_info = response.headers["server"]
                if "development" in server_info.lower():
                    issues.append("Сервер работает в режиме разработки")
                    recommendations.append("Переключить в production режим")
                    
        except Exception as e:
            issues.append(f"Ошибка при проверке сервера: {e}")
        
        status = "PASS" if not issues else "FAIL"
        
        return SecurityCheck(
            name="A06:2021 - Vulnerable and Outdated Components",
            description="Проверка уязвимых компонентов",
            status=status,
            details={"issues": issues, "components_checked": ["python_deps", "server_mode"]},
            recommendation="; ".join(recommendations) if recommendations else "Все проверки пройдены"
        )
    
    def run_all_checks(self) -> List[SecurityCheck]:
        """Запуск всех проверок безопасности"""
        logger.info("Запуск полной проверки OWASP compliance")
        
        checks = [
            self.check_broken_access_control(),
            self.check_cryptographic_failures(),
            self.check_injection(),
            self.check_insecure_design(),
            self.check_security_misconfiguration(),
            self.check_vulnerable_components()
        ]
        
        self.results = checks
        return checks
    
    def generate_report(self) -> Dict[str, Any]:
        """Генерация отчета о безопасности"""
        total_checks = len(self.results)
        passed_checks = len([r for r in self.results if r.status == "PASS"])
        failed_checks = len([r for r in self.results if r.status == "FAIL"])
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "failed": failed_checks,
                "success_rate": (passed_checks / total_checks * 100) if total_checks > 0 else 0
            },
            "checks": [
                {
                    "name": check.name,
                    "description": check.description,
                    "status": check.status,
                    "details": check.details,
                    "recommendation": check.recommendation
                }
                for check in self.results
            ],
            "critical_issues": [
                check.name for check in self.results 
                if check.status == "FAIL" and "injection" in check.name.lower()
            ],
            "recommendations": list(set([
                check.recommendation for check in self.results 
                if check.recommendation and check.status == "FAIL"
            ]))
        }
        
        return report
    
    def save_report(self, filename: str = "owasp_compliance_report.json"):
        """Сохранение отчета в файл"""
        report = self.generate_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Отчет сохранен в {filename}")
        return filename


def main():
    """Основная функция для запуска проверки"""
    print("🔒 OWASP Compliance Check для Crypto Analytics Platform")
    print("=" * 60)
    
    # Создаем экземпляр проверки
    checker = OWASPComplianceChecker()
    
    # Запускаем все проверки
    results = checker.run_all_checks()
    
    # Выводим результаты
    print("\n📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
    print("-" * 40)
    
    for check in results:
        status_icon = "✅" if check.status == "PASS" else "❌"
        print(f"{status_icon} {check.name}")
        print(f"   Статус: {check.status}")
        if check.status == "FAIL":
            print(f"   Рекомендации: {check.recommendation}")
        print()
    
    # Генерируем отчет
    report = checker.generate_report()
    
    print("📈 СВОДКА:")
    print(f"   Всего проверок: {report['summary']['total_checks']}")
    print(f"   Пройдено: {report['summary']['passed']}")
    print(f"   Провалено: {report['summary']['failed']}")
    print(f"   Успешность: {report['summary']['success_rate']:.1f}%")
    
    # Сохраняем отчет
    filename = checker.save_report()
    print(f"\n📄 Отчет сохранен в: {filename}")
    
    # Критические проблемы
    if report['critical_issues']:
        print("\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
        for issue in report['critical_issues']:
            print(f"   ❌ {issue}")
    
    print("\n" + "=" * 60)
    if report['summary']['failed'] == 0:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ БЕЗОПАСНОСТИ!")


if __name__ == "__main__":
    main()
