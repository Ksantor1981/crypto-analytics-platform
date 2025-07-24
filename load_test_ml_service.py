#!/usr/bin/env python3
"""
Нагрузочное тестирование ML-сервиса
"""
import requests
import threading
import time
from datetime import datetime

ML_SERVICE_URL = "http://localhost:8001/api/v1/predictions/predict"

TEST_DATA = [
    {"asset": "BTC", "entry_price": 50000, "direction": "LONG"},
    {"asset": "ETH", "entry_price": 3000, "direction": "LONG"},
    {"asset": "SOL", "entry_price": 100, "direction": "LONG"},
]

THREADS = 5
REQUESTS_PER_THREAD = 10

def make_requests(thread_id, results):
    for i in range(REQUESTS_PER_THREAD):
        data = TEST_DATA[i % len(TEST_DATA)]
        start = time.time()
        try:
            resp = requests.post(ML_SERVICE_URL, json=data, timeout=10)
            elapsed = time.time() - start
            results.append({
                "thread": thread_id,
                "status": resp.status_code,
                "elapsed": elapsed,
                "ok": resp.status_code == 200
            })
        except Exception as e:
            elapsed = time.time() - start
            results.append({
                "thread": thread_id,
                "status": "EXC",
                "elapsed": elapsed,
                "ok": False,
                "error": str(e)
            })

def main():
    print(f"🚀 Нагрузочное тестирование ML-сервиса ({THREADS*REQUESTS_PER_THREAD} запросов)...")
    results = []
    threads = []
    start_time = time.time()
    for t in range(THREADS):
        thread = threading.Thread(target=make_requests, args=(t, results))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    total_time = time.time() - start_time
    # Анализ результатов
    success = [r for r in results if r["ok"]]
    failed = [r for r in results if not r["ok"]]
    if success:
        avg_time = sum(r["elapsed"] for r in success) / len(success)
        max_time = max(r["elapsed"] for r in success)
        min_time = min(r["elapsed"] for r in success)
    else:
        avg_time = max_time = min_time = 0
    print(f"\n📊 Результаты:")
    print(f"  Всего запросов: {len(results)}")
    print(f"  Успешных: {len(success)}")
    print(f"  Ошибок: {len(failed)}")
    print(f"  Среднее время ответа: {avg_time:.3f} сек")
    print(f"  Макс. время: {max_time:.3f} сек")
    print(f"  Мин. время: {min_time:.3f} сек")
    print(f"  Общее время теста: {total_time:.2f} сек")
    if failed:
        print("\n❌ Ошибки:")
        for r in failed:
            print(f"  [Поток {r['thread']}] Статус: {r['status']} Время: {r['elapsed']:.3f} Ошибка: {r.get('error','')}")
    print("\n⏰ Время окончания:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

if __name__ == "__main__":
    main() 