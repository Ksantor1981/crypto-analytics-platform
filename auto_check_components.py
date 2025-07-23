#!/usr/bin/env python3
"""
Скрипт автоматической проверки всех компонентов
Crypto Analytics Platform - Задача 0.4.3
"""

import sys
import json
import time
import psutil
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Any, Tuple
import os
import socket

class ComponentChecker:
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.errors = []
        self.warnings = []
        
    def print_header(self, title: str):
        """Печать заголовка с форматированием"""
        print("=" * 80)
        print(f"🔍 {title}")
        print("=" * 80)
    
    def print_step(self, step: str):
        """Печать этапа проверки"""
        print(f"\n📋 {step}")
        print("-" * 60)
    
    def check_status(self, name: str, status: bool, details: str = ""):
        """Проверка и запись статуса компонента"""
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}: {'OK' if status else 'FAILED'}")
        if details:
            print(f"     {details}")
        
        self.results[name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if not status:
            self.errors.append(f"{name}: {details}")
        
        return status
    
    def check_docker_containers(self) -> bool:
        """Проверка Docker контейнеров"""
        self.print_step("ПРОВЕРКА DOCKER КОНТЕЙНЕРОВ")
        
        try:
            # Проверка Docker Desktop
            result = subprocess.run(['docker', '--version'], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.check_status("Docker Desktop", False, "Docker не установлен или не запущен")
                return False
            
            self.check_status("Docker Desktop", True, f"Версия: {result.stdout.strip()}")
            
            # Проверка запущенных контейнеров
            result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                                 capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0:
                self.check_status("Docker Containers", False, "Ошибка получения списка контейнеров")
                return False
            
            containers = []
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    try:
                        container = json.loads(line)
                        containers.append(container)
                    except:
                        continue
            
            # Проверка конкретных контейнеров
            required_containers = [
                'crypto-analytics-postgres',
                'crypto-analytics-redis',
                'crypto_analytics_ml'
            ]
            
            running_containers = [c.get('Names', '') for c in containers]
            all_running = True
            
            for container_name in required_containers:
                is_running = any(container_name in name for name in running_containers)
                if not self.check_status(f"Container {container_name}", is_running,
                                        "Работает" if is_running else "Не запущен"):
                    all_running = False
            
            return all_running
            
        except subprocess.TimeoutExpired:
            self.check_status("Docker Check", False, "Таймаут при проверке Docker")
            return False
        except Exception as e:
            self.check_status("Docker Check", False, f"Ошибка: {str(e)}")
            return False
    
    def check_network_ports(self) -> bool:
        """Проверка сетевых портов"""
        self.print_step("ПРОВЕРКА СЕТЕВЫХ ПОРТОВ")
        
        ports_to_check = {
            5432: "PostgreSQL Database",
            6379: "Redis Cache", 
            8001: "ML Service",
            8080: "Web Demo Server"
        }
        
        all_ports_ok = True
        
        for port, service in ports_to_check.items():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(3)
                    result = sock.connect_ex(('localhost', port))
                    is_open = result == 0
                    
                    self.check_status(f"Port {port} ({service})", is_open,
                                    "Доступен" if is_open else "Недоступен")
                    if not is_open:
                        all_ports_ok = False
                        
            except Exception as e:
                self.check_status(f"Port {port} ({service})", False, f"Ошибка: {str(e)}")
                all_ports_ok = False
        
        return all_ports_ok
    
    def check_api_endpoints(self) -> bool:
        """Проверка API endpoints"""
        self.print_step("ПРОВЕРКА API ENDPOINTS")
        
        endpoints = {
            "http://localhost:8001/api/v1/health/": "ML Service Health",
            "http://localhost:8080/api/status": "Web Demo Status"
        }
        
        all_endpoints_ok = True
        
        for url, name in endpoints.items():
            try:
                response = requests.get(url, timeout=10)
                is_ok = response.status_code == 200
                
                details = f"HTTP {response.status_code}"
                if is_ok:
                    try:
                        data = response.json()
                        if 'status' in data:
                            details += f", Status: {data['status']}"
                    except:
                        pass
                
                self.check_status(name, is_ok, details)
                if not is_ok:
                    all_endpoints_ok = False
                    
            except requests.exceptions.RequestException as e:
                self.check_status(name, False, f"Ошибка соединения: {str(e)}")
                all_endpoints_ok = False
            except Exception as e:
                self.check_status(name, False, f"Ошибка: {str(e)}")
                all_endpoints_ok = False
        
        return all_endpoints_ok
    
    def check_database_connection(self) -> bool:
        """Проверка подключения к базе данных"""
        self.print_step("ПРОВЕРКА БАЗЫ ДАННЫХ")
        
        try:
            import psycopg2
            
            conn_params = {
                'host': 'localhost',
                'port': 5432,
                'database': 'crypto_analytics',
                'user': 'postgres',
                'password': 'postgres123'
            }
            
            # Тест подключения
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor()
            
            # Проверка версии PostgreSQL
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            self.check_status("PostgreSQL Connection", True, f"Подключение успешно")
            
            # Проверка существования базы данных
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            self.check_status("Database Exists", True, f"База данных: {db_name}")
            
            # Проверка таблиц
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            table_count = cursor.fetchone()[0]
            self.check_status("Database Tables", table_count > 0, f"Таблиц найдено: {table_count}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except ImportError:
            self.check_status("PostgreSQL Driver", False, "psycopg2 не установлен")
            return False
        except Exception as e:
            self.check_status("Database Connection", False, f"Ошибка: {str(e)}")
            return False
    
    def check_redis_connection(self) -> bool:
        """Проверка подключения к Redis"""
        self.print_step("ПРОВЕРКА REDIS")
        
        try:
            import redis
            
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            
            # Тест ping
            result = r.ping()
            self.check_status("Redis Connection", result, "Ping успешно")
            
            # Тест записи/чтения
            test_key = "health_check_test"
            test_value = "test_value_" + str(int(time.time()))
            
            r.set(test_key, test_value, ex=10)  # Expire через 10 секунд
            read_value = r.get(test_key)
            
            write_read_ok = read_value == test_value
            self.check_status("Redis Read/Write", write_read_ok, 
                            "Запись/чтение работает" if write_read_ok else "Ошибка записи/чтения")
            
            # Очистка тестового ключа
            r.delete(test_key)
            
            # Информация о Redis
            info = r.info()
            memory_usage = info.get('used_memory_human', 'Unknown')
            self.check_status("Redis Info", True, f"Использование памяти: {memory_usage}")
            
            return result and write_read_ok
            
        except ImportError:
            self.check_status("Redis Driver", False, "redis-py не установлен")
            return False
        except Exception as e:
            self.check_status("Redis Connection", False, f"Ошибка: {str(e)}")
            return False
    
    def check_python_dependencies(self) -> bool:
        """Проверка Python зависимостей"""
        self.print_step("ПРОВЕРКА PYTHON ЗАВИСИМОСТЕЙ")
        
        required_packages = [
            'requests',
            'psycopg2',
            'redis',
            'psutil',
            'numpy',
            'pandas',
            'scikit-learn',
            'fastapi',
            'uvicorn'
        ]
        
        all_installed = True
        
        for package in required_packages:
            try:
                # Специальная обработка для scikit-learn
                if package == 'scikit-learn':
                    import sklearn
                else:
                    __import__(package.replace('-', '_'))
                self.check_status(f"Package {package}", True, "Установлен")
            except ImportError:
                self.check_status(f"Package {package}", False, "Не установлен")
                all_installed = False
        
        return all_installed
    
    def check_file_structure(self) -> bool:
        """Проверка файловой структуры проекта"""
        self.print_step("ПРОВЕРКА ФАЙЛОВОЙ СТРУКТУРЫ")
        
        required_files = [
            'quick_demo_0_4_1_fixed.py',
            'web_demo_0_4_2.html',
            'web_server_demo.py',
            'auto_check_components.py',
            'docker-compose.yml',
            'backend/requirements.txt',
            'ml-service/requirements.txt',
            'workers/requirements.txt'
        ]
        
        required_dirs = [
            'backend',
            'ml-service', 
            'workers',
            'frontend'
        ]
        
        all_files_ok = True
        
        # Проверка файлов
        for file_path in required_files:
            exists = os.path.exists(file_path)
            size = ""
            if exists:
                size = f"({os.path.getsize(file_path)} bytes)"
            
            self.check_status(f"File {file_path}", exists, 
                            f"Существует {size}" if exists else "Отсутствует")
            if not exists:
                all_files_ok = False
        
        # Проверка директорий
        for dir_path in required_dirs:
            exists = os.path.isdir(dir_path)
            self.check_status(f"Directory {dir_path}", exists,
                            "Существует" if exists else "Отсутствует")
            if not exists:
                all_files_ok = False
        
        return all_files_ok
    
    def check_system_resources(self) -> bool:
        """Проверка системных ресурсов"""
        self.print_step("ПРОВЕРКА СИСТЕМНЫХ РЕСУРСОВ")
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_ok = cpu_percent < 90
        self.check_status("CPU Usage", cpu_ok, f"{cpu_percent:.1f}%")
        
        # Память
        memory = psutil.virtual_memory()
        memory_ok = memory.percent < 90
        self.check_status("Memory Usage", memory_ok, 
                         f"{memory.percent:.1f}% ({memory.used // 1024 // 1024}MB used)")
        
        # Диск
        disk = psutil.disk_usage('.')
        disk_ok = disk.percent < 90
        self.check_status("Disk Usage", disk_ok, f"{disk.percent:.1f}%")
        
        return cpu_ok and memory_ok and disk_ok
    
    def run_end_to_end_test(self) -> bool:
        """Запуск end-to-end теста"""
        self.print_step("END-TO-END ТЕСТ")
        
        try:
            # Запуск упрощенной демонстрации
            result = subprocess.run([sys.executable, 'quick_demo_0_4_1_fixed.py'], 
                                 capture_output=True, text=True, timeout=60)
            
            success = result.returncode == 0
            details = "Тест прошел успешно" if success else f"Ошибка: {result.stderr}"
            
            self.check_status("End-to-End Test", success, details)
            
            if success:
                # Проверяем, что в выводе есть ключевые элементы
                output = result.stdout
                has_telegram = "ЭТАП 1: Получение сигналов из Telegram" in output
                has_parsing = "ЭТАП 2: Парсинг и анализ сигналов" in output
                has_market = "ЭТАП 3: Получение рыночных данных" in output
                has_ml = "ЭТАП 4: ML анализ и предсказания" in output
                has_results = "ЭТАП 5: Финальные рекомендации" in output
                has_completion = "ДЕМОНСТРАЦИЯ УСПЕШНО ЗАВЕРШЕНА" in output
                
                all_stages = all([has_telegram, has_parsing, has_market, has_ml, has_results, has_completion])
                self.check_status("Pipeline Stages", all_stages, 
                                f"Все этапы выполнены: {all_stages}")
                
                return success and all_stages
            
            return success
            
        except subprocess.TimeoutExpired:
            self.check_status("End-to-End Test", False, "Таймаут теста (60 секунд)")
            return False
        except Exception as e:
            self.check_status("End-to-End Test", False, f"Ошибка: {str(e)}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Генерация финального отчета"""
        self.print_step("ФИНАЛЬНЫЙ ОТЧЕТ")
        
        total_checks = len(self.results)
        passed_checks = len([r for r in self.results.values() if r['status']])
        failed_checks = total_checks - passed_checks
        
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        execution_time = time.time() - self.start_time
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "success_rate": success_rate,
            "overall_status": "PASS" if failed_checks == 0 else "FAIL",
            "results": self.results,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        print("📊 ОБЩАЯ СТАТИСТИКА:")
        print("=" * 50)
        print(f"✅ Проверок пройдено: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        print(f"❌ Проверок провалено: {failed_checks}")
        print(f"⏱️ Время выполнения: {execution_time:.1f} секунд")
        print(f"🎯 Общий статус: {report['overall_status']}")
        
        if self.errors:
            print(f"\n❌ ОШИБКИ ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️ ПРЕДУПРЕЖДЕНИЯ ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        return report
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Запуск всех проверок"""
        self.print_header("CRYPTO ANALYTICS PLATFORM - АВТОМАТИЧЕСКАЯ ПРОВЕРКА КОМПОНЕНТОВ")
        print("🎯 Задача 0.4.3 - Скрипт автоматической проверки всех компонентов")
        print("⏱️ Начало проверки...")
        
        # Последовательность проверок
        checks = [
            ("System Resources", self.check_system_resources),
            ("File Structure", self.check_file_structure),
            ("Python Dependencies", self.check_python_dependencies),
            ("Docker Containers", self.check_docker_containers),
            ("Network Ports", self.check_network_ports),
            ("Database Connection", self.check_database_connection),
            ("Redis Connection", self.check_redis_connection),
            ("API Endpoints", self.check_api_endpoints),
            ("End-to-End Test", self.run_end_to_end_test)
        ]
        
        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self.check_status(f"{check_name} (Exception)", False, f"Критическая ошибка: {str(e)}")
        
        return self.generate_report()

def main():
    """Главная функция"""
    checker = ComponentChecker()
    
    try:
        report = checker.run_all_checks()
        
        # Сохранение отчета
        report_file = f"component_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Отчет сохранен в файл: {report_file}")
        
        print("\n" + "=" * 80)
        if report['overall_status'] == 'PASS':
            print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
            print("✅ Задача 0.4.3 выполнена: создан скрипт автоматической проверки компонентов")
        else:
            print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В СИСТЕМЕ")
            print("🔧 Требуется устранение ошибок для полной функциональности")
        print("=" * 80)
        
        return report['overall_status'] == 'PASS'
        
    except KeyboardInterrupt:
        print("\n🛑 Проверка прервана пользователем")
        return False
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 