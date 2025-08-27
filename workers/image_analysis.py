import urllib.request
import json
import re
from datetime import datetime
import base64

def get_messages_with_images(username):
    """Получает сообщения с изображениями из канала"""
    try:
        url = f"https://t.me/s/{username}"
        
        opener = urllib.request.build_opener()
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        ]
        
        with opener.open(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            
            messages = []
            
            # Ищем блоки сообщений с изображениями
            message_pattern = r'<div class="tgme_widget_message[^"]*"[^>]*>(.*?)</div>'
            message_matches = re.findall(message_pattern, content, re.DOTALL)
            
            for i, message_html in enumerate(message_matches):
                # Ищем изображения в сообщении
                image_pattern = r'<img[^>]*class="[^"]*photo[^"]*"[^>]*src="([^"]*)"[^>]*>'
                image_matches = re.findall(image_pattern, message_html)
                
                # Ищем текст сообщения
                text_pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
                text_match = re.search(text_pattern, message_html, re.DOTALL)
                
                text = ""
                if text_match:
                    text = re.sub(r'<[^>]+>', '', text_match.group(1))
                    text = text.strip()
                
                if image_matches or text:
                    messages.append({
                        'id': f"{username}_{i+1}",
                        'text': text,
                        'images': image_matches,
                        'image_count': len(image_matches),
                        'date': datetime.now().isoformat()
                    })
            
            return messages
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def analyze_channel_images(username):
    """Анализирует изображения в канале"""
    print(f"🔍 АНАЛИЗ ИЗОБРАЖЕНИЙ В КАНАЛЕ: {username}")
    print("=" * 60)
    
    messages = get_messages_with_images(username)
    
    if not messages:
        print("❌ Сообщения не найдены")
        return []
    
    print(f"📊 Найдено {len(messages)} сообщений")
    
    image_stats = {
        "total_messages": len(messages),
        "messages_with_images": 0,
        "total_images": 0,
        "messages_with_text": 0,
        "sample_images": []
    }
    
    for i, message in enumerate(messages[:10]):  # Анализируем первые 10
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

def download_sample_images(image_stats):
    """Скачивает образцы изображений для анализа"""
    print(f"\n📥 СКАЧИВАНИЕ ОБРАЗЦОВ ИЗОБРАЖЕНИЙ")
    print("=" * 60)
    
    if not image_stats["sample_images"]:
        print("❌ Нет изображений для скачивания")
        return
    
    downloaded = []
    
    for i, img_info in enumerate(image_stats["sample_images"]):
        try:
            url = img_info["url"]
            filename = f"sample_image_{i+1}.jpg"
            
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
                "message_text": img_info["message_text"]
            })
            
            print(f"   ✅ Сохранено как {filename}")
            
        except Exception as e:
            print(f"   ❌ Ошибка скачивания: {e}")
    
    return downloaded

def main():
    """Основная функция"""
    print("🚀 АНАЛИЗ ИЗОБРАЖЕНИЙ В TELEGRAM КАНАЛАХ")
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
        image_stats = analyze_channel_images(username)
        
        if image_stats:
            image_stats["channel_username"] = username
            all_results["channels_analyzed"].append(image_stats)
            all_results["total_images_found"] += image_stats["total_images"]
            
            # Скачиваем образцы изображений
            if image_stats["sample_images"]:
                downloaded = download_sample_images(image_stats)
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
    with open('image_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результаты сохранены в image_analysis_results.json")
    
    # Рекомендации по обработке изображений
    print(f"\n💡 РЕКОМЕНДАЦИИ ПО ОБРАБОТКЕ ИЗОБРАЖЕНИЙ:")
    print(f"1. OCR (Optical Character Recognition) для извлечения текста")
    print(f"2. Анализ графиков и диаграмм")
    print(f"3. Распознавание таблиц с сигналами")
    print(f"4. Обработка скриншотов торговых платформ")
    print(f"5. Анализ инфографики с торговыми рекомендациями")

if __name__ == "__main__":
    main()
