#!/usr/bin/env python3
"""
Тест для проверки статуса серверов
"""

import asyncio
import httpx
import time
from typing import Dict, Any

async def check_server_status(url: str, service_name: str) -> Dict[str, Any]:
    """Проверка статуса сервера"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                return {
                    "service": service_name,
                    "status": "✅ РАБОТАЕТ",
                    "url": url,
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                }
            else:
                return {
                    "service": service_name,
                    "status": f"❌ ОШИБКА {response.status_code}",
                    "url": url,
                    "error": response.text
                }
    except Exception as e:
        return {
            "service": service_name,
            "status": "❌ НЕДОСТУПЕН",
            "url": url,
            "error": str(e)
        }

async def main():
    """Основная функция проверки"""
    print("🔍 Проверка статуса серверов...")
    print("=" * 60)
    
    # Список серверов для проверки
    servers = [
        ("http://localhost:8000/docs", "Backend API"),
        ("http://localhost:8001/docs", "ML Service"),
        ("http://localhost:8000/api/v1/health", "Backend Health"),
        ("http://localhost:8001/api/v1/health/", "ML Service Health")
    ]
    
    # Проверяем каждый сервер
    for url, service_name in servers:
        result = await check_server_status(url, service_name)
        
        print(f"📊 {result['service']}: {result['status']}")
        print(f"   URL: {result['url']}")
        
        if 'response_time' in result:
            print(f"   Время ответа: {result['response_time']:.3f}s")
        
        if 'error' in result:
            print(f"   Ошибка: {result['error']}")
        
        print()
        
        # Небольшая задержка между запросами
        await asyncio.sleep(0.5)
    
    print("=" * 60)
    print("✅ Проверка завершена")

if __name__ == "__main__":
    asyncio.run(main()) 