import urllib.request
import json
import re
from datetime import datetime

def get_messages_with_images_fixed(username):
    """Получает сообщения с изображениями из канала (исправленная версия)"""
    try:
        url = f"https://t.me/s/{username}"
        
        opener = urllib.request.build_opener()
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        ]
        
        with opener.open(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            
            messages = []
            
            # Ищем все блоки сообщений
            message_pattern = r'<div class="tgme_widget_message[^"]*"[^>]*>(.*?)</div>'
            message_matches = re.findall(message_pattern, content, re.DOTALL)
            
            print(f"Найдено {len(message_matches)} блоков сообщений")
            
            for i, message_html in enumerate(message_matches):
                # Ищем изображения с разными паттернами
                image_patterns = [
                    r'<img[^>]*src="([^"]*)"[^>]*>',  # Любые изображения
                    r'<img[^>]*class="[^"]*photo[^"]*"[^>]*src="([^"]*)"[^>]*>',  # Фото
                    r'<img[^>]*class="[^"]*image[^"]*"[^>]*src="([^"]*)"[^>]*>',  # Изображения
                    r'<img[^>]*class="[^"]*media[^"]*"[^>]*src="([^"]*)"[^>]*>',  # Медиа
                ]
                
                images = []
                for pattern in image_patterns:
                    matches = re.findall(pattern, message_html, re.IGNORECASE)
                    images.extend(matches)
                
                # Убираем дубликаты
                images = list(set(images))
                
                # Ищем текст сообщения
                text_pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
                text_match = re.search(text_pattern, message_html, re.DOTALL)
                
                text = ""
                if text_match:
                    text = re.sub(r'<[^>]+>', '', text_match.group(1))
                    text = text.strip()
                
                if images or text:
                    messages.append({
                        'id': f"{username}_{i+1}",
                        'text': text,
                        'images': images,
                        'image_count': len(images),
                        'date': datetime.now().isoformat()
                    })
                    
                    if images:
                        print(f"Сообщение {i+1}: найдено {len(images)} изображений")
                        for img in images[:2]:  # Показываем первые 2
                            print(f"  📷 {img}")
            
            return messages
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def analyze_single_channel_images(username):
    """Анализирует изображения в одном канале"""
    print(f"🔍 АНАЛИЗ ИЗОБРАЖЕНИЙ В КАНАЛЕ: {username}")
    print("=" * 60)
    
    messages = get_messages_with_images_fixed(username)
    
    if not messages:
        print("❌ Сообщения не найдены")
        return None
    
    print(f"📊 Найдено {len(messages)} сообщений")
    
    image_stats = {
        "channel_username": username,
        "total_messages": len(messages),
        "messages_with_images": 0,
        "total_images": 0,
        "messages_with_text": 0,
        "sample_images": []
    }
    
    for i, message in enumerate(messages[:5]):  # Анализируем первые 5
        print(f"\n📝 Сообщение {i+1}:")
        
        if message['text']:
            print(f"   Текст: {message['text'][:100]}...")
            image_stats["messages_with_text"] += 1
        
        if message['images']:
            print(f"   🖼️ Изображений: {message['image_count']}")
            image_stats["messages_with_images"] += 1
            image_stats["total_images"] += message['image_count']
            
            # Сохраняем первые 3 URL изображений для анализа
            if len(image_stats["sample_images"]) < 3:
                for img_url in message['images'][:3]:
                    image_stats["sample_images"].append({
                        "url": img_url,
                        "message_id": message['id'],
                        "message_text": message['text'][:100] if message['text'] else ""
                    })
                    print(f"      📷 {img_url}")
        else:
            print(f"   📄 Только текст")
    
    print(f"\n📊 СТАТИСТИКА ИЗОБРАЖЕНИЙ:")
    print(f"   Всего сообщений: {image_stats['total_messages']}")
    print(f"   Сообщений с изображениями: {image_stats['messages_with_images']}")
    print(f"   Всего изображений: {image_stats['total_images']}")
    print(f"   Сообщений с текстом: {image_stats['messages_with_text']}")
    
    return image_stats

def download_and_analyze_images(image_stats):
    """Скачивает и анализирует изображения"""
    if not image_stats or not image_stats["sample_images"]:
        print("❌ Нет изображений для анализа")
        return
    
    print(f"\n📥 СКАЧИВАНИЕ И АНАЛИЗ ИЗОБРАЖЕНИЙ")
    print("=" * 60)
    
    downloaded = []
    
    for i, img_info in enumerate(image_stats["sample_images"]):
        try:
            url = img_info["url"]
            filename = f"{image_stats['channel_username']}_image_{i+1}.jpg"
            
            print(f"📥 Скачивание {i+1}: {url}")
            
            opener = urllib.request.build_opener()
            opener.addheaders = [
                ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            ]
            
            with opener.open(url, timeout=10) as response:
                with open(filename, 'wb') as f:
                    f.write(response.read())
            
            downloaded.append({
                "filename": filename,
                "url": url,
                "message_id": img_info["message_id"],
                "message_text": img_info["message_text"],
                "size_bytes": len(response.read()) if hasattr(response, 'read') else 0
            })
            
            print(f"   ✅ Сохранено как {filename}")
            
            # Анализируем тип изображения
            if "chart" in url.lower() or "graph" in url.lower():
                print(f"   📊 Похоже на график/диаграмму")
            elif "screenshot" in url.lower() or "screen" in url.lower():
                print(f"   🖥️ Похоже на скриншот")
            elif "table" in url.lower() or "list" in url.lower():
                print(f"   📋 Похоже на таблицу/список")
            else:
                print(f"   🖼️ Обычное изображение")
            
        except Exception as e:
            print(f"   ❌ Ошибка скачивания: {e}")
    
    return downloaded

def main():
    """Основная функция"""
    print("🚀 ИСПРАВЛЕННЫЙ АНАЛИЗ ИЗОБРАЖЕНИЙ В TELEGRAM КАНАЛАХ")
    print("=" * 60)
    
    # Анализируем каналы с аналитикой
    analytical_channels = [
        "CryptoCapoTG",
        "binance_signals_official", 
        "crypto_signals_daily",
        "crypto_analytics_pro",
        "price_alerts",
        "crypto_news_signals"
    ]
    
    all_results = {
        "channels_analyzed": [],
        "total_images_found": 0,
        "sample_images_downloaded": [],
        "analysis_time": datetime.now().isoformat()
    }
    
    for username in analytical_channels:
        print(f"\n{'='*60}")
        
        # Анализируем изображения в канале
        image_stats = analyze_single_channel_images(username)
        
        if image_stats and image_stats["total_images"] > 0:
            all_results["channels_analyzed"].append(image_stats)
            all_results["total_images_found"] += image_stats["total_images"]
            
            # Скачиваем и анализируем образцы изображений
            downloaded = download_and_analyze_images(image_stats)
            if downloaded:
                all_results["sample_images_downloaded"].extend(downloaded)
    
    # Итоговый отчет
    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ ПО ИЗОБРАЖЕНИЯМ")
    print(f"{'='*60}")
    
    print(f"Проанализировано каналов: {len(all_results['channels_analyzed'])}")
    print(f"Всего найдено изображений: {all_results['total_images_found']}")
    print(f"Скачано образцов: {len(all_results['sample_images_downloaded'])}")
    
    if all_results["channels_analyzed"]:
        print(f"\n📊 ПО КАНАЛАМ:")
        for channel in all_results["channels_analyzed"]:
            print(f"  - {channel['channel_username']}: {channel['total_images']} изображений")
    
    if all_results["sample_images_downloaded"]:
        print(f"\n📥 СКАЧАННЫЕ ОБРАЗЦЫ:")
        for img in all_results["sample_images_downloaded"]:
            print(f"  - {img['filename']} (из {img['message_id']})")
            if img['message_text']:
                print(f"    Текст: {img['message_text']}")
    
    # Сохраняем результаты
    with open('fixed_image_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результаты сохранены в fixed_image_analysis.json")
    
    # Рекомендации по обработке изображений
    print(f"\n💡 РЕКОМЕНДАЦИИ ПО ОБРАБОТКЕ ИЗОБРАЖЕНИЙ:")
    print(f"1. OCR (Optical Character Recognition) для извлечения текста")
    print(f"2. Анализ графиков и диаграмм")
    print(f"3. Распознавание таблиц с сигналами")
    print(f"4. Обработка скриншотов торговых платформ")
    print(f"5. Анализ инфографики с торговыми рекомендациями")
    print(f"6. Использование AI для распознавания торговых сигналов на изображениях")

if __name__ == "__main__":
    main()
