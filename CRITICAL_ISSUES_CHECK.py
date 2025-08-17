#!/usr/bin/env python3
"""
🔍 КРИТИЧЕСКАЯ ПРОВЕРКА ПРОБЛЕМ ИЗ ПЛАНА РЕАЛИЗАЦИИ ПРОЕКТА

Проверяет все критические проблемы, упомянутые в Comprehensive Analysis:
1. Frontend недоступен - БЛОКИРУЕТ ПРОДАЖИ
2. Ошибки импорта в ML Service - НЕСТАБИЛЬНОСТЬ  
3. Отсутствует CI/CD в продакшене - РИСКИ ДЕПЛОЯ
4. Нет автоматического тестирования - КАЧЕСТВО КОДА
5. Проблемы с зависимостями - НЕСТАБИЛЬНОСТЬ
6. Отсутствует Staging-окружение
7. Нет базового аудита безопасности
8. Недостаточный функционал сбора и обработки данных
9. Проблемы с Onboarding и User Experience
"""

import asyncio
import sys
import json
import time
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import importlib.util

class CriticalIssuesChecker:
    """Проверка критических проблем из плана реализации"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "critical_issues": [],
            "details": {}
        }
        
    def log_check(self, category: str, check_name: str, status: str, message: str = "", error: str = ""):
        """Логирование результата проверки"""
        self.results["total_checks"] += 1
        
        if status == "PASS":
            self.results["passed"] += 1
            print(f"✅ {category}: {check_name} - {message}")
        elif status == "FAIL":
            self.results["failed"] += 1
            print(f"❌ {category}: {check_name} - {message}")
            if error:
                print(f"   Ошибка: {error}")
            self.results["critical_issues"].append(f"{category}: {check_name}")
        elif status == "WARNING":
            self.results["warnings"] += 1
            print(f"⚠️  {category}: {check_name} - {message}")
            
        if category not in self.results["details"]:
            self.results["details"][category] = []
            
        self.results["details"][category].append({
            "check": check_name,
            "status": status,
            "message": message,
            "error": error
        })
    
    def check_frontend_availability(self):
        """Проверка доступности Frontend - КРИТИЧЕСКАЯ ПРОБЛЕМА 1"""
        print("\n🔍 ПРОВЕРКА 1: Frontend недоступен - БЛОКИРУЕТ ПРОДАЖИ")
        
        # Проверка сборки frontend
        try:
            # Проверяем, что мы в правильной директории
            frontend_dir = Path("frontend")
            if not frontend_dir.exists():
                self.log_check("Frontend", "Сборка Next.js", "FAIL", "Папка frontend не найдена")
                return
                
            # Проверяем package.json
            package_json = frontend_dir / "package.json"
            if not package_json.exists():
                self.log_check("Frontend", "Сборка Next.js", "FAIL", "package.json не найден")
                return
                
            # Проверяем, что npm доступен
            try:
                # Пробуем найти npm в разных местах
                npm_paths = ["npm", "C:\\Program Files\\nodejs\\npm.cmd", "C:\\Program Files (x86)\\nodejs\\npm.cmd"]
                npm_found = False
                
                for npm_path in npm_paths:
                    try:
                        subprocess.run([npm_path, "--version"], capture_output=True, check=True)
                        npm_found = True
                        npm_cmd = npm_path
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                
                if not npm_found:
                    self.log_check("Frontend", "Сборка Next.js", "FAIL", "npm не найден в PATH")
                    return
                    
            except Exception as e:
                self.log_check("Frontend", "Сборка Next.js", "FAIL", f"Ошибка проверки npm: {str(e)}")
                return
                
            # Пробуем собрать проект
            result = subprocess.run(
                [npm_cmd, "run", "build"], 
                cwd=str(frontend_dir.absolute()), 
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            if result.returncode == 0:
                self.log_check("Frontend", "Сборка Next.js", "PASS", "Frontend успешно собирается")
            else:
                self.log_check("Frontend", "Сборка Next.js", "FAIL", "Ошибка сборки frontend", result.stderr)
                return
                
        except Exception as e:
            self.log_check("Frontend", "Сборка Next.js", "FAIL", "Не удалось запустить сборку", str(e))
            return
        
        # Проверка зависимостей
        try:
            with open("frontend/package.json", "r") as f:
                package_data = json.load(f)
                
            required_deps = ["@mui/material", "next", "react"]
            missing_deps = []
            
            for dep in required_deps:
                if dep not in package_data.get("dependencies", {}):
                    missing_deps.append(dep)
            
            if not missing_deps:
                self.log_check("Frontend", "Зависимости", "PASS", "Все необходимые зависимости установлены")
            else:
                self.log_check("Frontend", "Зависимости", "FAIL", f"Отсутствуют зависимости: {missing_deps}")
                
        except Exception as e:
            self.log_check("Frontend", "Зависимости", "FAIL", "Ошибка проверки package.json", str(e))
    
    def check_ml_service_stability(self):
        """Проверка стабильности ML Service - КРИТИЧЕСКАЯ ПРОБЛЕМА 2"""
        print("\n🔍 ПРОВЕРКА 2: Ошибки импорта в ML Service - НЕСТАБИЛЬНОСТЬ")
        
        try:
            # Проверка импорта основного модуля
            spec = importlib.util.spec_from_file_location("ml_main", "ml-service/main.py")
            ml_main = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ml_main)
            
            self.log_check("ML Service", "Импорт main.py", "PASS", "ML Service успешно импортируется")
            
        except Exception as e:
            self.log_check("ML Service", "Импорт main.py", "FAIL", "Ошибка импорта ML Service", str(e))
            return
        
        # Проверка моделей
        try:
            models_dir = Path("ml-service/models")
            if models_dir.exists():
                model_files = list(models_dir.glob("*.py"))
                if model_files:
                    self.log_check("ML Service", "Модели", "PASS", f"Найдено {len(model_files)} файлов моделей")
                else:
                    self.log_check("ML Service", "Модели", "WARNING", "Папка моделей пуста")
            else:
                self.log_check("ML Service", "Модели", "WARNING", "Папка моделей не найдена")
                
        except Exception as e:
            self.log_check("ML Service", "Модели", "FAIL", "Ошибка проверки моделей", str(e))
    
    def check_cicd_production(self):
        """Проверка CI/CD в продакшене - КРИТИЧЕСКАЯ ПРОБЛЕМА 3"""
        print("\n🔍 ПРОВЕРКА 3: Отсутствует CI/CD в продакшене - РИСКИ ДЕПЛОЯ")
        
        # Проверка наличия GitHub Actions
        workflows_dir = Path(".github/workflows")
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml"))
            
            required_workflows = ["ci.yml", "deploy-production.yml", "deploy-staging.yml"]
            found_workflows = [f.name for f in workflow_files]
            
            missing_workflows = [w for w in required_workflows if w not in found_workflows]
            
            if not missing_workflows:
                self.log_check("CI/CD", "GitHub Actions", "PASS", f"Найдено {len(workflow_files)} workflow файлов")
            else:
                self.log_check("CI/CD", "GitHub Actions", "WARNING", f"Отсутствуют: {missing_workflows}")
        else:
            self.log_check("CI/CD", "GitHub Actions", "FAIL", "Папка .github/workflows не найдена")
        
        # Проверка Docker конфигурации
        try:
            with open("docker-compose.yml", "r") as f:
                docker_config = f.read()
                
            required_services = ["backend", "frontend", "ml-service", "postgres", "redis"]
            missing_services = []
            
            for service in required_services:
                if service not in docker_config:
                    missing_services.append(service)
            
            if not missing_services:
                self.log_check("CI/CD", "Docker Compose", "PASS", "Все необходимые сервисы настроены")
            else:
                self.log_check("CI/CD", "Docker Compose", "FAIL", f"Отсутствуют сервисы: {missing_services}")
                
        except Exception as e:
            self.log_check("CI/CD", "Docker Compose", "FAIL", "Ошибка проверки docker-compose.yml", str(e))
    
    def check_automated_testing(self):
        """Проверка автоматического тестирования - КРИТИЧЕСКАЯ ПРОБЛЕМА 4"""
        print("\n🔍 ПРОВЕРКА 4: Нет автоматического тестирования - КАЧЕСТВО КОДА")
        
        # Проверка тестов backend
        backend_tests_dir = Path("backend/tests")
        if backend_tests_dir.exists():
            test_files = list(backend_tests_dir.glob("test_*.py"))
            if test_files:
                self.log_check("Testing", "Backend тесты", "PASS", f"Найдено {len(test_files)} тестовых файлов")
            else:
                self.log_check("Testing", "Backend тесты", "WARNING", "Тестовые файлы не найдены")
        else:
            self.log_check("Testing", "Backend тесты", "FAIL", "Папка backend/tests не найдена")
        
        # Проверка тестов frontend
        frontend_tests_dir = Path("frontend/tests")
        if frontend_tests_dir.exists():
            test_files = list(frontend_tests_dir.rglob("*.test.*"))
            if test_files:
                self.log_check("Testing", "Frontend тесты", "PASS", f"Найдено {len(test_files)} тестовых файлов")
            else:
                self.log_check("Testing", "Frontend тесты", "WARNING", "Тестовые файлы не найдены")
        else:
            self.log_check("Testing", "Frontend тесты", "WARNING", "Папка frontend/tests не найдена")
        
        # Проверка pytest конфигурации
        pytest_config = Path("backend/pytest.ini")
        if pytest_config.exists():
            self.log_check("Testing", "Pytest конфигурация", "PASS", "pytest.ini найден")
        else:
            self.log_check("Testing", "Pytest конфигурация", "WARNING", "pytest.ini не найден")
    
    def check_dependencies_stability(self):
        """Проверка стабильности зависимостей - КРИТИЧЕСКАЯ ПРОБЛЕМА 5"""
        print("\n🔍 ПРОВЕРКА 5: Проблемы с зависимостями - НЕСТАБИЛЬНОСТЬ")
        
        # Проверка requirements.txt
        try:
            # Пробуем разные кодировки
            encodings = ['utf-8', 'cp1251', 'latin-1', 'utf-16', 'utf-16le']
            backend_deps = None
            
            for encoding in encodings:
                try:
                    with open("backend/requirements.txt", "r", encoding=encoding) as f:
                        backend_deps = f.read()
                    # Проверяем, что файл прочитался правильно
                    if 'fastapi' in backend_deps:
                        break
                except UnicodeDecodeError:
                    continue
            
            if backend_deps is None:
                self.log_check("Dependencies", "Backend requirements", "FAIL", "Не удалось прочитать requirements.txt")
                return
                
            # Отладочная информация
            print(f"DEBUG: Прочитано {len(backend_deps)} символов из requirements.txt")
            print(f"DEBUG: Первые 100 символов: {repr(backend_deps[:100])}")
                
            critical_deps = ["fastapi", "sqlalchemy", "pydantic", "uvicorn"]
            missing_deps = []
            
            for dep in critical_deps:
                # Простая проверка наличия зависимости в тексте (убираем BOM)
                clean_deps = backend_deps.replace('\ufeff', '')
                if dep in clean_deps:
                    continue
                else:
                    missing_deps.append(dep)
            
            if not missing_deps:
                self.log_check("Dependencies", "Backend requirements", "PASS", "Все критические зависимости присутствуют")
            else:
                self.log_check("Dependencies", "Backend requirements", "FAIL", f"Отсутствуют: {missing_deps}")
                
        except Exception as e:
            self.log_check("Dependencies", "Backend requirements", "FAIL", "Ошибка чтения requirements.txt", str(e))
        
        # Проверка package.json
        try:
            with open("frontend/package.json", "r") as f:
                frontend_deps = json.load(f)
                
            critical_frontend_deps = ["next", "react", "react-dom"]
            missing_frontend_deps = []
            
            for dep in critical_frontend_deps:
                if dep not in frontend_deps.get("dependencies", {}):
                    missing_frontend_deps.append(dep)
            
            if not missing_frontend_deps:
                self.log_check("Dependencies", "Frontend package.json", "PASS", "Все критические зависимости присутствуют")
            else:
                self.log_check("Dependencies", "Frontend package.json", "FAIL", f"Отсутствуют: {missing_frontend_deps}")
                
        except Exception as e:
            self.log_check("Dependencies", "Frontend package.json", "FAIL", "Ошибка чтения package.json", str(e))
    
    def check_staging_environment(self):
        """Проверка Staging-окружения - КРИТИЧЕСКАЯ ПРОБЛЕМА 6"""
        print("\n🔍 ПРОВЕРКА 6: Отсутствует Staging-окружение")
        
        # Проверка staging workflow
        staging_workflow = Path(".github/workflows/deploy-staging.yml")
        if staging_workflow.exists():
            self.log_check("Staging", "Staging workflow", "PASS", "deploy-staging.yml найден")
        else:
            self.log_check("Staging", "Staging workflow", "FAIL", "deploy-staging.yml не найден")
        
        # Проверка environment переменных
        env_files = [".env.example", "env.example"]
        found_env = False
        
        for env_file in env_files:
            if Path(env_file).exists():
                self.log_check("Staging", "Environment файлы", "PASS", f"{env_file} найден")
                found_env = True
                break
        
        if not found_env:
            self.log_check("Staging", "Environment файлы", "WARNING", "Файл .env.example не найден")
    
    def check_security_audit(self):
        """Проверка базового аудита безопасности - КРИТИЧЕСКАЯ ПРОБЛЕМА 7"""
        print("\n🔍 ПРОВЕРКА 7: Нет базового аудита безопасности")
        
        # Проверка security workflow
        security_workflow = Path(".github/workflows/security-audit.yml")
        if security_workflow.exists():
            self.log_check("Security", "Security workflow", "PASS", "security-audit.yml найден")
        else:
            self.log_check("Security", "Security workflow", "WARNING", "security-audit.yml не найден")
        
        # Проверка .env файлов на секреты
        try:
            with open("docker-compose.yml", "r") as f:
                docker_content = f.read()
                
            # Проверяем на hardcoded секреты (не переменные окружения)
            hardcoded_patterns = [
                "password=",
                "secret=",
                "key=",
                "token="
            ]
            
            lines = docker_content.split('\n')
            hardcoded_found = []
            
            for line in lines:
                line_lower = line.lower().strip()
                if any(pattern in line_lower for pattern in hardcoded_patterns):
                    # Проверяем, что это не переменная окружения
                    if not line_lower.startswith(('- ', '  - ')) or '${' not in line:
                        hardcoded_found.append(line.strip())
            
            if hardcoded_found:
                self.log_check("Security", "Hardcoded secrets", "WARNING", f"Найдено {len(hardcoded_found)} возможных hardcoded секретов")
            else:
                self.log_check("Security", "Hardcoded secrets", "PASS", "Hardcoded секреты не найдены")
                
        except Exception as e:
            self.log_check("Security", "Hardcoded secrets", "FAIL", "Ошибка проверки секретов", str(e))
        
        # Проверка .gitignore
        try:
            with open(".gitignore", "r") as f:
                gitignore_content = f.read()
                
            security_patterns = [".env", "*.key", "*.pem", "secrets"]
            missing_patterns = []
            
            for pattern in security_patterns:
                if pattern not in gitignore_content:
                    missing_patterns.append(pattern)
            
            if not missing_patterns:
                self.log_check("Security", ".gitignore", "PASS", "Безопасные паттерны настроены")
            else:
                self.log_check("Security", ".gitignore", "WARNING", f"Отсутствуют паттерны: {missing_patterns}")
                
        except Exception as e:
            self.log_check("Security", ".gitignore", "FAIL", "Ошибка проверки .gitignore", str(e))
    
    def check_data_processing_functionality(self):
        """Проверка функционала сбора и обработки данных - КРИТИЧЕСКАЯ ПРОБЛЕМА 8"""
        print("\n🔍 ПРОВЕРКА 8: Недостаточный функционал сбора и обработки данных")
        
        # Проверка workers
        workers_dir = Path("workers")
        if workers_dir.exists():
            # Ищем файлы в основной папке и подпапках
            worker_files = list(workers_dir.rglob("*.py"))
            critical_workers = ["telegram_scraper.py", "reddit_collector.py", "signal_patterns.py"]
            
            found_workers = [f.name for f in worker_files]
            missing_workers = [w for w in critical_workers if w not in found_workers]
            
            if not missing_workers:
                self.log_check("Data Processing", "Workers", "PASS", f"Найдено {len(worker_files)} worker файлов")
            else:
                self.log_check("Data Processing", "Workers", "WARNING", f"Отсутствуют: {missing_workers}")
        else:
            self.log_check("Data Processing", "Workers", "FAIL", "Папка workers не найдена")
        
        # Проверка OCR
        try:
            ocr_service = Path("backend/app/services/ocr_service.py")
            if ocr_service.exists():
                self.log_check("Data Processing", "OCR Service", "PASS", "OCR сервис найден")
            else:
                self.log_check("Data Processing", "OCR Service", "WARNING", "OCR сервис не найден")
        except Exception as e:
            self.log_check("Data Processing", "OCR Service", "FAIL", "Ошибка проверки OCR", str(e))
    
    def check_user_experience(self):
        """Проверка Onboarding и User Experience - КРИТИЧЕСКАЯ ПРОБЛЕМА 9"""
        print("\n🔍 ПРОВЕРКА 9: Проблемы с Onboarding и User Experience")
        
        # Проверка README
        readme_files = ["README.md", "docs/README.md"]
        found_readme = False
        
        for readme in readme_files:
            if Path(readme).exists():
                self.log_check("UX", "Документация", "PASS", f"{readme} найден")
                found_readme = True
                break
        
        if not found_readme:
            self.log_check("UX", "Документация", "WARNING", "README.md не найден")
        
        # Проверка onboarding компонентов
        try:
            frontend_pages = Path("frontend/pages")
            if frontend_pages.exists():
                page_files = list(frontend_pages.glob("*.tsx"))
                if page_files:
                    self.log_check("UX", "Frontend страницы", "PASS", f"Найдено {len(page_files)} страниц")
                else:
                    self.log_check("UX", "Frontend страницы", "WARNING", "Страницы не найдены")
            else:
                self.log_check("UX", "Frontend страницы", "FAIL", "Папка pages не найдена")
        except Exception as e:
            self.log_check("UX", "Frontend страницы", "FAIL", "Ошибка проверки страниц", str(e))
    
    def run_all_checks(self):
        """Запуск всех проверок"""
        print("🚀 ЗАПУСК КРИТИЧЕСКОЙ ПРОВЕРКИ ПРОБЛЕМ ИЗ ПЛАНА РЕАЛИЗАЦИИ")
        print("=" * 80)
        
        start_time = time.time()
        
        self.check_frontend_availability()
        self.check_ml_service_stability()
        self.check_cicd_production()
        self.check_automated_testing()
        self.check_dependencies_stability()
        self.check_staging_environment()
        self.check_security_audit()
        self.check_data_processing_functionality()
        self.check_user_experience()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Подсчет результатов
        total = self.results["total_checks"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        warnings = self.results["warnings"]
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКОЙ ПРОВЕРКИ")
        print("=" * 80)
        print(f"⏱️  Время выполнения: {execution_time:.2f} секунд")
        print(f"📈 Всего проверок: {total}")
        print(f"✅ Успешных: {passed} ({success_rate:.1f}%)")
        print(f"❌ Ошибок: {failed}")
        print(f"⚠️  Предупреждений: {warnings}")
        
        if failed == 0:
            print("\n🎉 ОТЛИЧНО: Все критические проблемы решены!")
            print("🚀 Проект готов к продакшену")
        elif failed <= 2:
            print("\n✅ ХОРОШО: Большинство критических проблем решены")
            print("🔧 Требуются незначительные доработки")
        else:
            print("\n⚠️  ВНИМАНИЕ: Обнаружены критические проблемы")
            print("🔧 Требуется немедленное исправление")
        
        if self.results["critical_issues"]:
            print("\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
            for issue in self.results["critical_issues"]:
                print(f"   • {issue}")
        
        # Сохранение отчета
        report_file = f"critical_issues_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Отчет сохранен: {report_file}")
        
        return success_rate

async def main():
    """Основная функция"""
    checker = CriticalIssuesChecker()
    success_rate = checker.run_all_checks()
    return success_rate

if __name__ == "__main__":
    asyncio.run(main())
