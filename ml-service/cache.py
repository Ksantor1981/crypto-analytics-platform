"""
Redis caching module for ML service
"""

import redis
import json
import hashlib
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class MLCache:
    """Кэш для ML результатов"""
    
    def __init__(self):
        """Инициализация подключения к Redis"""
        try:
            # Получаем настройки Redis из переменных окружения
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            redis_password = os.getenv('REDIS_PASSWORD')
            
            # Подключение к Redis
            if redis_password:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True
                )
            else:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True
                )
            
            # Проверяем подключение
            self.redis_client.ping()
            logger.info(f"✅ Redis cache connected to {redis_host}:{redis_port}")
            self.enabled = True
            
        except Exception as e:
            logger.warning(f"⚠️ Redis cache not available: {e}")
            self.enabled = False
            self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Генерация ключа кэша на основе данных"""
        # Сортируем ключи для консистентности
        sorted_data = json.dumps(data, sort_keys=True)
        # Создаем хеш от данных
        data_hash = hashlib.md5(sorted_data.encode()).hexdigest()
        return f"ml:{prefix}:{data_hash}"
    
    def get(self, prefix: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Получение данных из кэша"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(prefix, data)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                logger.info(f"✅ Cache hit for {prefix}")
                return result
            else:
                logger.info(f"❌ Cache miss for {prefix}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Cache get error: {e}")
            return None
    
    def set(self, prefix: str, data: Dict[str, Any], result: Dict[str, Any], 
            ttl_seconds: int = 3600) -> bool:
        """Сохранение данных в кэш"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, data)
            
            # Добавляем метаданные к результату
            cached_result = {
                "data": result,
                "cached_at": datetime.now().isoformat(),
                "ttl_seconds": ttl_seconds,
                "cache_key": cache_key
            }
            
            # Сохраняем в Redis
            self.redis_client.setex(
                cache_key,
                ttl_seconds,
                json.dumps(cached_result)
            )
            
            logger.info(f"✅ Cached {prefix} for {ttl_seconds}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache set error: {e}")
            return False
    
    def invalidate(self, prefix: str, data: Dict[str, Any]) -> bool:
        """Инвалидация кэша"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, data)
            self.redis_client.delete(cache_key)
            logger.info(f"✅ Invalidated cache for {prefix}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache invalidation error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            # Получаем все ключи кэша
            keys = self.redis_client.keys("ml:*")
            
            # Подсчитываем по префиксам
            stats = {}
            for key in keys:
                prefix = key.split(":")[1] if ":" in key else "unknown"
                stats[prefix] = stats.get(prefix, 0) + 1
            
            return {
                "enabled": True,
                "total_keys": len(keys),
                "prefixes": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Cache stats error: {e}")
            return {"enabled": False, "error": str(e)}

# Глобальный экземпляр кэша
ml_cache = MLCache()

def cache_prediction(ttl_seconds: int = 3600):
    """Декоратор для кэширования предсказаний"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Извлекаем данные запроса
            request_data = None
            for arg in args:
                if hasattr(arg, 'dict'):
                    request_data = arg.dict()
                    break
            
            if not request_data:
                return await func(*args, **kwargs)
            
            # Пытаемся получить из кэша
            cached_result = ml_cache.get("prediction", request_data)
            if cached_result:
                return cached_result["data"]
            
            # Выполняем предсказание
            result = await func(*args, **kwargs)
            
            # Сохраняем в кэш
            if hasattr(result, 'dict'):
                ml_cache.set("prediction", request_data, result.dict(), ttl_seconds)
            
            return result
        
        return wrapper
    return decorator

def cache_market_data(ttl_seconds: int = 300):
    """Декоратор для кэширования рыночных данных"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Извлекаем asset из аргументов
            asset = None
            for arg in args:
                if isinstance(arg, str):
                    asset = arg
                    break
            
            if not asset:
                return await func(*args, **kwargs)
            
            request_data = {"asset": asset}
            
            # Пытаемся получить из кэша
            cached_result = ml_cache.get("market_data", request_data)
            if cached_result:
                return cached_result["data"]
            
            # Получаем данные
            result = await func(*args, **kwargs)
            
            # Сохраняем в кэш
            if isinstance(result, dict):
                ml_cache.set("market_data", request_data, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator
