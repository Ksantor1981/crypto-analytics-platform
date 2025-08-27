#!/usr/bin/env python3
"""
Скрипт для запуска API сервера и дашборда на одном порту
"""

import http.server
import socketserver
import webbrowser
import threading
import time
import os
import sys
import socket
import json
import sqlite3
from urllib.parse import urlparse
from datetime import datetime, timedelta

DB_PATH = "workers/signals.db"

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return None

class CombinedAPIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # API эндпоинты
            if path.startswith('/api/'):
                self.handle_api_request(path)
            else:
                # Статические файлы (HTML, CSS, JS)
                super().do_GET()
                
        except Exception as e:
            print(f"Ошибка обработки запроса: {e}")
            self.send_error(500, str(e))
    
    def handle_api_request(self, path):
        # CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if path == '/api/signals':
            response = self.get_signals()
        elif path == '/api/channels':
            response = self.get_channels()
        elif path == '/api/stats':
            response = self.get_stats()
        elif path == '/health':
            response = {"status": "ok", "timestamp": datetime.now().isoformat()}
        else:
            response = {"error": "Endpoint not found"}
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def get_signals(self):
        conn = get_db_connection()
        if not conn:
            return {"signals": [], "error": "Database connection failed"}
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM signals 
                ORDER BY timestamp DESC 
                LIMIT 50
            """)
            
            signals = []
            for row in cursor.fetchall():
                signal = dict(row)
                # Преобразуем timestamp
                if signal['timestamp']:
                    try:
                        if 'T' in signal['timestamp']:
                            dt = datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00'))
                        else:
                            dt = datetime.strptime(signal['timestamp'], '%Y-%m-%d %H:%M:%S')
                        signal['timestamp'] = dt.isoformat()
                    except:
                        pass
                
                # Убеждаемся, что числовые поля - числа
                for field in ['entry_price', 'target_price', 'stop_loss', 'real_confidence', 
                             'calculated_confidence', 'risk_reward_ratio', 'potential_profit', 'potential_loss']:
                    if signal[field] is not None:
                        try:
                            signal[field] = float(signal[field])
                        except:
                            signal[field] = 0.0
                
                signals.append(signal)
            
            return {"signals": signals}
            
        except Exception as e:
            print(f"Ошибка получения сигналов: {e}")
            return {"signals": [], "error": str(e)}
        finally:
            conn.close()
    
    def get_channels(self):
        conn = get_db_connection()
        if not conn:
            return {"channels": [], "error": "Database connection failed"}
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM channel_stats 
                ORDER BY total_signals DESC
            """)
            
            channels = []
            for row in cursor.fetchall():
                channel = dict(row)
                # Убеждаемся, что числовые поля - числа
                for field in ['total_signals', 'successful_signals', 'accuracy']:
                    if channel[field] is not None:
                        try:
                            channel[field] = float(channel[field])
                        except:
                            channel[field] = 0.0
                
                channels.append(channel)
            
            return {"channels": channels}
            
        except Exception as e:
            print(f"Ошибка получения каналов: {e}")
            return {"channels": [], "error": str(e)}
        finally:
            conn.close()
    
    def get_stats(self):
        conn = get_db_connection()
        if not conn:
            return {"error": "Database connection failed"}
        
        try:
            cursor = conn.cursor()
            
            # Общая статистика
            cursor.execute("SELECT COUNT(*) as total FROM signals")
            total_signals = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as total FROM channel_stats")
            total_channels = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(accuracy) as avg_accuracy FROM channel_stats")
            avg_accuracy = cursor.fetchone()[0] or 0.0
            
            # Недавние сигналы (последние 24 часа)
            yesterday = datetime.now() - timedelta(days=1)
            cursor.execute("""
                SELECT COUNT(*) as recent FROM signals 
                WHERE timestamp > ?
            """, (yesterday.isoformat(),))
            recent_signals = cursor.fetchone()[0]
            
            return {
                "total_signals": total_signals,
                "total_channels": total_channels,
                "avg_accuracy": float(avg_accuracy),
                "recent_signals": recent_signals
            }
            
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {"error": str(e)}
        finally:
            conn.close()

def start_server():
    """Запускает комбинированный сервер"""
    # Проверяем, что файл дашборда существует
    if not os.path.exists('dashboard.html'):
        print("❌ Ошибка: файл dashboard.html не найден!")
        print("Убедитесь, что вы находитесь в корневой папке проекта")
        return False
    
    # Проверяем базу данных
    if not os.path.exists(DB_PATH):
        print("❌ Ошибка: база данных не найдена!")
        print("Создайте базу данных, запустив create_database.py")
        return False
    
    PORT = 8000
    
    try:
        with socketserver.TCPServer(("", PORT), CombinedAPIHandler) as httpd:
            print(f"🚀 Комбинированный сервер запущен на http://localhost:{PORT}")
            print(f"📊 Дашборд доступен по адресу: http://localhost:{PORT}/dashboard.html")
            print("🔌 API эндпоинты:")
            print("   - GET /api/signals - список сигналов")
            print("   - GET /api/channels - статистика каналов")
            print("   - GET /api/stats - общая статистика")
            print("   - GET /health - проверка состояния")
            print("🔄 Нажмите Ctrl+C для остановки сервера")
            
            # Открываем браузер через 2 секунды
            def open_browser():
                time.sleep(2)
                webbrowser.open(f'http://localhost:{PORT}/dashboard.html')
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            # Запускаем сервер
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
        return True
    except OSError as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        return False

def main():
    """Основная функция"""
    print("=" * 60)
    print("🚀 CRYPTO ANALYTICS PLATFORM - КОМБИНИРОВАННЫЙ СЕРВЕР")
    print("=" * 60)
    print()
    print("📊 Запуск API сервера и дашборда на одном порту...")
    print("🎯 Особенности:")
    print("   • API сервер и дашборд на порту 8000")
    print("   • Реальные данные из базы данных")
    print("   • Темная тема с градиентным фоном")
    print("   • Фильтры и сортировка")
    print("   • Аналитика каналов")
    print()
    
    # Запускаем сервер
    success = start_server()
    
    if not success:
        print("\n💡 Альтернативные способы запуска:")
        print("1. python simple_api_server.py (только API)")
        print("2. python start_dashboard.py (только дашборд)")
        print("3. Откройте файл dashboard.html напрямую в браузере")
    
    return success

if __name__ == "__main__":
    main()
