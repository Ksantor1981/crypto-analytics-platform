import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1/signal-predictions"

def print_response(name, response):
    """Красиво печатает ответ от API."""
    print(f"--- {name} ---")
    try:
        print(f"Status Code: {response.status_code}")
        print(f"Response JSON: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except (json.JSONDecodeError, AttributeError):
        print(f"Response Text: {response.text}")
    print("-" * (len(name) + 8) + "\\n")

def run_test():
    """Запускает последовательность тестовых вызовов к API."""
    # 1. Запустить обучение модели
    print("Шаг 1: Запуск обучения модели...")
    try:
        train_response = requests.post(f"{BASE_URL}/train", timeout=60)
        print_response("Train Model", train_response)

        if train_response.status_code != 200:
            print(f"Обучение не удалось (статус {train_response.status_code}). Тест прерван.")
            return

        response_json = train_response.json()
        if response_json.get('status') != 'success':
            print(f"Обучение не удалось (статус: {response_json.get('status')}, сообщение: {response_json.get('message')}). Тест прерван.")
            return

    except requests.exceptions.RequestException as e:
        print(f"Не удалось подключиться к серверу для обучения: {e}")
        return

    # 2. Проверить статус модели
    print("Шаг 2: Проверка статуса модели...")
    try:
        status_response = requests.get(f"{BASE_URL}/model-status")
        print_response("Model Status", status_response)

        if not status_response.json().get('model_trained'):
            print("Модель не обучена. Тест прерван.")
            return
    except requests.exceptions.RequestException as e:
        print(f"Не удалось получить статус модели: {e}")
        return

    # 3. Получить предсказание для одного сигнала (предполагаем, что сигнал с ID=1 существует)
    print("Шаг 3: Предсказание для одного сигнала (ID=1)...")
    try:
        predict_payload = {"signal_id": 1}
        predict_response = requests.post(f"{BASE_URL}/predict", json=predict_payload)
        print_response("Single Prediction", predict_response)
    except requests.exceptions.RequestException as e:
        print(f"Не удалось получить предсказание для одного сигнала: {e}")


    # 4. Получить предсказание для нескольких сигналов
    print("Шаг 4: Пакетное предсказание для сигналов (ID=1, 2, 3)...")
    try:
        batch_payload = {"signal_ids": [1, 2, 3]}
        batch_response = requests.post(f"{BASE_URL}/batch-predict", json=batch_payload)
        print_response("Batch Prediction", batch_response)
    except requests.exceptions.RequestException as e:
        print(f"Не удалось получить пакетное предсказание: {e}")


if __name__ == "__main__":
    print("Запуск теста для Signal Prediction Service через 3 секунды...")
    print("Убедитесь, что FastAPI сервер запущен и в таблице 'signal_results' есть данные.")
    time.sleep(3)
    run_test()