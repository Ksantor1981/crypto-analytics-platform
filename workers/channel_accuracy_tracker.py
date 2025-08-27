import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChannelAccuracyTracker:
    """Система отслеживания точности каналов на основе исторических сигналов"""
    
    def __init__(self, db_path: str = "crypto_analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных для отслеживания точности"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для исторических сигналов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_name TEXT NOT NULL,
                channel_username TEXT NOT NULL,
                asset TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                target_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                signal_date TEXT NOT NULL,
                expected_date TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                result TEXT DEFAULT NULL,
                accuracy_score REAL DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица для статистики каналов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_name TEXT UNIQUE NOT NULL,
                channel_username TEXT UNIQUE NOT NULL,
                total_signals INTEGER DEFAULT 0,
                successful_signals INTEGER DEFAULT 0,
                accuracy_percentage REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                monthly_accuracy TEXT DEFAULT '{}'
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ База данных для отслеживания точности инициализирована")
    
    def add_signal(self, signal_data: Dict) -> int:
        """Добавляет новый сигнал в историю"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO historical_signals 
            (channel_name, channel_username, asset, direction, entry_price, 
             target_price, stop_loss, signal_date, expected_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal_data['channel_name'],
            signal_data['channel_username'],
            signal_data['asset'],
            signal_data['direction'],
            signal_data['entry_price'],
            signal_data['target_price'],
            signal_data['stop_loss'],
            signal_data['signal_date'],
            signal_data['expected_date']
        ))
        
        signal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Сигнал {signal_id} добавлен в историю: {signal_data['channel_name']} - {signal_data['asset']}")
        return signal_id
    
    def check_signal_result(self, signal_id: int, current_price: float, current_date: str = None) -> Dict:
        """Проверяет результат сигнала на основе текущей цены"""
        if current_date is None:
            current_date = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем данные сигнала
        cursor.execute('''
            SELECT channel_name, asset, direction, entry_price, target_price, 
                   stop_loss, expected_date, status
            FROM historical_signals WHERE id = ?
        ''', (signal_id,))
        
        signal = cursor.fetchone()
        if not signal:
            conn.close()
            return {"error": "Сигнал не найден"}
        
        channel_name, asset, direction, entry_price, target_price, stop_loss, expected_date, status = signal
        
        # Проверяем, прошла ли ожидаемая дата
        expected_dt = datetime.strptime(expected_date, "%Y-%m-%d")
        current_dt = datetime.strptime(current_date, "%Y-%m-%d")
        
        if current_dt < expected_dt:
            conn.close()
            return {
                "status": "PENDING",
                "message": f"Ожидаемая дата еще не наступила ({expected_date})"
            }
        
        # Определяем результат сигнала
        if direction == "LONG":
            if current_price >= target_price:
                result = "SUCCESS"
                accuracy_score = 1.0
            elif current_price <= stop_loss:
                result = "FAILED"
                accuracy_score = 0.0
            else:
                result = "PARTIAL"
                # Частичный успех - рассчитываем процент достижения цели
                progress = (current_price - entry_price) / (target_price - entry_price)
                accuracy_score = max(0.0, min(1.0, progress))
        else:  # SHORT
            if current_price <= target_price:
                result = "SUCCESS"
                accuracy_score = 1.0
            elif current_price >= stop_loss:
                result = "FAILED"
                accuracy_score = 0.0
            else:
                result = "PARTIAL"
                # Частичный успех для SHORT
                progress = (entry_price - current_price) / (entry_price - target_price)
                accuracy_score = max(0.0, min(1.0, progress))
        
        # Обновляем результат сигнала
        cursor.execute('''
            UPDATE historical_signals 
            SET status = ?, result = ?, accuracy_score = ?
            WHERE id = ?
        ''', (result, result, accuracy_score, signal_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Результат сигнала {signal_id}: {result} (точность: {accuracy_score:.1%})")
        
        return {
            "signal_id": signal_id,
            "channel_name": channel_name,
            "asset": asset,
            "direction": direction,
            "current_price": current_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "result": result,
            "accuracy_score": accuracy_score,
            "expected_date": expected_date,
            "current_date": current_date
        }
    
    def calculate_channel_accuracy(self, channel_name: str, months: int = 12) -> Dict:
        """Рассчитывает точность канала за последние N месяцев"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем все завершенные сигналы канала за последние N месяцев
        cutoff_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
        
        cursor.execute('''
            SELECT accuracy_score, signal_date, expected_date, asset, direction
            FROM historical_signals 
            WHERE channel_name = ? AND status != 'PENDING' AND expected_date >= ?
            ORDER BY signal_date DESC
        ''', (channel_name, cutoff_date))
        
        signals = cursor.fetchall()
        
        if not signals:
            conn.close()
            return {
                "channel_name": channel_name,
                "total_signals": 0,
                "successful_signals": 0,
                "accuracy_percentage": 0.0,
                "monthly_breakdown": {},
                "message": "Нет завершенных сигналов за указанный период"
            }
        
        # Рассчитываем общую точность
        total_signals = len(signals)
        successful_signals = sum(1 for s in signals if s[0] >= 0.5)  # Успешные сигналы (>=50%)
        accuracy_percentage = (successful_signals / total_signals) * 100
        
        # Месячная разбивка
        monthly_breakdown = {}
        for signal in signals:
            accuracy_score, signal_date, expected_date, asset, direction = signal
            month_key = expected_date[:7]  # YYYY-MM
            
            if month_key not in monthly_breakdown:
                monthly_breakdown[month_key] = {
                    "total": 0,
                    "successful": 0,
                    "accuracy": 0.0,
                    "signals": []
                }
            
            monthly_breakdown[month_key]["total"] += 1
            if accuracy_score >= 0.5:
                monthly_breakdown[month_key]["successful"] += 1
            
            monthly_breakdown[month_key]["signals"].append({
                "asset": asset,
                "direction": direction,
                "accuracy_score": accuracy_score,
                "expected_date": expected_date
            })
        
        # Рассчитываем месячную точность
        for month in monthly_breakdown:
            total = monthly_breakdown[month]["total"]
            successful = monthly_breakdown[month]["successful"]
            monthly_breakdown[month]["accuracy"] = (successful / total) * 100 if total > 0 else 0.0
        
        # Обновляем статистику канала в базе
        cursor.execute('''
            INSERT OR REPLACE INTO channel_accuracy 
            (channel_name, total_signals, successful_signals, accuracy_percentage, 
             monthly_accuracy, last_updated)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            channel_name, 
            total_signals, 
            successful_signals, 
            accuracy_percentage,
            json.dumps(monthly_breakdown)
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Точность канала {channel_name}: {accuracy_percentage:.1f}% ({successful_signals}/{total_signals})")
        
        return {
            "channel_name": channel_name,
            "total_signals": total_signals,
            "successful_signals": successful_signals,
            "accuracy_percentage": accuracy_percentage,
            "monthly_breakdown": monthly_breakdown
        }
    
    def get_channel_accuracy(self, channel_name: str) -> float:
        """Получает текущую точность канала"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT accuracy_percentage FROM channel_accuracy 
            WHERE channel_name = ?
        ''', (channel_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] / 100.0 if result else 0.5  # По умолчанию 50%
    
    def get_all_channels_accuracy(self) -> Dict[str, float]:
        """Получает точность всех каналов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT channel_name, accuracy_percentage FROM channel_accuracy
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return {channel: accuracy/100.0 for channel, accuracy in results}
    
    def simulate_historical_data(self):
        """Симулирует исторические данные для демонстрации"""
        logger.info("🔄 Создание симуляции исторических данных...")
        
        # Симулируем сигналы за последние 12 месяцев
        channels = [
            "Bitcoin & Ethereum Signals",
            "Crypto Capo", 
            "Crypto Signals",
            "Trading Signals Pro",
            "Bitcoin Analysis"
        ]
        
        assets = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOT"]
        
        # Генерируем исторические сигналы
        for month in range(12, 0, -1):
            month_date = (datetime.now() - timedelta(days=month*30)).strftime("%Y-%m")
            
            for channel in channels:
                # 2-4 сигнала в месяц на канал
                num_signals = 2 + (hash(channel + month_date) % 3)
                
                for i in range(num_signals):
                    asset = assets[hash(channel + str(i)) % len(assets)]
                    direction = "LONG" if (hash(asset + str(i)) % 2) == 0 else "SHORT"
                    
                    # Симулируем цены и результаты
                    base_price = {
                        "BTC": 100000, "ETH": 4000, "SOL": 200, 
                        "BNB": 500, "XRP": 0.6, "DOT": 4.0
                    }[asset]
                    
                    entry_price = base_price * (0.8 + 0.4 * (hash(f"{asset}{i}") % 100) / 100)
                    target_price = entry_price * (1.05 if direction == "LONG" else 0.95)
                    stop_loss = entry_price * (0.97 if direction == "LONG" else 1.03)
                    
                    # Симулируем результат (успешность зависит от канала)
                    channel_success_rate = {
                        "Bitcoin Analysis": 0.85,
                        "Bitcoin & Ethereum Signals": 0.80,
                        "Crypto Capo": 0.75,
                        "Trading Signals Pro": 0.70,
                        "Crypto Signals": 0.65
                    }.get(channel, 0.5)
                    
                    # Определяем результат на основе успешности канала
                    is_successful = (hash(f"{channel}{asset}{i}") % 100) < (channel_success_rate * 100)
                    
                    signal_date = f"{month_date}-{(i+1)*3:02d}"
                    expected_date = f"{month_date}-{(i+1)*3+7:02d}"
                    
                    signal_data = {
                        "channel_name": channel,
                        "channel_username": channel.lower().replace(" ", "_"),
                        "asset": asset,
                        "direction": direction,
                        "entry_price": round(entry_price, 2),
                        "target_price": round(target_price, 2),
                        "stop_loss": round(stop_loss, 2),
                        "signal_date": signal_date,
                        "expected_date": expected_date
                    }
                    
                    signal_id = self.add_signal(signal_data)
                    
                    # Симулируем результат
                    if is_successful:
                        result_price = target_price * (0.98 + 0.04 * (hash(f"result{i}") % 100) / 100)
                    else:
                        result_price = stop_loss * (0.98 + 0.04 * (hash(f"result{i}") % 100) / 100)
                    
                    self.check_signal_result(signal_id, result_price, expected_date)
        
        logger.info("✅ Симуляция исторических данных завершена")
        
        # Рассчитываем точность всех каналов
        for channel in channels:
            self.calculate_channel_accuracy(channel)

if __name__ == "__main__":
    tracker = ChannelAccuracyTracker()
    
    # Создаем симуляцию исторических данных
    tracker.simulate_historical_data()
    
    # Показываем результаты
    print("\n📊 ТОЧНОСТЬ КАНАЛОВ (за последние 12 месяцев):")
    print("=" * 60)
    
    channels_accuracy = tracker.get_all_channels_accuracy()
    for channel, accuracy in sorted(channels_accuracy.items(), key=lambda x: x[1], reverse=True):
        print(f"{channel:<30} {accuracy:.1%}")
    
    print("\n📈 ДЕТАЛЬНАЯ СТАТИСТИКА:")
    print("=" * 60)
    
    for channel in channels_accuracy.keys():
        stats = tracker.calculate_channel_accuracy(channel)
        print(f"\n{channel}:")
        print(f"  Всего сигналов: {stats['total_signals']}")
        print(f"  Успешных: {stats['successful_signals']}")
        print(f"  Точность: {stats['accuracy_percentage']:.1f}%")
        
        if stats['monthly_breakdown']:
            print("  Месячная разбивка:")
            for month, data in sorted(stats['monthly_breakdown'].items()):
                print(f"    {month}: {data['accuracy']:.1f}% ({data['successful']}/{data['total']})")
