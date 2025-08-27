#!/usr/bin/env python3
"""
Простой скрипт для открытия дашборда
"""

import webbrowser
import os
from pathlib import Path

def main():
    """Открывает дашборд в браузере"""
    print("🌐 Открытие дашборда...")
    
    # Путь к дашборду
    dashboard_path = Path('workers/comprehensive_dashboard.html')
    
    if dashboard_path.exists():
        # Получаем абсолютный путь
        abs_path = dashboard_path.absolute()
        
        print(f"📁 Путь к дашборду: {abs_path}")
        print("🔄 Открываю в браузере...")
        
        try:
            # Открываем в браузере
            webbrowser.open(f'file:///{abs_path.as_posix()}')
            print("✅ Дашборд открыт!")
            print("\n📊 Если данные не загрузились:")
            print("   1. Нажмите кнопку '🔄 Обновить данные' в дашборде")
            print("   2. Или обновите страницу (F5)")
            
        except Exception as e:
            print(f"❌ Ошибка открытия браузера: {e}")
            print(f"📋 Откройте вручную: {abs_path}")
    else:
        print("❌ Файл дашборда не найден!")
        print("💡 Убедитесь, что вы запустили demo_comprehensive_system.py")

if __name__ == "__main__":
    main()
