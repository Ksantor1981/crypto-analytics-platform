#!/usr/bin/env python3
"""
Скрипт для запуска HTTP сервера и открытия дашборда
"""

import http.server
import socketserver
import webbrowser
import os
import threading
import time
from pathlib import Path

def start_server():
    """Запускает HTTP сервер"""
    # Переходим в папку workers
    os.chdir('workers')
    
    # Настройки сервера
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 HTTP сервер запущен на порту {PORT}")
        print(f"📁 Обслуживаемая папка: {os.getcwd()}")
        print("🔄 Сервер работает... Нажмите Ctrl+C для остановки")
        
        # Запускаем сервер в отдельном потоке
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Ждем немного, чтобы сервер запустился
        time.sleep(2)
        
        # Открываем дашборд в браузере
        dashboard_url = f"http://localhost:{PORT}/comprehensive_dashboard.html"
        print(f"🚀 Открываю дашборд: {dashboard_url}")
        
        try:
            webbrowser.open(dashboard_url)
            print("✅ Дашборд открыт в браузере!")
            print("\n📊 Теперь дашборд должен загрузить данные корректно!")
            print("🔄 Сервер продолжает работать...")
            
            # Ждем, пока пользователь не остановит сервер
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Останавливаю сервер...")
                httpd.shutdown()
                
        except Exception as e:
            print(f"❌ Ошибка открытия браузера: {e}")
            print(f"📋 Откройте вручную: {dashboard_url}")

def main():
    """Основная функция"""
    print("🚀 ЗАПУСК ДАШБОРДА ЧЕРЕЗ HTTP СЕРВЕР")
    print("=" * 50)
    
    # Проверяем наличие файлов
    dashboard_path = Path('workers/comprehensive_dashboard.html')
    data_path = Path('workers/comprehensive_signals_report.json')
    
    if not dashboard_path.exists():
        print("❌ Файл дашборда не найден!")
        return
    
    if not data_path.exists():
        print("❌ Файл с данными не найден!")
        print("💡 Запустите сначала: python workers/demo_comprehensive_system.py")
        return
    
    print("✅ Все файлы найдены")
    print("🌐 Запускаю HTTP сервер...")
    
    try:
        start_server()
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")

if __name__ == "__main__":
    main()
