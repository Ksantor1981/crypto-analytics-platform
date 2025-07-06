"""
Интеграция Telegram коллектора с Backend API
Отправляет собранные сигналы в основную систему
"""
import asyncio
import aiohttp
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BackendIntegration:
    """Интеграция с Backend API для отправки сигналов"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url.rstrip('/')
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def test_connection(self) -> bool:
        """Тестирование соединения с backend"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            async with self.session.get(f"{self.backend_url}/health") as response:
                if response.status == 200:
                    logger.info("✅ Соединение с backend установлено")
                    return True
                else:
                    logger.error(f"❌ Backend недоступен: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Ошибка соединения с backend: {e}")
            return False
    
    async def send_signal(self, signal_data: Dict) -> bool:
        """Отправка одного сигнала в backend"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Преобразуем данные сигнала в формат API
            api_signal = self.convert_to_api_format(signal_data)
            
            async with self.session.post(
                f"{self.backend_url}/api/v1/signals/",
                json=api_signal,
                headers={'Content-Type': 'application/json'}
            ) as response:
                
                if response.status in [200, 201]:
                    logger.info(f"✅ Сигнал отправлен: {signal_data.get('coin', 'Unknown')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка отправки сигнала: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Исключение при отправке сигнала: {e}")
            return False
    
    async def send_signals_batch(self, signals: List[Dict]) -> Dict:
        """Отправка пакета сигналов"""
        results = {
            'total': len(signals),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for signal in signals:
            try:
                if await self.send_signal(signal):
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    
                # Небольшая задержка между запросами
                await asyncio.sleep(0.1)
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))
                logger.error(f"❌ Ошибка в пакетной отправке: {e}")
        
        logger.info(f"📊 Результаты пакетной отправки: {results['success']}/{results['total']} успешно")
        return results
    
    def convert_to_api_format(self, signal_data: Dict) -> Dict:
        """Преобразование данных сигнала в формат API"""
        
        # Извлекаем основные данные
        coin = signal_data.get('coin', '').upper()
        direction = signal_data.get('direction', 'LONG').upper()
        entry_price = self.parse_price(signal_data.get('entry'))
        target_price = self.parse_price(signal_data.get('target'))
        stop_loss = self.parse_price(signal_data.get('stop_loss'))
        
        # Формируем API объект
        api_signal = {
            "symbol": coin,
            "signal_type": direction.lower() if direction in ['LONG', 'SHORT'] else 'long',
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "confidence": signal_data.get('confidence', 0.5),
            "source": f"telegram_{signal_data.get('channel', 'unknown')}",
            "original_text": signal_data.get('original_text', ''),
            "metadata": {
                "telegram_channel": signal_data.get('channel'),
                "message_id": signal_data.get('message_id'),
                "message_date": signal_data.get('message_date'),
                "leverage": signal_data.get('leverage'),
                "extracted_at": datetime.utcnow().isoformat()
            }
        }
        
        # Удаляем None значения
        return {k: v for k, v in api_signal.items() if v is not None}
    
    def parse_price(self, price_str: Optional[str]) -> Optional[float]:
        """Парсинг цены из строки"""
        if not price_str:
            return None
            
        try:
            # Убираем лишние символы и конвертируем
            clean_price = str(price_str).replace(',', '.').strip()
            # Убираем символы валют
            clean_price = ''.join(c for c in clean_price if c.isdigit() or c == '.')
            return float(clean_price) if clean_price else None
        except (ValueError, TypeError):
            return None
    
    async def get_backend_stats(self) -> Optional[Dict]:
        """Получение статистики из backend"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            async with self.session.get(f"{self.backend_url}/api/v1/signals/stats") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"❌ Ошибка получения статистики: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Ошибка запроса статистики: {e}")
            return None

class TelegramToBackendBridge:
    """Мост между Telegram коллектором и Backend API"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.integration = BackendIntegration(backend_url)
        
    async def process_signals(self, signals: List[Dict]) -> Dict:
        """Обработка и отправка сигналов в backend"""
        async with self.integration as api:
            # Проверяем соединение
            if not await api.test_connection():
                return {"error": "Backend недоступен"}
            
            # Фильтруем и валидируем сигналы
            valid_signals = self.validate_signals(signals)
            
            if not valid_signals:
                return {"error": "Нет валидных сигналов для отправки"}
            
            # Отправляем пакетом
            results = await api.send_signals_batch(valid_signals)
            
            return results
    
    def validate_signals(self, signals: List[Dict]) -> List[Dict]:
        """Валидация сигналов перед отправкой"""
        valid_signals = []
        
        for signal in signals:
            # Проверяем обязательные поля
            if not signal.get('coin'):
                continue
                
            # Проверяем минимальную уверенность
            if signal.get('confidence', 0) < 0.3:
                continue
                
            # Проверяем наличие хотя бы entry или target
            if not (signal.get('entry') or signal.get('target')):
                continue
                
            valid_signals.append(signal)
        
        logger.info(f"✅ Валидация: {len(valid_signals)}/{len(signals)} сигналов прошли проверку")
        return valid_signals
    
    async def start_real_time_bridge(self, telegram_collector):
        """Запуск моста в реальном времени"""
        
        async def signal_callback(signal_data: Dict):
            """Callback для обработки новых сигналов"""
            try:
                async with self.integration as api:
                    await api.send_signal(signal_data)
            except Exception as e:
                logger.error(f"❌ Ошибка в real-time мосте: {e}")
        
        # Запускаем мониторинг с callback
        await telegram_collector.start_real_time_monitoring(callback=signal_callback)

# Утилита для быстрого тестирования интеграции
async def test_backend_integration():
    """Тестирование интеграции с backend"""
    
    # Тестовый сигнал
    test_signal = {
        'coin': 'BTCUSDT',
        'direction': 'LONG', 
        'entry': '45000',
        'target': '46000',
        'stop_loss': '44000',
        'confidence': 0.8,
        'channel': 'test_channel',
        'original_text': 'TEST SIGNAL BTC LONG ENTRY 45000 TARGET 46000 SL 44000',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    async with BackendIntegration() as api:
        # Тест соединения
        if await api.test_connection():
            logger.info("✅ Backend доступен")
            
            # Тест отправки сигнала
            success = await api.send_signal(test_signal)
            if success:
                logger.info("✅ Тестовый сигнал отправлен успешно")
            else:
                logger.error("❌ Ошибка отправки тестового сигнала")
                
            # Получение статистики
            stats = await api.get_backend_stats()
            if stats:
                logger.info(f"📊 Статистика backend: {stats}")
        else:
            logger.error("❌ Backend недоступен")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_backend_integration()) 