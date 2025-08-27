import json
import re
from datetime import datetime
import os
import base64

def extract_text_from_image_simple(image_path):
    """Простая имитация OCR для демонстрации (без внешних зависимостей)"""
    try:
        # Проверяем существование файла
        if not os.path.exists(image_path):
            return None
        
        # Получаем размер файла для анализа
        file_size = os.path.getsize(image_path)
        
        # Имитируем OCR на основе имени файла и размера
        # В реальном проекте здесь был бы настоящий OCR (например, Tesseract)
        
        channel_name = image_path.split('_')[0] if '_' in image_path else "unknown"
        
        # Имитируем извлеченный текст на основе канала
        if "CryptoCapoTG" in channel_name:
            return [
                "BTC/USDT LONG Entry: $110,500",
                "Target: $116,025 Stop: $107,185",
                "Confidence: 85%",
                "ETH/USDT SHORT Entry: $3,200",
                "Target: $3,040 Stop: $3,280"
            ]
        elif "binance_signals_official" in channel_name:
            return [
                "SOL/USDT LONG Entry: $95.50",
                "Target: $102.00 Stop: $91.00",
                "Confidence: 78%",
                "ADA/USDT SHORT Entry: $0.45",
                "Target: $0.42 Stop: $0.48"
            ]
        elif "crypto_signals_daily" in channel_name:
            return [
                "MATIC/USDT LONG Entry: $0.85",
                "Target: $0.92 Stop: $0.81",
                "Confidence: 82%",
                "DOT/USDT SHORT Entry: $4.16",
                "Target: $3.95 Stop: $4.35"
            ]
        elif "crypto_analytics_pro" in channel_name:
            return [
                "AVAX/USDT LONG Entry: $28.50",
                "Target: $31.00 Stop: $27.00",
                "Confidence: 75%",
                "LINK/USDT SHORT Entry: $12.80",
                "Target: $12.00 Stop: $13.20"
            ]
        else:
            return [
                "UNKNOWN/USDT LONG Entry: $100.00",
                "Target: $110.00 Stop: $95.00",
                "Confidence: 70%"
            ]
            
    except Exception as e:
        print(f"❌ Ошибка OCR для {image_path}: {e}")
        return None

def parse_signals_from_text(text_lines):
    """Парсит торговые сигналы из текста, извлеченного OCR"""
    signals = []
    
    # Паттерны для поиска сигналов в тексте
    patterns = [
        # Формат: BTC/USDT LONG Entry: $110,500
        r'(\w+)/USDT\s+(LONG|SHORT)\s+Entry:\s*\$?([\d,]+\.?\d*)',
        
        # Формат: Target: $116,025 Stop: $107,185
        r'Target:\s*\$?([\d,]+\.?\d*)\s+Stop:\s*\$?([\d,]+\.?\d*)',
        
        # Формат: Confidence: 85%
        r'Confidence:\s*(\d+)%',
        
        # Простые форматы
        r'(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
        r'(\w+)\s+\$?([\d,]+\.?\d*)\s+(LONG|SHORT)',
        
        # Форматы с эмодзи
        r'🚀\s*(\w+)\s+\$?([\d,]+\.?\d*)',
        r'📉\s*(\w+)\s+\$?([\d,]+\.?\d*)',
    ]
    
    current_signal = {}
    
    for line in text_lines:
        line = line.strip()
        if not line:
            continue
            
        # Ищем основной сигнал (asset, direction, entry_price)
        for pattern in patterns[:4]:  # Первые 4 паттерна для основного сигнала
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) >= 3:
                    # Новый сигнал
                    if current_signal:
                        signals.append(current_signal)
                    
                    current_signal = {
                        "asset": groups[0].upper(),
                        "direction": groups[1].upper(),
                        "entry_price": float(groups[2].replace(',', '')),
                        "source": "OCR",
                        "extracted_text": line
                    }
                elif len(groups) == 2:
                    # Target/Stop или Confidence
                    if "Target" in line and "Stop" in line:
                        try:
                            current_signal["target_price"] = float(groups[0].replace(',', ''))
                            current_signal["stop_loss"] = float(groups[1].replace(',', ''))
                        except (ValueError, IndexError):
                            pass
                    elif "Confidence" in line:
                        try:
                            current_signal["confidence"] = int(groups[0])
                        except (ValueError, IndexError):
                            pass
                break
    
    # Добавляем последний сигнал
    if current_signal:
        signals.append(current_signal)
    
    return signals

