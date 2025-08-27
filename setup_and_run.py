#!/usr/bin/env python3
"""
Скрипт для установки зависимостей и запуска дашборда
"""

import subprocess
import sys
import os
import webbrowser
from pathlib import Path

def install_requirements():
    """Устанавливает необходимые зависимости"""
    print("📦 Установка зависимостей...")
    
    requirements = [
        'requests>=2.25.1',
        'urllib3>=1.26.0'
    ]
    
    for req in requirements:
        try:
            print(f"Устанавливаю {req}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', req])
            print(f"✅ {req} установлен")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки {req}: {e}")
            return False
    
    return True

def run_demo():
    """Запускает демонстрацию системы"""
    print("🎯 Запуск демонстрации системы...")
    
    try:
        # Переходим в папку workers
        workers_dir = Path('workers')
        if not workers_dir.exists():
            print("❌ Папка workers не найдена")
            return False
        
        # Запускаем демо
        demo_script = workers_dir / 'demo_comprehensive_system.py'
        if demo_script.exists():
            subprocess.check_call([sys.executable, str(demo_script)])
            print("✅ Демонстрация завершена")
            return True
        else:
            print("❌ Файл demo_comprehensive_system.py не найден")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска демо: {e}")
        return False

def open_dashboard():
    """Открывает дашборд в браузере"""
    print("🌐 Открытие дашборда...")
    
    dashboard_path = Path('workers/comprehensive_dashboard.html')
    if dashboard_path.exists():
        # Получаем абсолютный путь
        abs_path = dashboard_path.absolute()
        # Конвертируем в URL
        file_url = f"file:///{abs_path.as_posix()}"
        
        print(f"📁 Путь к дашборду: {abs_path}")
        print(f"🌐 URL: {file_url}")
        
        try:
            webbrowser.open(file_url)
            print("✅ Дашборд открыт в браузере")
            return True
        except Exception as e:
            print(f"❌ Ошибка открытия браузера: {e}")
            print(f"📋 Откройте вручную: {abs_path}")
            return False
    else:
        print("❌ Файл comprehensive_dashboard.html не найден")
        return False

def main():
    """Основная функция"""
    print("🚀 НАСТРОЙКА И ЗАПУСК ДАШБОРДА")
    print("=" * 50)
    
    # Устанавливаем зависимости
    if not install_requirements():
        print("❌ Не удалось установить зависимости")
        return
    
    # Запускаем демо
    if not run_demo():
        print("❌ Не удалось запустить демо")
        return
    
    # Открываем дашборд
    if not open_dashboard():
        print("❌ Не удалось открыть дашборд")
        return
    
    print("\n🎉 ВСЕ ГОТОВО!")
    print("📊 Дашборд должен открыться в браузере")
    print("🔄 Если не открылся, нажмите 'Обновить данные' в дашборде")

if __name__ == "__main__":
    main()
