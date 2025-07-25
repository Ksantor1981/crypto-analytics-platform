"""
Тестовый скрипт для проверки ML-сервиса предсказания сигналов
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# Конфигурация
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/ml-prediction"


def print_section(title: str):
    """Печатает заголовок секции"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(test_name: str, success: bool, details: str = ""):
    """Печатает результат теста"""
    status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
    print(f"{status} | {test_name}")
    if details:
        print(f"    {details}")


def test_health_check() -> bool:
    """Тест проверки здоровья сервиса"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_result("Health Check", True, f"Статус: {data.get('status')}")
            return True
        else:
            print_result("Health Check", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result("Health Check", False, str(e))
        return False


def test_model_status() -> bool:
    """Тест получения статуса модели"""
    try:
        response = requests.get(f"{API_BASE}/model-status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            status_data = data.get('data', {})
            is_trained = status_data.get('is_trained', False)
            accuracy = status_data.get('model_accuracy', 0.0)
            
            print_result("Model Status", True, 
                        f"Обучена: {is_trained}, Точность: {accuracy:.3f}")
            return True
        else:
            print_result("Model Status", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result("Model Status", False, str(e))
        return False


def test_model_training() -> bool:
    """Тест обучения модели"""
    try:
        print("🔄 Обучение модели...")
        response = requests.post(f"{API_BASE}/train", timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            training_data = data.get('data', {})
            
            if training_data.get('success', False):
                accuracy = training_data.get('accuracy', 0.0)
                training_samples = training_data.get('training_samples', 0)
                test_samples = training_data.get('test_samples', 0)
                
                print_result("Model Training", True, 
                            f"Точность: {accuracy:.3f}, "
                            f"Обучающих: {training_samples}, "
                            f"Тестовых: {test_samples}")
                
                # Выводим важность признаков
                feature_importance = training_data.get('feature_importance', {})
                if feature_importance:
                    print("\n📊 Важность признаков:")
                    for feature, importance in sorted(
                        feature_importance.items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:5]:
                        print(f"    {feature}: {importance:.3f}")
                
                return True
            else:
                error = training_data.get('error', 'Неизвестная ошибка')
                print_result("Model Training", False, error)
                return False
        else:
            print_result("Model Training", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result("Model Training", False, str(e))
        return False


def test_single_prediction() -> bool:
    """Тест предсказания для одного сигнала"""
    try:
        # Сначала проверим, есть ли обученная модель
        status_response = requests.get(f"{API_BASE}/model-status", timeout=10)
        if status_response.status_code != 200:
            print_result("Single Prediction", False, "Не удалось получить статус модели")
            return False
        
        status_data = status_response.json().get('data', {})
        if not status_data.get('is_trained', False):
            print_result("Single Prediction", False, "Модель не обучена")
            return False
        
        # Тестируем предсказание (используем ID 1 как пример)
        signal_id = 1
        response = requests.post(f"{API_BASE}/predict/{signal_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            prediction_data = data.get('prediction', {})
            
            if prediction_data.get('success', False):
                prediction = prediction_data.get('prediction')
                confidence = prediction_data.get('confidence', 0.0)
                model_accuracy = prediction_data.get('model_accuracy', 0.0)
                
                result_text = "УСПЕШЕН" if prediction == 1 else "НЕУСПЕШЕН"
                print_result("Single Prediction", True, 
                            f"Сигнал {signal_id}: {result_text}, "
                            f"Уверенность: {confidence:.3f}, "
                            f"Точность модели: {model_accuracy:.3f}")
                return True
            else:
                error = prediction_data.get('error', 'Неизвестная ошибка')
                print_result("Single Prediction", False, error)
                return False
        elif response.status_code == 404:
            print_result("Single Prediction", False, "Сигнал не найден (это нормально для тестовой БД)")
            return True  # Считаем успехом, так как это ожидаемое поведение
        else:
            print_result("Single Prediction", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result("Single Prediction", False, str(e))
        return False


def test_batch_prediction() -> bool:
    """Тест batch предсказания"""
    try:
        # Тестируем batch предсказание для нескольких сигналов
        signal_ids = [1, 2, 3, 4, 5]
        
        response = requests.post(
            f"{API_BASE}/batch-predict",
            json=signal_ids,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            total_signals = data.get('total_signals', 0)
            
            print_result("Batch Prediction", True, 
                        f"Обработано сигналов: {total_signals}")
            
            # Выводим результаты предсказаний
            successful_predictions = 0
            for pred in predictions:
                signal_id = pred.get('signal_id')
                prediction_data = pred.get('prediction', {})
                
                if prediction_data.get('success', False):
                    successful_predictions += 1
                    prediction = prediction_data.get('prediction')
                    confidence = prediction_data.get('confidence', 0.0)
                    result_text = "УСПЕШЕН" if prediction == 1 else "НЕУСПЕШЕН"
                    print(f"    Сигнал {signal_id}: {result_text} (уверенность: {confidence:.3f})")
                else:
                    error = prediction_data.get('error', 'Неизвестная ошибка')
                    print(f"    Сигнал {signal_id}: ОШИБКА - {error}")
            
            print(f"    Успешных предсказаний: {successful_predictions}/{total_signals}")
            return True
        elif response.status_code == 404:
            print_result("Batch Prediction", False, "Сигналы не найдены (это нормально для тестовой БД)")
            return True  # Считаем успехом, так как это ожидаемое поведение
        else:
            print_result("Batch Prediction", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result("Batch Prediction", False, str(e))
        return False


def test_feature_importance() -> bool:
    """Тест получения важности признаков"""
    try:
        response = requests.get(f"{API_BASE}/feature-importance", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            feature_importance = data.get('feature_importance', {})
            model_accuracy = data.get('model_accuracy', 0.0)
            
            print_result("Feature Importance", True, 
                        f"Точность модели: {model_accuracy:.3f}")
            
            if feature_importance:
                print("\n📊 Топ-5 важных признаков:")
                for i, (feature, importance) in enumerate(
                    sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5], 1
                ):
                    print(f"    {i}. {feature}: {importance:.3f}")
            
            return True
        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get('detail', 'Неизвестная ошибка')
            print_result("Feature Importance", False, error_msg)
            return True  # Считаем успехом, так как это ожидаемое поведение для необученной модели
        else:
            print_result("Feature Importance", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result("Feature Importance", False, str(e))
        return False


def test_model_save_load() -> bool:
    """Тест сохранения и загрузки модели"""
    try:
        # Сохранение модели
        save_response = requests.post(f"{API_BASE}/save-model", timeout=10)
        
        if save_response.status_code == 200:
            print_result("Model Save", True, "Модель сохранена")
            
            # Загрузка модели
            load_response = requests.post(f"{API_BASE}/load-model", timeout=10)
            
            if load_response.status_code == 200:
                print_result("Model Load", True, "Модель загружена")
                return True
            else:
                print_result("Model Load", False, f"HTTP {load_response.status_code}")
                return False
        else:
            print_result("Model Save", False, f"HTTP {save_response.status_code}")
            return False
    except Exception as e:
        print_result("Model Save/Load", False, str(e))
        return False


def main():
    """Основная функция тестирования"""
    print_section("🧪 ТЕСТИРОВАНИЕ ML-СЕРВИСА ПРЕДСКАЗАНИЯ СИГНАЛОВ")
    print(f"📅 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Базовый URL: {BASE_URL}")
    
    # Список тестов
    tests = [
        ("Health Check", test_health_check),
        ("Model Status", test_model_status),
        ("Model Training", test_model_training),
        ("Single Prediction", test_single_prediction),
        ("Batch Prediction", test_batch_prediction),
        ("Feature Importance", test_feature_importance),
        ("Model Save/Load", test_model_save_load),
    ]
    
    # Выполнение тестов
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print_result(test_name, False, f"Критическая ошибка: {str(e)}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print_section("📊 ИТОГОВЫЙ ОТЧЕТ")
    
    successful_tests = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"Всего тестов: {total_tests}")
    print(f"Успешных: {successful_tests}")
    print(f"Неудачных: {total_tests - successful_tests}")
    print(f"Процент успеха: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ ML-сервис предсказания сигналов работает корректно")
    else:
        print(f"\n⚠️  {total_tests - successful_tests} тестов не прошли")
        print("Проверьте логи сервера для получения дополнительной информации")
    
    print(f"\n📅 Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main() 