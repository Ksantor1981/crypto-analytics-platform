import json
import os
from datetime import datetime

def load_text_signals():
    """Загружает сигналы из текстового анализа"""
    try:
        with open('all_channels_check.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('all_signals', [])
    except FileNotFoundError:
        print("⚠️ Файл all_channels_check.json не найден")
        return []

def load_ocr_signals():
    """Загружает сигналы из OCR анализа"""
    try:
        with open('ocr_signals_results.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('all_signals', [])
    except FileNotFoundError:
        print("⚠️ Файл ocr_signals_results.json не найден")
        return []

def normalize_signal(signal, source_type):
    """Нормализует сигнал в единый формат"""
    normalized = {
        "id": f"{source_type}_{signal.get('message_id', signal.get('image_source', 'unknown'))}",
        "asset": signal.get('asset', 'UNKNOWN'),
        "direction": signal.get('direction', 'UNKNOWN'),
        "entry_price": signal.get('entry_price'),
        "target_price": signal.get('target_price'),
        "stop_loss": signal.get('stop_loss'),
        "confidence": signal.get('confidence', signal.get('combined_confidence', 70)),
        "channel": signal.get('channel_username', signal.get('channel', 'unknown')),
        "source_type": source_type,
        "extraction_time": signal.get('extraction_time', datetime.now().isoformat()),
        "bybit_available": check_bybit_availability(signal.get('asset', 'UNKNOWN'))
    }
    
    # Добавляем дополнительную информацию
    if source_type == "text":
        normalized["message_text"] = signal.get('message_text', '')
        normalized["pattern_used"] = signal.get('pattern_used', '')
    elif source_type == "ocr":
        normalized["image_source"] = signal.get('image_source', '')
        normalized["extracted_text"] = signal.get('extracted_text', '')
    
    return normalized

def check_bybit_availability(asset):
    """Проверяет доступность актива на Bybit"""
    # Список активов, доступных на Bybit
    bybit_assets = [
        'BTC', 'ETH', 'SOL', 'ADA', 'MATIC', 'DOT', 'AVAX', 'LINK', 
        'UNI', 'ATOM', 'LTC', 'BCH', 'XRP', 'DOGE', 'SHIB', 'TRX'
    ]
    return asset.upper() in bybit_assets

def integrate_all_signals():
    """Интегрирует все найденные сигналы"""
    print("🚀 ИНТЕГРАЦИЯ ВСЕХ НАЙДЕННЫХ СИГНАЛОВ")
    print("=" * 60)
    
    # Загружаем сигналы из разных источников
    text_signals = load_text_signals()
    ocr_signals = load_ocr_signals()
    
    print(f"📝 Сигналы из текста: {len(text_signals)}")
    print(f"🖼️ Сигналы из OCR: {len(ocr_signals)}")
    
    # Нормализуем и объединяем сигналы
    all_signals = []
    
    # Обрабатываем текстовые сигналы
    for signal in text_signals:
        normalized = normalize_signal(signal, "text")
        all_signals.append(normalized)
    
    # Обрабатываем OCR сигналы
    for signal in ocr_signals:
        normalized = normalize_signal(signal, "ocr")
        all_signals.append(normalized)
    
    print(f"📊 Всего интегрировано сигналов: {len(all_signals)}")
    
    return all_signals

def generate_statistics(all_signals):
    """Генерирует статистику по всем сигналам"""
    stats = {
        "total_signals": len(all_signals),
        "by_source_type": {},
        "by_channel": {},
        "by_direction": {},
        "bybit_available": 0,
        "bybit_unavailable": 0,
        "confidence_ranges": {
            "high": 0,    # 80-100%
            "medium": 0,  # 60-79%
            "low": 0      # 0-59%
        }
    }
    
    for signal in all_signals:
        # По типу источника
        source_type = signal['source_type']
        stats['by_source_type'][source_type] = stats['by_source_type'].get(source_type, 0) + 1
        
        # По каналу
        channel = signal['channel']
        stats['by_channel'][channel] = stats['by_channel'].get(channel, 0) + 1
        
        # По направлению
        direction = signal['direction']
        stats['by_direction'][direction] = stats['by_direction'].get(direction, 0) + 1
        
        # По доступности на Bybit
        if signal['bybit_available']:
            stats['bybit_available'] += 1
        else:
            stats['bybit_unavailable'] += 1
        
        # По уровню уверенности
        confidence = signal.get('confidence', 70)
        if confidence >= 80:
            stats['confidence_ranges']['high'] += 1
        elif confidence >= 60:
            stats['confidence_ranges']['medium'] += 1
        else:
            stats['confidence_ranges']['low'] += 1
    
    return stats

def save_integrated_results(all_signals, stats):
    """Сохраняет интегрированные результаты"""
    results = {
        "integration_time": datetime.now().isoformat(),
        "statistics": stats,
        "all_signals": all_signals
    }
    
    # Сохраняем полные результаты
    with open('integrated_signals.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Создаем упрощенную версию для фронтенда
    simplified_signals = []
    for signal in all_signals:
        simplified = {
            "id": signal['id'],
            "asset": signal['asset'],
            "direction": signal['direction'],
            "entry_price": signal['entry_price'],
            "target_price": signal['target_price'],
            "stop_loss": signal['stop_loss'],
            "confidence": signal['confidence'],
            "channel": signal['channel'],
            "source_type": signal['source_type'],
            "bybit_available": signal['bybit_available']
        }
        simplified_signals.append(simplified)
    
    frontend_data = {
        "signals": simplified_signals,
        "total_count": len(simplified_signals),
        "last_updated": datetime.now().isoformat()
    }
    
    with open('real_data.json', 'w', encoding='utf-8') as f:
        json.dump(frontend_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Результаты сохранены:")
    print(f"   - integrated_signals.json (полные данные)")
    print(f"   - real_data.json (для фронтенда)")

def print_detailed_report(all_signals, stats):
    """Выводит детальный отчет"""
    print(f"\n{'='*60}")
    print("📊 ДЕТАЛЬНЫЙ ОТЧЕТ ПО ИНТЕГРИРОВАННЫМ СИГНАЛАМ")
    print(f"{'='*60}")
    
    print(f"📈 ОБЩАЯ СТАТИСТИКА:")
    print(f"   Всего сигналов: {stats['total_signals']}")
    print(f"   Доступно на Bybit: {stats['bybit_available']}")
    print(f"   Недоступно на Bybit: {stats['bybit_unavailable']}")
    
    print(f"\n📊 ПО ТИПУ ИСТОЧНИКА:")
    for source_type, count in stats['by_source_type'].items():
        print(f"   - {source_type.upper()}: {count} сигналов")
    
    print(f"\n📊 ПО КАНАЛАМ:")
    for channel, count in stats['by_channel'].items():
        print(f"   - {channel}: {count} сигналов")
    
    print(f"\n📊 ПО НАПРАВЛЕНИЮ:")
    for direction, count in stats['by_direction'].items():
        print(f"   - {direction}: {count} сигналов")
    
    print(f"\n📊 ПО УРОВНЮ УВЕРЕННОСТИ:")
    print(f"   - Высокий (80-100%): {stats['confidence_ranges']['high']}")
    print(f"   - Средний (60-79%): {stats['confidence_ranges']['medium']}")
    print(f"   - Низкий (0-59%): {stats['confidence_ranges']['low']}")
    
    print(f"\n🎯 ТОП-10 СИГНАЛОВ ПО УВЕРЕННОСТИ:")
    top_signals = sorted(all_signals, key=lambda x: x.get('confidence', 0), reverse=True)[:10]
    for i, signal in enumerate(top_signals, 1):
        print(f"   {i:2d}. {signal['asset']} {signal['direction']} @ ${signal['entry_price']}")
        print(f"       Канал: {signal['channel']} | Источник: {signal['source_type']}")
        print(f"       Уверенность: {signal.get('confidence', 0)}% | Bybit: {'✅' if signal['bybit_available'] else '❌'}")
        if signal.get('target_price'):
            print(f"       Target: ${signal['target_price']} Stop: ${signal['stop_loss']}")
        print()

def main():
    """Основная функция"""
    print("🚀 ИНТЕГРАЦИЯ ВСЕХ СИГНАЛОВ ИЗ TELEGRAM КАНАЛОВ")
    print("=" * 60)
    
    # Интегрируем все сигналы
    all_signals = integrate_all_signals()
    
    if not all_signals:
        print("❌ Нет сигналов для интеграции")
        return
    
    # Генерируем статистику
    stats = generate_statistics(all_signals)
    
    # Сохраняем результаты
    save_integrated_results(all_signals, stats)
    
    # Выводим детальный отчет
    print_detailed_report(all_signals, stats)
    
    # Финальные рекомендации
    print(f"💡 РЕКОМЕНДАЦИИ ПО ДАЛЬНЕЙШЕМУ РАЗВИТИЮ:")
    print(f"1. Интегрировать с реальным OCR (Tesseract)")
    print(f"2. Добавить валидацию сигналов по времени")
    print(f"3. Реализовать автоматическое обновление данных")
    print(f"4. Добавить фильтрацию по качеству сигналов")
    print(f"5. Интегрировать с торговыми API для исполнения")
    print(f"6. Добавить уведомления о новых сигналах")

if __name__ == "__main__":
    main()
