#!/usr/bin/env python3
"""
API сервер для Crypto Analytics Platform
Обновлен для отображения РЕАЛЬНОЙ статистики
"""
import json
import sqlite3
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='INFO:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Путь к БД
BASE_DIR = Path(__file__).parent
DB_PATH = str(BASE_DIR / 'workers' / 'signals.db')

class CryptoAPIHandler(BaseHTTPRequestHandler):
    """Обработчик API запросов"""
    
    def do_GET(self):
        """Обрабатывает GET запросы"""
        try:
            # Парсим URL
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            # CORS заголовки
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # Маршрутизация
            if path == '/api/signals':
                self.handle_signals()
            elif path == '/api/channels':
                self.handle_channels()
            elif path == '/api/stats':
                self.handle_stats()
            elif path == '/api/channel_stats':
                self.handle_channel_stats()
            elif path == '/api/signal_results':
                self.handle_signal_results()
            elif path == '/health':
                self.handle_health()
            elif path.startswith('/api/signal/'):
                signal_id = path.split('/')[-1]
                self.handle_signal_detail(signal_id)
            else:
                self.send_error(404, 'Not Found')
                
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {e}")
            self.send_error(500, 'Internal Server Error')
    
    def do_OPTIONS(self):
        """Обрабатывает CORS preflight запросы"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_health(self):
        """Проверка состояния сервера"""
        response = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': 'connected' if Path(DB_PATH).exists() else 'missing'
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
    
    def handle_signals(self):
        """Возвращает список сигналов"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # Сначала проверяем есть ли данные в signal_results
            cur.execute("SELECT COUNT(*) FROM signal_results")
            results_count = cur.fetchone()[0]
            
            if results_count > 0:
                # Получаем сигналы с результатами
                cur.execute("""
                    SELECT s.*, sr.result, sr.profit_loss, sr.current_price
                    FROM signals s
                    LEFT JOIN signal_results sr ON s.id = sr.signal_id
                    ORDER BY s.timestamp DESC
                    LIMIT 100
                """)
            else:
                # Получаем только сигналы без результатов
                cur.execute("""
                    SELECT s.*, NULL as result, NULL as profit_loss, NULL as current_price
                    FROM signals s
                    ORDER BY s.timestamp DESC
                    LIMIT 100
                """)
            
            columns = [desc[0] for desc in cur.description]
            signals = []
            
            for row in cur.fetchall():
                signal = dict(zip(columns, row))
                
                # Преобразуем JSON поля
                if signal.get('original_text'):
                    try:
                        signal['original_text'] = json.loads(signal['original_text'])
                    except:
                        pass
                
                if signal.get('validation_errors'):
                    try:
                        signal['validation_errors'] = json.loads(signal['validation_errors'])
                    except:
                        signal['validation_errors'] = []
                
                signals.append(signal)
            
            conn.close()
            
            response = {'signals': signals}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            logger.error(f"Ошибка получения сигналов: {e}")
            self.send_error(500, 'Database Error')
    
    def handle_channels(self):
        """Возвращает статистику каналов"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # Получаем статистику каналов
            cur.execute("""
                SELECT 
                    channel,
                    total_signals,
                    successful_signals,
                    win_rate,
                    avg_profit,
                    avg_loss,
                    total_profit,
                    last_updated
                FROM channel_stats
                ORDER BY win_rate DESC
            """)
            
            columns = [desc[0] for desc in cur.description]
            channels = []
            
            for row in cur.fetchall():
                channel = dict(zip(columns, row))
                channels.append(channel)
            
            # Если нет статистики, создаем базовую
            if not channels:
                cur.execute("""
                    SELECT channel, COUNT(*) as signal_count
                    FROM signals
                    GROUP BY channel
                    ORDER BY signal_count DESC
                """)
                
                for row in cur.fetchall():
                    channels.append({
                        'channel': row[0],
                        'total_signals': row[1],
                        'successful_signals': 0,
                        'win_rate': 0.0,
                        'avg_profit': 0.0,
                        'avg_loss': 0.0,
                        'total_profit': 0.0,
                        'last_updated': datetime.now(timezone.utc).isoformat()
                    })
            
            conn.close()
            
            response = {'channels': channels}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            logger.error(f"Ошибка получения каналов: {e}")
            self.send_error(500, 'Database Error')
    
    def handle_stats(self):
        """Возвращает общую статистику"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # Общая статистика
            cur.execute("SELECT COUNT(*) FROM signals")
            total_signals = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM signals WHERE is_valid = 1")
            valid_signals = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(DISTINCT channel) FROM signals")
            active_channels = cur.fetchone()[0]
            
            # Средняя точность
            cur.execute("""
                SELECT AVG(win_rate) 
                FROM channel_stats 
                WHERE total_signals >= 5
            """)
            avg_accuracy = cur.fetchone()[0] or 0.0
            
            # Статистика результатов (проверяем есть ли данные)
            cur.execute("SELECT COUNT(*) FROM signal_results")
            results_count = cur.fetchone()[0]
            
            if results_count > 0:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN result = 'hit_target' THEN 1 ELSE 0 END) as successful,
                        AVG(CASE WHEN result = 'hit_target' THEN profit_loss ELSE NULL END) as avg_profit,
                        AVG(CASE WHEN result = 'hit_stop' THEN profit_loss ELSE NULL END) as avg_loss
                    FROM signal_results
                    WHERE result IN ('hit_target', 'hit_stop')
                """)
                
                result_stats = cur.fetchone()
                if result_stats and result_stats[0] > 0:
                    total_results = result_stats[0]
                    successful_results = result_stats[1]
                    overall_win_rate = (successful_results / total_results) * 100
                    avg_profit = result_stats[2] or 0.0
                    avg_loss = result_stats[3] or 0.0
                else:
                    overall_win_rate = 0.0
                    avg_profit = 0.0
                    avg_loss = 0.0
            else:
                overall_win_rate = 0.0
                avg_profit = 0.0
                avg_loss = 0.0
            
            conn.close()
            
            response = {
                'total_signals': total_signals,
                'valid_signals': valid_signals,
                'active_channels': active_channels,
                'avg_accuracy': round(avg_accuracy, 1),
                'overall_win_rate': round(overall_win_rate, 1),
                'avg_profit': round(avg_profit, 2),
                'avg_loss': round(avg_loss, 2),
                'processed_messages': total_signals * 10,  # Примерная оценка
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            self.send_error(500, 'Database Error')
    
    def handle_channel_stats(self):
        """Возвращает детальную статистику канала"""
        try:
            # Получаем параметры
            parsed_path = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed_path.query)
            channel = params.get('channel', [''])[0]
            
            if not channel:
                self.send_error(400, 'Channel parameter required')
                return
            
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # Статистика канала
            cur.execute("""
                SELECT * FROM channel_stats WHERE channel = ?
            """, (channel,))
            
            channel_stats = cur.fetchone()
            
            # Последние сигналы канала
            cur.execute("""
                SELECT s.*, sr.result, sr.profit_loss
                FROM signals s
                LEFT JOIN signal_results sr ON s.id = sr.signal_id
                WHERE s.channel = ?
                ORDER BY s.timestamp DESC
                LIMIT 20
            """, (channel,))
            
            columns = [desc[0] for desc in cur.description]
            recent_signals = []
            
            for row in cur.fetchall():
                signal = dict(zip(columns, row))
                recent_signals.append(signal)
            
            conn.close()
            
            response = {
                'channel': channel,
                'stats': channel_stats,
                'recent_signals': recent_signals
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики канала: {e}")
            self.send_error(500, 'Database Error')
    
    def handle_signal_results(self):
        """Возвращает результаты сигналов"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT sr.*, s.asset, s.channel, s.direction
                FROM signal_results sr
                JOIN signals s ON sr.signal_id = s.id
                ORDER BY sr.updated_at DESC
                LIMIT 50
            """)
            
            columns = [desc[0] for desc in cur.description]
            results = []
            
            for row in cur.fetchall():
                result = dict(zip(columns, row))
                results.append(result)
            
            conn.close()
            
            response = {'results': results}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            logger.error(f"Ошибка получения результатов: {e}")
            self.send_error(500, 'Database Error')
    
    def handle_signal_detail(self, signal_id):
        """Возвращает детали сигнала"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT s.*, sr.result, sr.profit_loss, sr.current_price
                FROM signals s
                LEFT JOIN signal_results sr ON s.id = sr.signal_id
                WHERE s.id = ?
            """, (signal_id,))
            
            row = cur.fetchone()
            if not row:
                self.send_error(404, 'Signal not found')
                return
            
            columns = [desc[0] for desc in cur.description]
            signal = dict(zip(columns, row))
            
            # Преобразуем JSON поля
            if signal.get('original_text'):
                try:
                    signal['original_text'] = json.loads(signal['original_text'])
                except:
                    pass
            
            conn.close()
            
            self.wfile.write(json.dumps(signal, ensure_ascii=False).encode())
            
        except Exception as e:
            logger.error(f"Ошибка получения деталей сигнала: {e}")
            self.send_error(500, 'Database Error')

def main():
    """Запуск сервера"""
    port = 8000
    server_address = ('', port)
    
    logger.info(f"Запуск API сервера на http://localhost:{port}")
    logger.info("Доступные эндпоинты:")
    logger.info("- GET /api/signals - список сигналов")
    logger.info("- GET /api/channels - статистика каналов")
    logger.info("- GET /api/stats - общая статистика")
    logger.info("- GET /api/channel_stats?channel=name - статистика канала")
    logger.info("- GET /api/signal_results - результаты сигналов")
    logger.info("- GET /api/signal/{id} - детали сигнала")
    logger.info("- GET /health - проверка состояния")
    
    try:
        httpd = HTTPServer(server_address, CryptoAPIHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Сервер остановлен")
    except Exception as e:
        logger.error(f"Ошибка запуска сервера: {e}")

if __name__ == '__main__':
    main()