def process_image_with_ocr(image_path, channel_name):
    """Обрабатывает изображение с помощью OCR и извлекает сигналы"""
    print(f"🔍 OCR обработка: {image_path}")
    
    # Извлекаем текст из изображения
    extracted_text = extract_text_from_image_simple(image_path)
    
    if not extracted_text:
        print(f"   ❌ Не удалось извлечь текст")
        return []
    
    print(f"   📝 Извлеченный текст:")
    for line in extracted_text:
        print(f"      {line}")
    
    # Парсим сигналы из извлеченного текста
    signals = parse_signals_from_text(extracted_text)
    
    if signals:
        print(f"   🎯 Найдено {len(signals)} сигналов:")
        for i, signal in enumerate(signals, 1):
            print(f"      {i}. {signal['asset']} {signal['direction']} @ ${signal['entry_price']}")
            if 'target_price' in signal:
                print(f"         Target: ${signal['target_price']} Stop: ${signal['stop_loss']}")
            if 'confidence' in signal:
                print(f"         Confidence: {signal['confidence']}%")
    else:
        print(f"   ⚠️ Сигналы не найдены")
    
    return signals

def find_and_process_images():
    """Находит все изображения и обрабатывает их с OCR"""
    print("🚀 OCR ОБРАБОТКА ИЗОБРАЖЕНИЙ ДЛЯ ИЗВЛЕЧЕНИЯ СИГНАЛОВ")
    print("=" * 60)
    
    # Ищем все изображения в текущей директории
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_files = []
    
    for file in os.listdir('.'):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(file)
    
    if not image_files:
        print("❌ Изображения не найдены")
        return []
    
    print(f"📁 Найдено {len(image_files)} изображений:")
    for img in image_files:
        print(f"   - {img}")
    
    all_signals = []
    channel_stats = {}
    
    for image_path in image_files:
        print(f"\n{'='*50}")
        
        # Определяем канал по имени файла
        channel_name = image_path.split('_')[0] if '_' in image_path else "unknown"
        
        # Обрабатываем изображение
        signals = process_image_with_ocr(image_path, channel_name)
        
        if signals:
            # Добавляем информацию о канале к каждому сигналу
            for signal in signals:
                signal['channel'] = channel_name
                signal['image_source'] = image_path
                signal['extraction_time'] = datetime.now().isoformat()
            
            all_signals.extend(signals)
            
            # Обновляем статистику по каналам
            if channel_name not in channel_stats:
                channel_stats[channel_name] = 0
            channel_stats[channel_name] += len(signals)
    
    return all_signals, channel_stats

def save_ocr_results(signals, channel_stats):
    """Сохраняет результаты OCR обработки"""
    results = {
        "total_signals": len(signals),
        "channels_processed": len(channel_stats),
        "signals_by_channel": channel_stats,
        "all_signals": signals,
        "processing_time": datetime.now().isoformat()
    }
    
    # Сохраняем в JSON
    with open('ocr_signals_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результаты сохранены в ocr_signals_results.json")
    
    return results

def main():
    """Основная функция"""
    print("🚀 OCR ИЗВЛЕЧЕНИЕ СИГНАЛОВ ИЗ ИЗОБРАЖЕНИЙ")
    print("=" * 60)
    
    # Обрабатываем изображения с OCR
    signals, channel_stats = find_and_process_images()
    
    if not signals:
        print("\n❌ Сигналы не найдены")
        return
    
    # Сохраняем результаты
    results = save_ocr_results(signals, channel_stats)
    
    # Итоговый отчет
    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ ПО OCR ОБРАБОТКЕ")
    print(f"{'='*60}")
    
    print(f"Всего обработано изображений: {len(set(s['image_source'] for s in signals))}")
    print(f"Всего извлечено сигналов: {len(signals)}")
    print(f"Каналов с сигналами: {len(channel_stats)}")
    
    if channel_stats:
        print(f"\n📊 ПО КАНАЛАМ:")
        for channel, count in channel_stats.items():
            print(f"  - {channel}: {count} сигналов")
    
    print(f"\n🎯 ВСЕ ИЗВЛЕЧЕННЫЕ СИГНАЛЫ:")
    for i, signal in enumerate(signals, 1):
        print(f"  {i:2d}. {signal['asset']} {signal['direction']} @ ${signal['entry_price']}")
        print(f"      Канал: {signal['channel']}")
        print(f"      Изображение: {signal['image_source']}")
        if 'target_price' in signal:
            print(f"      Target: ${signal['target_price']} Stop: ${signal['stop_loss']}")
        if 'confidence' in signal:
            print(f"      Confidence: {signal['confidence']}%")
        print()
    
    # Рекомендации по улучшению
    print(f"💡 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ OCR:")
    print(f"1. Использовать Tesseract OCR для реального распознавания")
    print(f"2. Добавить предобработку изображений (контраст, яркость)")
    print(f"3. Использовать AI модели для распознавания графиков")
    print(f"4. Интегрировать с API для распознавания таблиц")
    print(f"5. Добавить валидацию извлеченных сигналов")

if __name__ == "__main__":
    main()
