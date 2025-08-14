#!/usr/bin/env python3
"""
Скрипт валидации безопасности конфигурации
Crypto Analytics Platform - Задача 0.5.3
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
import subprocess

# Загружаем переменные окружения из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env файл загружен")
except ImportError:
    print("⚠️ python-dotenv не установлен, загружаем переменные вручную")
    # Простая загрузка .env файла
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ .env файл загружен вручную")
    else:
        print("⚠️ .env файл не найден")

class SecurityValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
        self.project_root = Path(__file__).parent
        
    def print_header(self, title: str):
        """Печать заголовка с форматированием"""
        print("=" * 80)
        print(f"🔒 {title}")
        print("=" * 80)
    
    def print_step(self, step: str):
        """Печать этапа проверки"""
        print(f"\n📋 {step}")
        print("-" * 60)
    
    def add_error(self, message: str, file: str = None, line: int = None):
        """Добавить критическую ошибку"""
        error = f"❌ {message}"
        if file:
            error += f" (файл: {file}"
            if line:
                error += f", строка: {line}"
            error += ")"
        self.errors.append(error)
        print(error)
    
    def add_warning(self, message: str, file: str = None):
        """Добавить предупреждение"""
        warning = f"⚠️ {message}"
        if file:
            warning += f" (файл: {file})"
        self.warnings.append(warning)
        print(warning)
    
    def add_success(self, message: str):
        """Добавить успешную проверку"""
        success = f"✅ {message}"
        self.passed.append(success)
        print(success)
    
    def check_hardcoded_secrets(self) -> bool:
        """Проверка на hardcoded секреты"""
        self.print_step("ПРОВЕРКА HARDCODED SECRETS")
        
        # Паттерны для поиска секретов
        secret_patterns = [
            r'password\s*[:=]\s*["\'][^"\']*["\']',
            r'secret.*key\s*[:=]\s*["\'][^"\']*["\']',
            r'token\s*[:=]\s*["\'][^"\']*["\']',
            r'api.*key\s*[:=]\s*["\'][^"\']*["\']',
            r'postgres123',
            r'crypto-analytics-secret-key',
            r'sk_test_',
            r'pk_test_',
            r'whsec_',
        ]
        
        # Файлы для проверки
        files_to_check = [
            'docker-compose.yml',
            'docker-compose.fixed.yml', 
            'docker-compose.simple.yml',
            'helm/values.yaml',
            'infrastructure/helm/crypto-analytics/values.yaml'
        ]
        
        # Добавляем все Python файлы
        for py_file in self.project_root.rglob('*.py'):
            if 'venv' not in str(py_file) and '__pycache__' not in str(py_file):
                files_to_check.append(str(py_file.relative_to(self.project_root)))
        
        found_secrets = False
        
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern in secret_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                # Исключаем комментарии и безопасные паттерны
                                if not line.strip().startswith('#') and 'CHANGE_THIS' not in line:
                                    self.add_error(
                                        f"Найден hardcoded секрет: {line.strip()}",
                                        str(file_path),
                                        line_num
                                    )
                                    found_secrets = True
                                    
            except Exception as e:
                self.add_warning(f"Не удалось проверить файл {file_path}: {e}")
        
        if not found_secrets:
            self.add_success("Hardcoded секреты не найдены")
            return True
        else:
            return False
    
    def check_environment_variables(self) -> bool:
        """Проверка переменных окружения"""
        self.print_step("ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
        
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'REDIS_URL',
            'ENVIRONMENT',
            'DEBUG'
        ]
        
        optional_vars = [
            'STRIPE_SECRET_KEY',
            'STRIPE_PUBLISHABLE_KEY',
            'TELEGRAM_BOT_TOKEN',
            'BYBIT_API_KEY',
            'BINANCE_API_KEY'
        ]
        
        missing_required = []
        missing_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
            else:
                self.add_success(f"Переменная {var} установлена")
        
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
            else:
                self.add_success(f"Переменная {var} установлена")
        
        if missing_required:
            for var in missing_required:
                self.add_error(f"Отсутствует обязательная переменная: {var}")
            return False
        
        if missing_optional:
            for var in missing_optional:
                self.add_warning(f"Отсутствует опциональная переменная: {var}")
        
        return True
    
    def check_debug_settings(self) -> bool:
        """Проверка настроек DEBUG"""
        self.print_step("ПРОВЕРКА НАСТРОЕК DEBUG")
        
        debug_value = os.getenv('DEBUG', 'false').lower()
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        
        if environment == 'production' and debug_value in ['true', '1', 'yes']:
            self.add_error("DEBUG=True в production окружении!")
            return False
        
        if environment == 'development' and debug_value in ['true', '1', 'yes']:
            self.add_warning("DEBUG=True в development (нормально для разработки)")
        
        self.add_success(f"DEBUG настройки корректны для {environment}")
        return True
    
    def check_secret_key_strength(self) -> bool:
        """Проверка силы SECRET_KEY"""
        self.print_step("ПРОВЕРКА СИЛЫ SECRET_KEY")
        
        secret_key = os.getenv('SECRET_KEY', '')
        
        if not secret_key:
            self.add_error("SECRET_KEY не установлен")
            return False
        
        if len(secret_key) < 32:
            self.add_error(f"SECRET_KEY слишком короткий: {len(secret_key)} символов (минимум 32)")
            return False
        
        if 'CHANGE_THIS' in secret_key:
            self.add_error("SECRET_KEY содержит placeholder значение")
            return False
        
        # Проверяем на разнообразие символов
        if len(set(secret_key)) < 16:
            self.add_warning("SECRET_KEY имеет низкое разнообразие символов")
        
        self.add_success(f"SECRET_KEY соответствует требованиям безопасности ({len(secret_key)} символов)")
        return True
    
    def check_docker_security(self) -> bool:
        """Проверка безопасности Docker конфигурации"""
        self.print_step("ПРОВЕРКА БЕЗОПАСНОСТИ DOCKER")
        
        docker_files = [
            'docker-compose.yml',
            'docker-compose.fixed.yml',
            'docker-compose.simple.yml'
        ]
        
        all_safe = True
        
        for docker_file in docker_files:
            file_path = self.project_root / docker_file
            if not file_path.exists():
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Проверяем на hardcoded пароли
                    if 'postgres123' in content:
                        self.add_error(f"Hardcoded пароль в {docker_file}")
                        all_safe = False
                    
                    # Проверяем на переменные окружения
                    if '${POSTGRES_PASSWORD}' in content or '${SECRET_KEY}' in content:
                        self.add_success(f"{docker_file} использует переменные окружения")
                    else:
                        self.add_warning(f"{docker_file} может содержать hardcoded значения")
                        
            except Exception as e:
                self.add_warning(f"Не удалось проверить {docker_file}: {e}")
        
        return all_safe
    
    def generate_security_report(self) -> Dict:
        """Генерация отчета по безопасности"""
        self.print_step("ФИНАЛЬНЫЙ ОТЧЕТ ПО БЕЗОПАСНОСТИ")
        
        total_checks = len(self.passed) + len(self.warnings) + len(self.errors)
        passed_checks = len(self.passed)
        failed_checks = len(self.errors)
        warning_checks = len(self.warnings)
        
        security_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        report = {
            "timestamp": "2025-01-13",
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "warning_checks": warning_checks,
            "security_score": security_score,
            "status": "PASS" if failed_checks == 0 else "FAIL",
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors
        }
        
        print("📊 СТАТИСТИКА БЕЗОПАСНОСТИ:")
        print("=" * 50)
        print(f"✅ Проверок пройдено: {passed_checks}/{total_checks} ({security_score:.1f}%)")
        print(f"⚠️ Предупреждений: {warning_checks}")
        print(f"❌ Критических ошибок: {failed_checks}")
        print(f"🎯 Общий статус: {report['status']}")
        
        if self.errors:
            print(f"\n❌ КРИТИЧЕСКИЕ ОШИБКИ ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️ ПРЕДУПРЕЖДЕНИЯ ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        return report
    
    def run_all_checks(self) -> Dict:
        """Запуск всех проверок безопасности"""
        self.print_header("CRYPTO ANALYTICS PLATFORM - ВАЛИДАЦИЯ БЕЗОПАСНОСТИ")
        print("🎯 Задача 0.5.3 - Унификация управления секретами")
        print("⏱️ Начало проверки безопасности...")
        
        # Последовательность проверок
        checks = [
            ("Hardcoded Secrets", self.check_hardcoded_secrets),
            ("Environment Variables", self.check_environment_variables),
            ("Debug Settings", self.check_debug_settings),
            ("Secret Key Strength", self.check_secret_key_strength),
            ("Docker Security", self.check_docker_security)
        ]
        
        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self.add_error(f"Ошибка в проверке {check_name}: {str(e)}")
        
        return self.generate_security_report()

def main():
    """Главная функция"""
    validator = SecurityValidator()
    
    try:
        report = validator.run_all_checks()
        
        # Сохранение отчета
        report_file = f"security_audit_report_{report['timestamp']}.json"
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Отчет сохранен в файл: {report_file}")
        
        print("\n" + "=" * 80)
        if report['status'] == 'PASS':
            print("✅ ВСЕ ПРОВЕРКИ БЕЗОПАСНОСТИ ПРОЙДЕНЫ!")
            print("✅ Задача 0.5.3 выполнена: безопасность настроена корректно")
        else:
            print("❌ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ БЕЗОПАСНОСТИ")
            print("🔧 Требуется устранение ошибок перед production deployment")
        print("=" * 80)
        
        return report['status'] == 'PASS'
        
    except KeyboardInterrupt:
        print("\n🛑 Проверка безопасности прервана пользователем")
        return False
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
