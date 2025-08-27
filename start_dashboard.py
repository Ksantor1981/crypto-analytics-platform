#!/usr/bin/env python3
"""
Скрипт для запуска Crypto Analytics Platform
"""
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def main():
    print("🚀 Запуск Crypto Analytics Platform...")
    
    # Проверяем что мы в правильной директории
    if not Path("workers/signals.db").exists():
        print("❌ Файл workers/signals.db не найден")
        print("   Запустите сначала: python workers/real_signals_collector.py")
        return
    
    # Запускаем API сервер
    print("📡 Запуск API сервера...")
    try:
        server_process = subprocess.Popen([
            sys.executable, "simple_api_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ждем немного чтобы сервер запустился
        time.sleep(2)
        
        # Проверяем что сервер работает
        import urllib.request
        try:
            response = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
            if response.getcode() == 200:
                print("✅ API сервер запущен на http://localhost:8000")
            else:
                print("❌ API сервер не отвечает")
                return
        except Exception as e:
            print(f"❌ Ошибка подключения к API: {e}")
            return
        
        # Открываем дашборд в браузере
        print("🌐 Открытие дашборда...")
        dashboard_path = Path("dashboard.html").absolute()
        webbrowser.open(f"file://{dashboard_path}")
        
        print("✅ Дашборд открыт в браузере")
        print("📊 Для остановки нажмите Ctrl+C")
        
        # Ждем завершения
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Остановка сервера...")
            server_process.terminate()
            server_process.wait()
            print("✅ Сервер остановлен")
            
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    main()
