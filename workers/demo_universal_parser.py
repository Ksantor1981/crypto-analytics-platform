"""
Демонстрация универсального парсера структурированных сигналов
"""

import json
from datetime import datetime

def demo_universal_parser():
    """Демонстрирует работу универсального парсера"""
    
    try:
        from universal_signal_parser import UniversalSignalParser
        
        print("🎯 ДЕМОНСТРАЦИЯ УНИВЕРСАЛЬНОГО ПАРСЕРА СИГНАЛОВ")
        print("=" * 60)
        
        parser = UniversalSignalParser()
        
        # Тестовые случаи из реальных каналов
        test_cases = [
            {
                'name': 'BinanceKillers',
                'text': """
                SIGNAL ID: #1956
                COIN: $BTC/USDT (3-5x)
                Direction: LONG 📈
                ENTRY: 112207 - 110500
                TARGETS: 113500 - 114800 - 117000 - 123236
                STOP LOSS: 109638
                """,
                'channel': 'BinanceKillers'
            },
            {
                'name': 'Wolf of Trading',
                'text': """
                #BAND/USDT
                🔴 SHORT
                👆 Entry: 1.0700 - 1.1050
                🌐 Leverage: 20x
                🎯 Target 1: 1.0590
                🎯 Target 2: 1.0480
                🎯 Target 3: 1.0370
                🎯 Target 4: 1.0260
                🎯 Target 5: 1.0150
                🎯 Target 6: 1.0040
                ❌ StopLoss: 1.1340
                """,
                'channel': 'Wolf of Trading'
            },
            {
                'name': 'Crypto Inner Circle',
                'text': """
                ⚡⚡ BSW/USDT ⚡
                Signal Type: Regular (Short)
                Leverage: Cross (25x)
                Entry Targets: 0.01862
                Take-Profit Targets: 0.01834, 0.01815, 0.01797, 0.01769, 0.01750, 0.01722
                Stop Targets: 5-10%
                """,
                'channel': 'Crypto Inner Circle'
            },
            {
                'name': 'Дневник Трейдера',
                'text': """
                Открываем пару WOO / USDT в SHORT
                Рыночный ордер: 0.07673
                Cross маржа
                Плечо: 17x
                Тейки: 0.0756, 0.07447, 0.07221
                Стоп: 0.08304
                """,
                'channel': 'Дневник Трейдера'
            },
            {
                'name': 'Торговля Криптовалютой',
                'text': """
                Заходим JASMY SHORT 25x
                Вход: по рынку
                Тейк: 0.015956 / 0.014906 / 0.013173
                Стоп: 0.017547
                """,
                'channel': 'Торговля Криптовалютой'
            }
        ]
        
        all_signals = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📊 Тест {i}: {test_case['name']}")
            print("-" * 40)
            
            signal = parser.parse_signal(test_case['text'], test_case['channel'])
            
            if signal:
                print(f"✅ Успешно извлечен сигнал!")
                print(f"Asset: {signal.asset}")
                print(f"Direction: {signal.direction}")
                print(f"Entry Type: {signal.entry_type}")
                if signal.entry_price:
                    print(f"Entry Price: ${signal.entry_price:,.6f}")
                if signal.entry_range:
                    print(f"Entry Range: {signal.entry_range}")
                print(f"Targets: {signal.targets}")
                if signal.stop_loss:
                    print(f"Stop Loss: ${signal.stop_loss:,.6f}")
                if signal.stop_loss_percent:
                    print(f"Stop Loss %: {signal.stop_loss_percent}%")
                print(f"Leverage: {signal.leverage}")
                print(f"Timeframe: {signal.timeframe}")
                
                # Конвертируем в стандартный формат
                standard = parser.convert_to_standard_format(signal)
                all_signals.append(standard)
                
                print(f"Standard Format: {standard['asset']} {standard['direction']} @ ${standard['entry_price']:,.6f if standard['entry_price'] else 'Market'}")
            else:
                print("❌ Не удалось извлечь сигнал")
        
        # Сохраняем результаты
        result = {
            'success': True,
            'total_signals': len(all_signals),
            'signals': all_signals,
            'demo_time': datetime.now().isoformat(),
            'parser_version': 'universal_v1.0'
        }
        
        with open('demo_universal_signals.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 Демонстрация завершена!")
        print(f"📊 Всего извлечено сигналов: {len(all_signals)}")
        print(f"📁 Результаты сохранены в: demo_universal_signals.json")
        
        return result
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что файл universal_signal_parser.py находится в той же директории")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    demo_universal_parser()
