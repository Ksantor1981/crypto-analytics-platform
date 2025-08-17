"""
Высокоточный OCR сервис для извлечения крипто-сигналов из изображений
Основан на готовой модели из предыдущего проекта analyst_crypto
"""
import os
import re
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import base64
import io

# OCR библиотеки
try:
    import easyocr
    import cv2
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("OCR библиотеки не установлены. Установите: pip install easyocr opencv-python pillow")

# NLP для анализа текста
try:
    import spacy
    from spacy.matcher import Matcher
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    logging.warning("NLP библиотеки не установлены. Установите: pip install spacy")

from sqlalchemy.orm import Session
from ..models.signal import Signal, SignalDirection
from ..models.channel import Channel
from ..schemas.signal import SignalCreate
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class AdvancedOCRService:
    """
    Высокоточный OCR сервис для извлечения крипто-сигналов из изображений
    Поддерживает готовую модель из предыдущего проекта
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        
        # Инициализация OCR
        self.reader = None
        self.nlp = None
        self.matcher = None
        
        # Поддерживаемые языки для OCR
        self.languages = ['en', 'ru']  # Английский и русский
        
        # Паттерны для распознавания сигналов
        self.signal_patterns = {
            'long': [
                r'(?i)(long|buy|bullish|moon|pump|🚀|📈).*?(\w+usdt).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
                r'(?i)(\w+usdt).*?(long|buy|bullish).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
                r'(?i)вход.*?(\w+usdt).*?(лонг|покупка).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
            ],
            'short': [
                r'(?i)(short|sell|bearish|dump|crash|📉|🔻).*?(\w+usdt).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
                r'(?i)(\w+usdt).*?(short|sell|bearish).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
                r'(?i)вход.*?(\w+usdt).*?(шорт|продажа).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
            ]
        }
        
        # Поддерживаемые торговые пары
        self.supported_pairs = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
            'DOT/USDT', 'MATIC/USDT', 'AVAX/USDT', 'LINK/USDT', 'UNI/USDT',
            'SHIB/USDT', 'DOGE/USDT', 'PEPE/USDT', 'FLOKI/USDT', 'BONK/USDT',
            'WIF/USDT', 'BOME/USDT', 'MYRO/USDT', 'POPCAT/USDT', 'BOOK/USDT'
        ]
        
        # Инициализация компонентов
        self._initialize_ocr()
        self._initialize_nlp()
        
    def _initialize_ocr(self):
        """Инициализация OCR с готовой моделью"""
        if not OCR_AVAILABLE:
            logger.error("OCR библиотеки не установлены")
            return
            
        try:
            # Инициализация EasyOCR с готовой моделью
            # Если есть готовая модель из предыдущего проекта, загружаем её
            model_path = self._get_custom_model_path()
            
            if model_path and os.path.exists(model_path):
                logger.info(f"Загружаем готовую модель из: {model_path}")
                self.reader = easyocr.Reader(
                    self.languages,
                    model_storage_directory=model_path,
                    download_enabled=False
                )
            else:
                logger.info("Используем стандартную модель EasyOCR")
                self.reader = easyocr.Reader(
                    self.languages,
                    gpu=False,  # CPU для стабильности
                    download_enabled=True
                )
                
            logger.info("OCR инициализирован успешно")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации OCR: {e}")
            self.reader = None
    
    def _initialize_nlp(self):
        """Инициализация NLP для анализа текста"""
        if not NLP_AVAILABLE:
            logger.warning("NLP недоступен, используем только regex")
            return
            
        try:
            # Загружаем модель spaCy
            model_name = 'en_core_web_sm'
            try:
                self.nlp = spacy.load(model_name)
            except OSError:
                logger.warning(f"Модель {model_name} не найдена. Установите: python -m spacy download {model_name}")
                return
                
            # Создаем matcher для поиска паттернов
            self.matcher = Matcher(self.nlp.vocab)
            
            # Добавляем паттерны для крипто-сигналов
            patterns = [
                [{"LOWER": {"IN": ["long", "buy", "bullish", "moon", "pump"]}}],
                [{"LOWER": {"IN": ["short", "sell", "bearish", "dump", "crash"]}}],
                [{"LOWER": {"IN": ["btc", "eth", "bnb", "ada", "sol"]}}],
                [{"LOWER": {"IN": ["usdt", "usdc", "btc"]}}],
            ]
            
            for pattern in patterns:
                self.matcher.add("CRYPTO_SIGNAL", [pattern])
                
            logger.info("NLP инициализирован успешно")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации NLP: {e}")
            self.nlp = None
            self.matcher = None
    
    def _get_custom_model_path(self) -> Optional[str]:
        """Получение пути к готовой модели из предыдущего проекта"""
        # Возможные пути к готовой модели
        possible_paths = [
            "models/ocr_model",
            "assets/ocr_model", 
            "data/ocr_model",
            "../analyst_crypto/models/ocr_model",
            "../analyst_crypto/assets/ocr_model"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        return None
    
    async def extract_signals_from_image(
        self, 
        image_data: bytes, 
        channel_id: int,
        message_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Извлечение сигналов из изображения с высочайшей точностью
        
        Args:
            image_data: Байты изображения
            channel_id: ID канала
            message_id: ID сообщения
            
        Returns:
            Список извлеченных сигналов
        """
        if not self.reader:
            logger.error("OCR не инициализирован")
            return []
            
        try:
            # Предобработка изображения
            processed_image = await self._preprocess_image(image_data)
            
            # OCR распознавание
            ocr_results = await self._perform_ocr(processed_image)
            
            # Извлечение сигналов из текста
            signals = await self._extract_signals_from_text(ocr_results, channel_id, message_id)
            
            # Валидация и фильтрация сигналов
            validated_signals = await self._validate_extracted_signals(signals)
            
            logger.info(f"Извлечено {len(validated_signals)} сигналов из изображения")
            return validated_signals
            
        except Exception as e:
            logger.error(f"Ошибка извлечения сигналов из изображения: {e}")
            return []
    
    async def _preprocess_image(self, image_data: bytes) -> np.ndarray:
        """Предобработка изображения для улучшения OCR точности"""
        try:
            # Конвертируем байты в PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Конвертируем в RGB если нужно
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Улучшение контраста
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Улучшение резкости
            image = image.filter(ImageFilter.SHARPEN)
            
            # Увеличение размера для лучшего распознавания
            width, height = image.size
            if width < 800 or height < 600:
                scale_factor = max(800/width, 600/height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Конвертируем в numpy array
            image_array = np.array(image)
            
            # Конвертируем в BGR для OpenCV
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Дополнительная обработка OpenCV
            # Удаление шума
            denoised = cv2.fastNlMeansDenoisingColored(image_bgr, None, 10, 10, 7, 21)
            
            # Улучшение контраста
            lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            cl = clahe.apply(l)
            enhanced = cv2.merge((cl,a,b))
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Ошибка предобработки изображения: {e}")
            # Возвращаем оригинальное изображение
            image = Image.open(io.BytesIO(image_data))
            return np.array(image)
    
    async def _perform_ocr(self, image: np.ndarray) -> List[Tuple[str, float]]:
        """Выполнение OCR с высокой точностью"""
        try:
            # OCR распознавание
            results = self.reader.readtext(image)
            
            # Фильтрация результатов по уверенности
            filtered_results = []
            for (bbox, text, confidence) in results:
                # Минимальная уверенность 0.6
                if confidence > 0.6:
                    # Очистка текста
                    cleaned_text = self._clean_ocr_text(text)
                    if cleaned_text:
                        filtered_results.append((cleaned_text, confidence))
            
            # Сортировка по уверенности
            filtered_results.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"OCR распознал {len(filtered_results)} текстовых блоков")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Ошибка OCR распознавания: {e}")
            return []
    
    def _clean_ocr_text(self, text: str) -> str:
        """Очистка текста от OCR артефактов"""
        if not text:
            return ""
            
        # Удаление лишних пробелов
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Исправление частых OCR ошибок
        corrections = {
            '0': 'O',  # Ноль часто путают с буквой O
            '1': 'l',  # Единица с буквой l
            '5': 'S',  # Пятерка с буквой S
            '8': 'B',  # Восьмерка с буквой B
            '|': 'I',  # Вертикальная черта с буквой I
        }
        
        # Применяем исправления только в контексте крипто-символов
        for wrong, correct in corrections.items():
            # Исправляем только если это похоже на крипто-символ
            if re.search(rf'\b\w*{wrong}\w*\b', text, re.IGNORECASE):
                text = re.sub(rf'\b(\w*){wrong}(\w*)\b', rf'\1{correct}\2', text, flags=re.IGNORECASE)
        
        return text
    
    async def _extract_signals_from_text(
        self, 
        ocr_results: List[Tuple[str, float]], 
        channel_id: int,
        message_id: str
    ) -> List[Dict[str, Any]]:
        """Извлечение сигналов из распознанного текста"""
        signals = []
        
        # Объединяем весь текст
        full_text = " ".join([text for text, _ in ocr_results])
        
        # Анализируем с помощью NLP если доступен
        if self.nlp and self.matcher:
            nlp_signals = await self._extract_signals_with_nlp(full_text, channel_id, message_id)
            signals.extend(nlp_signals)
        
        # Анализируем с помощью regex паттернов
        regex_signals = await self._extract_signals_with_regex(full_text, channel_id, message_id)
        signals.extend(regex_signals)
        
        # Удаляем дубликаты
        unique_signals = self._remove_duplicate_signals(signals)
        
        return unique_signals
    
    async def _extract_signals_with_nlp(
        self, 
        text: str, 
        channel_id: int,
        message_id: str
    ) -> List[Dict[str, Any]]:
        """Извлечение сигналов с помощью NLP"""
        signals = []
        
        try:
            doc = self.nlp(text)
            matches = self.matcher(doc)
            
            for match_id, start, end in matches:
                span = doc[start:end]
                
                # Ищем торговую пару рядом с найденным паттерном
                pair = self._find_trading_pair_near_span(doc, start, end)
                if not pair:
                    continue
                
                # Определяем направление
                direction = self._determine_direction_from_span(span.text)
                if not direction:
                    continue
                
                # Ищем цены
                prices = self._extract_prices_from_context(doc, start, end)
                if len(prices) < 3:  # Нужны entry, target, stop
                    continue
                
                signal = {
                    'trading_pair': pair,
                    'direction': direction,
                    'entry_price': prices[0],
                    'target_price': prices[1],
                    'stop_loss': prices[2],
                    'confidence': 0.8,  # Высокая уверенность для NLP
                    'source': 'ocr_nlp',
                    'channel_id': channel_id,
                    'message_id': message_id,
                    'extracted_at': datetime.utcnow()
                }
                
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Ошибка NLP анализа: {e}")
            
        return signals
    
    async def _extract_signals_with_regex(
        self, 
        text: str, 
        channel_id: int,
        message_id: str
    ) -> List[Dict[str, Any]]:
        """Извлечение сигналов с помощью regex паттернов"""
        signals = []
        
        for direction, patterns in self.signal_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    try:
                        groups = match.groups()
                        
                        if len(groups) >= 5:
                            # Извлекаем данные из групп
                            action = groups[0].lower()
                            pair = groups[1].upper()
                            entry_price = float(groups[2])
                            target_price = float(groups[3])
                            stop_loss = float(groups[4])
                            
                            # Валидируем торговую пару
                            if not self._is_valid_trading_pair(pair):
                                continue
                            
                            # Определяем направление
                            signal_direction = self._determine_direction(action)
                            if not signal_direction:
                                continue
                            
                            signal = {
                                'trading_pair': pair,
                                'direction': signal_direction,
                                'entry_price': entry_price,
                                'target_price': target_price,
                                'stop_loss': stop_loss,
                                'confidence': 0.7,  # Средняя уверенность для regex
                                'source': 'ocr_regex',
                                'channel_id': channel_id,
                                'message_id': message_id,
                                'extracted_at': datetime.utcnow()
                            }
                            
                            signals.append(signal)
                            
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Ошибка парсинга regex match: {e}")
                        continue
        
        return signals
    
    def _find_trading_pair_near_span(self, doc, start: int, end: int) -> Optional[str]:
        """Поиск торговой пары рядом с найденным паттерном"""
        # Ищем в окне ±5 токенов
        search_start = max(0, start - 5)
        search_end = min(len(doc), end + 5)
        
        for i in range(search_start, search_end):
            token = doc[i].text.upper()
            
            # Проверяем на торговую пару
            if self._is_valid_trading_pair(token):
                return token
                
            # Проверяем комбинацию токенов
            if i < len(doc) - 1:
                combined = f"{token}/{doc[i+1].text.upper()}"
                if self._is_valid_trading_pair(combined):
                    return combined
        
        return None
    
    def _determine_direction_from_span(self, span_text: str) -> Optional[str]:
        """Определение направления из span текста"""
        span_lower = span_text.lower()
        
        if any(word in span_lower for word in ['long', 'buy', 'bullish', 'moon', 'pump']):
            return 'LONG'
        elif any(word in span_lower for word in ['short', 'sell', 'bearish', 'dump', 'crash']):
            return 'SHORT'
            
        return None
    
    def _extract_prices_from_context(self, doc, start: int, end: int) -> List[float]:
        """Извлечение цен из контекста"""
        prices = []
        
        # Ищем числа в окне ±10 токенов
        search_start = max(0, start - 10)
        search_end = min(len(doc), end + 10)
        
        for i in range(search_start, search_end):
            token = doc[i].text
            
            # Ищем числа
            if re.match(r'^\d+\.?\d*$', token):
                try:
                    price = float(token)
                    if 0.000001 <= price <= 1000000:  # Разумный диапазон цен
                        prices.append(price)
                except ValueError:
                    continue
        
        return sorted(prices)[:3]  # Возвращаем первые 3 цены
    
    def _is_valid_trading_pair(self, pair: str) -> bool:
        """Проверка валидности торговой пары"""
        # Нормализуем пару
        pair = pair.upper().replace('/', '')
        
        # Проверяем известные пары
        for known_pair in self.supported_pairs:
            if pair in known_pair.replace('/', ''):
                return True
        
        # Проверяем паттерн крипто/USDT
        if re.match(r'^[A-Z]{2,10}USDT$', pair):
            return True
            
        return False
    
    def _determine_direction(self, action: str) -> Optional[str]:
        """Определение направления сигнала"""
        action_lower = action.lower()
        
        if any(word in action_lower for word in ['long', 'buy', 'bullish', 'moon', 'pump', 'лонг', 'покупка']):
            return 'LONG'
        elif any(word in action_lower for word in ['short', 'sell', 'bearish', 'dump', 'crash', 'шорт', 'продажа']):
            return 'SHORT'
            
        return None
    
    def _remove_duplicate_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Удаление дубликатов сигналов"""
        unique_signals = []
        seen = set()
        
        for signal in signals:
            # Создаем ключ для сравнения
            key = (
                signal['trading_pair'],
                signal['direction'],
                round(signal['entry_price'], 6),
                round(signal['target_price'], 6),
                round(signal['stop_loss'], 6)
            )
            
            if key not in seen:
                seen.add(key)
                unique_signals.append(signal)
        
        return unique_signals
    
    async def _validate_extracted_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Валидация извлеченных сигналов"""
        validated_signals = []
        
        for signal in signals:
            try:
                # Проверяем обязательные поля
                required_fields = ['trading_pair', 'direction', 'entry_price', 'target_price', 'stop_loss']
                if not all(field in signal for field in required_fields):
                    continue
                
                # Проверяем валидность цен
                if not (0.000001 <= signal['entry_price'] <= 1000000):
                    continue
                if not (0.000001 <= signal['target_price'] <= 1000000):
                    continue
                if not (0.000001 <= signal['stop_loss'] <= 1000000):
                    continue
                
                # Проверяем логику цен
                if signal['direction'] == 'LONG':
                    if signal['target_price'] <= signal['entry_price']:
                        continue
                    if signal['stop_loss'] >= signal['entry_price']:
                        continue
                else:  # SHORT
                    if signal['target_price'] >= signal['entry_price']:
                        continue
                    if signal['stop_loss'] <= signal['entry_price']:
                        continue
                
                # Добавляем дополнительную информацию
                signal['leverage'] = 1.0  # По умолчанию
                signal['risk_reward_ratio'] = abs(
                    (signal['target_price'] - signal['entry_price']) / 
                    (signal['entry_price'] - signal['stop_loss'])
                )
                
                validated_signals.append(signal)
                
            except Exception as e:
                logger.warning(f"Ошибка валидации сигнала: {e}")
                continue
        
        return validated_signals
    
    async def save_extracted_signals(self, signals: List[Dict[str, Any]]) -> List[Signal]:
        """Сохранение извлеченных сигналов в базу данных"""
        saved_signals = []
        
        for signal_data in signals:
            try:
                # Создаем объект сигнала
                signal_create = SignalCreate(
                    trading_pair=signal_data['trading_pair'],
                    direction=SignalDirection.LONG if signal_data['direction'] == 'LONG' else SignalDirection.SHORT,
                    entry_price=signal_data['entry_price'],
                    target_price=signal_data['target_price'],
                    stop_loss=signal_data['stop_loss'],
                    leverage=signal_data.get('leverage', 1.0),
                    confidence=signal_data.get('confidence', 0.7),
                    source='ocr',
                    channel_id=signal_data['channel_id'],
                    message_id=signal_data.get('message_id'),
                    extracted_at=signal_data.get('extracted_at', datetime.utcnow())
                )
                
                # Создаем сигнал в базе
                signal = Signal(**signal_create.dict())
                self.db.add(signal)
                self.db.commit()
                self.db.refresh(signal)
                
                saved_signals.append(signal)
                
            except Exception as e:
                logger.error(f"Ошибка сохранения сигнала: {e}")
                self.db.rollback()
                continue
        
        return saved_signals
    
    async def get_ocr_statistics(self) -> Dict[str, Any]:
        """Получение статистики OCR работы"""
        try:
            # Статистика извлеченных сигналов
            total_signals = self.db.query(Signal).filter(Signal.source == 'ocr').count()
            
            # Статистика по каналам
            channel_stats = self.db.query(
                Signal.channel_id,
                Channel.name,
                self.db.func.count(Signal.id).label('signal_count'),
                self.db.func.avg(Signal.confidence).label('avg_confidence')
            ).join(Channel).filter(
                Signal.source == 'ocr'
            ).group_by(Signal.channel_id, Channel.name).all()
            
            return {
                'total_ocr_signals': total_signals,
                'channel_statistics': [
                    {
                        'channel_id': stat.channel_id,
                        'channel_name': stat.name,
                        'signal_count': stat.signal_count,
                        'avg_confidence': float(stat.avg_confidence) if stat.avg_confidence else 0.0
                    }
                    for stat in channel_stats
                ],
                'ocr_available': OCR_AVAILABLE,
                'nlp_available': NLP_AVAILABLE,
                'model_loaded': self.reader is not None
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения OCR статистики: {e}")
            return {
                'total_ocr_signals': 0,
                'channel_statistics': [],
                'ocr_available': OCR_AVAILABLE,
                'nlp_available': NLP_AVAILABLE,
                'model_loaded': self.reader is not None
            }
