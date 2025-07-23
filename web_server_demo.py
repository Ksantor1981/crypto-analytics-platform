#!/usr/bin/env python3
"""
Простой веб-сервер для демонстрации Crypto Analytics Platform
Задача 0.4.2 - Веб-интерфейс для демонстрации
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class CryptoAnalyticsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET запросов"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_main_page()
        elif parsed_path.path == '/api/analyze':
            self.serve_analysis()
        elif parsed_path.path == '/api/status':
            self.serve_status()
        else:
            self.send_error(404, "Not Found")
    
    def serve_main_page(self):
        """Главная страница с интерактивным интерфейсом"""
        html_content = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Analytics Platform - Live Demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }

        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #27ae60;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .controls {
            text-align: center;
            margin-bottom: 30px;
        }

        .btn {
            background: linear-gradient(45deg, #3498db, #2ecc71);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 10px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .loading {
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            margin: 20px 0;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .results {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }

        .signal-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 5px solid #3498db;
        }

        .signal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .asset-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
        }

        .recommendation {
            padding: 5px 12px;
            border-radius: 15px;
            font-weight: bold;
            font-size: 0.9em;
        }

        .recommendation.strong-buy {
            background: #27ae60;
            color: white;
        }

        .recommendation.sell {
            background: #e74c3c;
            color: white;
        }

        .signal-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            font-size: 0.9em;
        }

        .detail-item {
            color: #7f8c8d;
        }

        .detail-value {
            font-weight: bold;
            color: #2c3e50;
        }

        .log {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 20px;
        }

        .log-entry {
            margin-bottom: 5px;
            padding: 2px 0;
        }

        .log-timestamp {
            color: #95a5a6;
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Crypto Analytics Platform</h1>
            <p><span class="status-indicator"></span>Live Demo - Задача 0.4.2</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="runAnalysis()" id="analyzeBtn">
                🔍 Запустить анализ
            </button>
            <button class="btn" onclick="clearResults()" id="clearBtn">
                🗑️ Очистить результаты
            </button>
        </div>

        <div id="loading" class="loading" style="display: none;">
            <div class="spinner"></div>
            <p>Выполняется анализ торговых сигналов...</p>
            <p id="loadingStatus">Инициализация...</p>
        </div>

        <div id="results" class="results" style="display: none;">
            <h2>📊 Результаты анализа</h2>
            <div id="signalsContainer"></div>
            <div id="statsContainer"></div>
        </div>

        <div class="results">
            <h3>📝 Лог выполнения</h3>
            <div id="logContainer" class="log"></div>
        </div>
    </div>

    <script>
        let logContainer = document.getElementById('logContainer');
        
        function addLogEntry(message) {
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span>${message}`;
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        function showLoading() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            document.getElementById('analyzeBtn').disabled = true;
        }

        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('analyzeBtn').disabled = false;
        }

        function updateLoadingStatus(status) {
            document.getElementById('loadingStatus').textContent = status;
        }

        async function runAnalysis() {
            showLoading();
            addLogEntry('🚀 Запуск анализа торговых сигналов...');
            
            try {
                updateLoadingStatus('Получение данных из Telegram...');
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                updateLoadingStatus('Парсинг сигналов...');
                await new Promise(resolve => setTimeout(resolve, 800));
                
                updateLoadingStatus('Получение рыночных данных...');
                await new Promise(resolve => setTimeout(resolve, 1200));
                
                updateLoadingStatus('ML анализ...');
                await new Promise(resolve => setTimeout(resolve, 1500));
                
                updateLoadingStatus('Генерация рекомендаций...');
                await new Promise(resolve => setTimeout(resolve, 500));
                
                const response = await fetch('/api/analyze');
                const data = await response.json();
                
                displayResults(data);
                addLogEntry('✅ Анализ успешно завершен');
                
            } catch (error) {
                addLogEntry(`❌ Ошибка: ${error.message}`);
            } finally {
                hideLoading();
            }
        }

        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            const signalsContainer = document.getElementById('signalsContainer');
            const statsContainer = document.getElementById('statsContainer');
            
            // Отображение сигналов
            signalsContainer.innerHTML = '';
            data.signals.forEach(signal => {
                const signalCard = document.createElement('div');
                signalCard.className = 'signal-card';
                signalCard.innerHTML = `
                    <div class="signal-header">
                        <div class="asset-name">${signal.asset}</div>
                        <div class="recommendation ${signal.recommendation_class}">${signal.recommendation}</div>
                    </div>
                    <div class="signal-details">
                        <div class="detail-item">
                            ML Скор: <span class="detail-value">${signal.ml_score.toFixed(3)}</span>
                        </div>
                        <div class="detail-item">
                            Вероятность: <span class="detail-value">${signal.success_probability.toFixed(1)}%</span>
                        </div>
                        <div class="detail-item">
                            Вход: <span class="detail-value">$${signal.entry_price.toFixed(2)}</span>
                        </div>
                        <div class="detail-item">
                            Цель: <span class="detail-value">$${signal.target_price.toFixed(2)}</span>
                        </div>
                        <div class="detail-item">
                            Канал: <span class="detail-value">${signal.channel}</span>
                        </div>
                        <div class="detail-item">
                            Риск: <span class="detail-value">${signal.risk_level}</span>
                        </div>
                    </div>
                `;
                signalsContainer.appendChild(signalCard);
            });
            
            // Отображение статистики
            statsContainer.innerHTML = `
                <h3>📈 Статистика</h3>
                <div class="signal-details">
                    <div class="detail-item">
                        Всего сигналов: <span class="detail-value">${data.stats.total_signals}</span>
                    </div>
                    <div class="detail-item">
                        Высокая уверенность: <span class="detail-value">${data.stats.high_confidence}</span>
                    </div>
                    <div class="detail-item">
                        Средняя вероятность: <span class="detail-value">${data.stats.avg_success_rate.toFixed(1)}%</span>
                    </div>
                    <div class="detail-item">
                        Время анализа: <span class="detail-value">${data.stats.processing_time.toFixed(1)}s</span>
                    </div>
                </div>
            `;
            
            resultsDiv.style.display = 'block';
        }

        function clearResults() {
            document.getElementById('results').style.display = 'none';
            logContainer.innerHTML = '';
            addLogEntry('🗑️ Результаты очищены');
        }

        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            addLogEntry('🌐 Веб-интерфейс инициализирован');
            addLogEntry('✅ Готов к работе');
        });
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_analysis(self):
        """API для анализа сигналов"""
        # Симуляция анализа
        time.sleep(0.5)  # Имитация времени обработки
        
        # Генерация тестовых данных
        signals = [
            {
                "asset": "BTCUSDT",
                "direction": "LONG",
                "recommendation": "СИЛЬНАЯ ПОКУПКА",
                "recommendation_class": "strong-buy",
                "ml_score": 0.840 + random.uniform(-0.05, 0.05),
                "success_probability": 75.6 + random.uniform(-5, 5),
                "entry_price": 43250.00 + random.uniform(-100, 100),
                "target_price": 45000.00 + random.uniform(-100, 100),
                "stop_price": 42000.00 + random.uniform(-50, 50),
                "channel": "Crypto Signals Pro",
                "risk_level": "НИЗКИЙ"
            },
            {
                "asset": "SOLUSDT",
                "direction": "LONG",
                "recommendation": "СИЛЬНАЯ ПОКУПКА",
                "recommendation_class": "strong-buy",
                "ml_score": 0.817 + random.uniform(-0.05, 0.05),
                "success_probability": 73.5 + random.uniform(-5, 5),
                "entry_price": 98.50 + random.uniform(-2, 2),
                "target_price": 105.00 + random.uniform(-2, 2),
                "stop_price": 94.00 + random.uniform(-1, 1),
                "channel": "DeFi Trading Signals",
                "risk_level": "НИЗКИЙ"
            },
            {
                "asset": "ETHUSDT",
                "direction": "SHORT",
                "recommendation": "ПРОДАЖА",
                "recommendation_class": "sell",
                "ml_score": 0.774 + random.uniform(-0.05, 0.05),
                "success_probability": 69.7 + random.uniform(-5, 5),
                "entry_price": 2580.00 + random.uniform(-20, 20),
                "target_price": 2450.00 + random.uniform(-20, 20),
                "stop_price": 2650.00 + random.uniform(-10, 10),
                "channel": "Binance Trading Signals",
                "risk_level": "СРЕДНИЙ"
            }
        ]
        
        # Статистика
        high_confidence = len([s for s in signals if s['success_probability'] > 70])
        avg_success_rate = sum(s['success_probability'] for s in signals) / len(signals)
        
        response_data = {
            "signals": signals,
            "stats": {
                "total_signals": len(signals),
                "high_confidence": high_confidence,
                "avg_success_rate": avg_success_rate,
                "processing_time": 1.5 + random.uniform(-0.3, 0.3)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
    
    def serve_status(self):
        """API статуса системы"""
        status_data = {
            "status": "online",
            "version": "0.4.2",
            "services": {
                "telegram": "active",
                "parser": "active",
                "ml_service": "active",
                "database": "active"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(status_data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Переопределение логирования для более чистого вывода"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {format % args}")

def run_server(port=8080):
    """Запуск веб-сервера"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, CryptoAnalyticsHandler)
    
    print("=" * 60)
    print("🚀 CRYPTO ANALYTICS PLATFORM - WEB DEMO")
    print("=" * 60)
    print(f"🌐 Сервер запущен на http://localhost:{port}")
    print("📋 Задача 0.4.2 - Веб-интерфейс для демонстрации")
    print("🔗 Откройте браузер и перейдите по адресу выше")
    print("=" * 60)
    print("Нажмите Ctrl+C для остановки сервера")
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
        httpd.server_close()

if __name__ == "__main__":
    run_server() 