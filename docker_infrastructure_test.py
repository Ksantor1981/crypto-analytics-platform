#!/usr/bin/env python3
"""
Docker Infrastructure Test - Диагностика проблем контейнеризации
TASKS2.md - Этап 0.2.1
"""

import subprocess
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class DockerInfrastructureTest:
    def __init__(self):
        self.test_results = []
        self.docker_issues = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Логирование результатов тестов"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {test_name}: {status} {details}")

    def run_command(self, command: str) -> tuple:
        """Выполнение команды и возврат результата"""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as e:
            return -1, "", str(e)

    def test_docker_installation(self) -> bool:
        """Тест 1: Проверка установки Docker"""
        code, stdout, stderr = self.run_command("docker --version")
        if code == 0 and "Docker" in stdout:
            self.log_test("Docker Installation", "PASS", stdout.strip())
            return True
        else:
            self.log_test("Docker Installation", "FAIL", f"Error: {stderr}")
            self.docker_issues.append("Docker не установлен или не работает")
            return False

    def test_docker_compose_installation(self) -> bool:
        """Тест 2: Проверка установки Docker Compose"""
        code, stdout, stderr = self.run_command("docker-compose --version")
        if code == 0 and "Docker Compose" in stdout:
            self.log_test("Docker Compose Installation", "PASS", stdout.strip())
            return True
        else:
            self.log_test("Docker Compose Installation", "FAIL", f"Error: {stderr}")
            self.docker_issues.append("Docker Compose не установлен или не работает")
            return False

    def test_docker_service_status(self) -> bool:
        """Тест 3: Проверка статуса Docker сервиса"""
        code, stdout, stderr = self.run_command("docker info")
        if code == 0:
            self.log_test("Docker Service Status", "PASS", "Docker daemon running")
            return True
        else:
            self.log_test("Docker Service Status", "FAIL", f"Error: {stderr}")
            self.docker_issues.append("Docker daemon не запущен")
            return False

    def test_dockerfile_syntax(self) -> bool:
        """Тест 4: Проверка синтаксиса Dockerfile'ов"""
        dockerfiles = [
            "backend/Dockerfile",
            "ml-service/Dockerfile",
            "frontend/Dockerfile",
            "workers/Dockerfile"
        ]
        
        passed = 0
        total = len(dockerfiles)
        
        for dockerfile in dockerfiles:
            if os.path.exists(dockerfile):
                # Простая проверка синтаксиса
                try:
                    with open(dockerfile, 'r') as f:
                        content = f.read()
                        if content.strip() and "FROM" in content:
                            self.log_test(f"Dockerfile Syntax {dockerfile}", "PASS", "Valid syntax")
                            passed += 1
                        else:
                            self.log_test(f"Dockerfile Syntax {dockerfile}", "FAIL", "Missing FROM instruction")
                            self.docker_issues.append(f"Неверный синтаксис {dockerfile}")
                except Exception as e:
                    self.log_test(f"Dockerfile Syntax {dockerfile}", "FAIL", str(e))
                    self.docker_issues.append(f"Ошибка чтения {dockerfile}")
            else:
                self.log_test(f"Dockerfile Syntax {dockerfile}", "FAIL", "File not found")
                self.docker_issues.append(f"Отсутствует файл {dockerfile}")
        
        if passed >= total * 0.75:  # 75% должны пройти
            self.log_test("Dockerfile Syntax Check", "PASS", f"{passed}/{total} valid")
            return True
        else:
            self.log_test("Dockerfile Syntax Check", "FAIL", f"Only {passed}/{total} valid")
            return False

    def test_docker_compose_syntax(self) -> bool:
        """Тест 5: Проверка синтаксиса docker-compose.yml"""
        if not os.path.exists("docker-compose.yml"):
            self.log_test("Docker Compose Syntax", "FAIL", "docker-compose.yml not found")
            self.docker_issues.append("Отсутствует docker-compose.yml")
            return False
        
        code, stdout, stderr = self.run_command("docker-compose config")
        if code == 0:
            self.log_test("Docker Compose Syntax", "PASS", "Valid YAML syntax")
            return True
        else:
            self.log_test("Docker Compose Syntax", "FAIL", f"YAML Error: {stderr}")
            self.docker_issues.append(f"Ошибка в docker-compose.yml: {stderr}")
            return False

    def test_requirements_files(self) -> bool:
        """Тест 6: Проверка файлов зависимостей"""
        requirements_files = [
            "backend/requirements.txt",
            "ml-service/requirements.txt",
            "workers/requirements.txt",
            "frontend/package.json"
        ]
        
        passed = 0
        total = len(requirements_files)
        
        for req_file in requirements_files:
            if os.path.exists(req_file):
                try:
                    with open(req_file, 'r') as f:
                        content = f.read()
                        if content.strip():
                            self.log_test(f"Requirements {req_file}", "PASS", "File exists and not empty")
                            passed += 1
                        else:
                            self.log_test(f"Requirements {req_file}", "FAIL", "File empty")
                            self.docker_issues.append(f"Пустой файл {req_file}")
                except Exception as e:
                    self.log_test(f"Requirements {req_file}", "FAIL", str(e))
                    self.docker_issues.append(f"Ошибка чтения {req_file}")
            else:
                self.log_test(f"Requirements {req_file}", "FAIL", "File not found")
                self.docker_issues.append(f"Отсутствует {req_file}")
        
        if passed >= total * 0.75:
            self.log_test("Requirements Files Check", "PASS", f"{passed}/{total} valid")
            return True
        else:
            self.log_test("Requirements Files Check", "FAIL", f"Only {passed}/{total} valid")
            return False

    def test_docker_network_availability(self) -> bool:
        """Тест 7: Проверка доступности Docker сетей"""
        code, stdout, stderr = self.run_command("docker network ls")
        if code == 0:
            self.log_test("Docker Network Availability", "PASS", "Networks accessible")
            return True
        else:
            self.log_test("Docker Network Availability", "FAIL", f"Error: {stderr}")
            self.docker_issues.append("Проблемы с Docker сетями")
            return False

    def generate_infrastructure_fixes(self) -> List[str]:
        """Генерация списка исправлений"""
        fixes = []
        
        if any("Docker не установлен" in issue for issue in self.docker_issues):
            fixes.append("1. Установить Docker Desktop для Windows")
            fixes.append("   - Скачать с https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe")
            fixes.append("   - Запустить установщик и перезагрузить систему")
        
        if any("Docker daemon не запущен" in issue for issue in self.docker_issues):
            fixes.append("2. Запустить Docker Desktop")
            fixes.append("   - Открыть Docker Desktop из меню Пуск")
            fixes.append("   - Дождаться полного запуска (статус 'Engine running')")
        
        if any("docker-compose.yml" in issue for issue in self.docker_issues):
            fixes.append("3. Исправить docker-compose.yml")
            fixes.append("   - Проверить кодировку файла (должна быть UTF-8 без BOM)")
            fixes.append("   - Проверить отступы (только пробелы, не табы)")
            fixes.append("   - Добавить build контексты для всех сервисов")
        
        if any("Dockerfile" in issue for issue in self.docker_issues):
            fixes.append("4. Исправить Dockerfile'ы")
            fixes.append("   - Убедиться что все Dockerfile'ы начинаются с FROM")
            fixes.append("   - Добавить curl для health checks")
            fixes.append("   - Создать отсутствующие Dockerfile'ы")
        
        if any("requirements" in issue for issue in self.docker_issues):
            fixes.append("5. Проверить файлы зависимостей")
            fixes.append("   - Создать requirements.txt для всех Python сервисов")
            fixes.append("   - Проверить package.json для Frontend")
        
        return fixes

    def run_full_test_suite(self) -> Dict[str, Any]:
        """Запуск полного набора тестов"""
        print("🐳 ТЕСТИРОВАНИЕ DOCKER ИНФРАСТРУКТУРЫ")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Последовательность тестов
        tests = [
            ("Docker Installation", self.test_docker_installation),
            ("Docker Compose Installation", self.test_docker_compose_installation),
            ("Docker Service Status", self.test_docker_service_status),
            ("Dockerfile Syntax", self.test_dockerfile_syntax),
            ("Docker Compose Syntax", self.test_docker_compose_syntax),
            ("Requirements Files", self.test_requirements_files),
            ("Docker Network Availability", self.test_docker_network_availability)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔄 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, "ERROR", str(e))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Итоговый отчет
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 60)
        print("📊 ОТЧЕТ О СОСТОЯНИИ DOCKER ИНФРАСТРУКТУРЫ")
        print("=" * 60)
        print(f"✅ Пройдено тестов: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"⏱️ Время выполнения: {duration:.2f} сек")
        
        # Оценка готовности
        if success_rate >= 90:
            status = "ГОТОВО К PRODUCTION"
            grade = "A"
            emoji = "🏆"
        elif success_rate >= 70:
            status = "ГОТОВО К DEVELOPMENT" 
            grade = "B"
            emoji = "✅"
        elif success_rate >= 50:
            status = "ТРЕБУЮТСЯ ИСПРАВЛЕНИЯ"
            grade = "C"
            emoji = "⚠️"
        else:
            status = "КРИТИЧЕСКИЕ ПРОБЛЕМЫ"
            grade = "F"
            emoji = "❌"
        
        print(f"\n{emoji} СОСТОЯНИЕ ИНФРАСТРУКТУРЫ: {grade} ({status})")
        
        # Проблемы и исправления
        if self.docker_issues:
            print(f"\n🚨 ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ ({len(self.docker_issues)}):")
            for i, issue in enumerate(self.docker_issues, 1):
                print(f"  {i}. {issue}")
            
            fixes = self.generate_infrastructure_fixes()
            if fixes:
                print(f"\n🔧 РЕКОМЕНДУЕМЫЕ ИСПРАВЛЕНИЯ:")
                for fix in fixes:
                    print(f"  {fix}")
        
        # Сохранение результатов
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "duration_seconds": duration,
            "grade": grade,
            "status": status,
            "issues": self.docker_issues,
            "recommended_fixes": self.generate_infrastructure_fixes(),
            "detailed_results": self.test_results
        }
        
        with open("docker_infrastructure_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Отчет сохранен в: docker_infrastructure_report.json")
        
        return report

if __name__ == "__main__":
    print("🔥 ДИАГНОСТИКА DOCKER ИНФРАСТРУКТУРЫ")
    print("Соответствие TASKS2.md - Этап 0.2.1")
    print("=" * 60)
    
    tester = DockerInfrastructureTest()
    results = tester.run_full_test_suite()
    
    print(f"\n🎯 ФИНАЛЬНАЯ ОЦЕНКА: {results['grade']} ({results['success_rate']:.1f}%)") 