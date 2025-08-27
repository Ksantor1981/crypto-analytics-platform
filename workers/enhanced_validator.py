"""
Enhanced Signal Validator - Улучшенный валидатор сигналов
Включает расширенную проверку активов, цен и логики торговли
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from improved_signal_parser import ImprovedSignal, SignalDirection

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    CRITICAL = "critical"    # Критические ошибки - сигнал невалиден
    WARNING = "warning"      # Предупреждения - сигнал валиден, но с оговорками
    INFO = "info"           # Информационные сообщения

@dataclass
class ValidationResult:
    """Результат валидации"""
    is_valid: bool
    level: ValidationLevel
    message: str
    field: str
    suggested_value: Optional[str] = None

class EnhancedSignalValidator:
    """Улучшенный валидатор сигналов"""
    
    def __init__(self):
        # Расширенный список валидных криптовалют
        self.valid_assets = {
            # Основные криптовалюты
            'BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'LINK', 'UNI', 'AVAX',
            'MATIC', 'ATOM', 'XRP', 'DOGE', 'SHIB', 'LTC', 'BCH', 'BNB',
            
            # Стейблкоины
            'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'FRAX',
            
            # DeFi токены
            'AAVE', 'COMP', 'MKR', 'SNX', 'CRV', 'YFI', 'SUSHI', '1INCH',
            
            # Layer 1 блокчейны
            'LUNA', 'NEAR', 'FTM', 'ALGO', 'AVAX', 'ATOM', 'DOT', 'ADA',
            
            # Layer 2 решения
            'OP', 'ARB', 'MATIC', 'IMX', 'ZKSYNC', 'STARK',
            
            # Мемкоины и новые токены
            'PEPE', 'BONK', 'WIF', 'MEME', 'PUMP', 'DOGE', 'SHIB',
            
            # Игровые токены
            'AXS', 'MANA', 'SAND', 'ENJ', 'GALA', 'ILV',
            
            # AI и технологические токены
            'OCEAN', 'FET', 'AGIX', 'RNDR', 'TAO', 'BITTENSOR',
            
            # Новые популярные токены
            'SYS', 'ENA', 'ZIG', 'ATA', 'MAVIA', 'ORDI', 'BAND', 'BSW',
            'WOO', 'JASMY', 'ENS', 'SUI', 'APT', 'INJ', 'TIA', 'SEI',
            'PYTH', 'JUP', 'BONK', 'WIF', 'BOME', 'POPCAT', 'BOOK',
            
            # Альтернативные названия
            'BITCOIN', 'ETHEREUM', 'CARDANO', 'POLKADOT', 'CHAINLINK',
            'UNISWAP', 'POLYGON', 'COSMOS', 'RIPPLE', 'LITECOIN'
        }
        
        # Список доступных на Bybit (основные торговые пары)
        self.bybit_assets = {
            'BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'LINK', 'UNI', 'AVAX',
            'MATIC', 'ATOM', 'XRP', 'DOGE', 'SHIB', 'LTC', 'BCH', 'BNB',
            'SYS', 'ENA', 'ZIG', 'MAVIA', 'ORDI', 'BAND', 'BSW', 'WOO',
            'JASMY', 'MEME', 'PUMP', 'ENS', 'OP', 'ARB', 'SUI', 'APT',
            'INJ', 'TIA', 'SEI', 'PYTH', 'JUP', 'BONK', 'WIF', 'BOME',
            'POPCAT', 'BOOK', 'PEPE', 'FLOKI', 'BABYDOGE'
        }
        
        # Паттерны для валидации цен
        self.price_patterns = {
            'btc_range': (1000, 200000),      # BTC: $1K - $200K
            'eth_range': (100, 20000),        # ETH: $100 - $20K
            'altcoin_range': (0.0001, 1000),  # Альткоины: $0.0001 - $1K
            'stablecoin_range': (0.95, 1.05)  # Стейблкоины: $0.95 - $1.05
        }
        
        # Минимальные и максимальные значения для leverage
        self.leverage_limits = {
            'min': 1,
            'max': 100,
            'recommended_max': 20
        }
    
    def validate_signal(self, signal: ImprovedSignal) -> List[ValidationResult]:
        """Полная валидация сигнала"""
        results = []
        
        # Базовые проверки
        results.extend(self.validate_asset(signal))
        results.extend(self.validate_direction(signal))
        results.extend(self.validate_prices(signal))
        results.extend(self.validate_price_logic(signal))
        results.extend(self.validate_leverage(signal))
        results.extend(self.validate_timeframe(signal))
        results.extend(self.validate_bybit_availability(signal))
        
        # Определяем общую валидность
        critical_errors = [r for r in results if r.level == ValidationLevel.CRITICAL]
        signal.is_valid = len(critical_errors) == 0
        
        # Сохраняем ошибки валидации
        signal.validation_errors = [r.message for r in results if r.level in [ValidationLevel.CRITICAL, ValidationLevel.WARNING]]
        
        return results
    
    def validate_asset(self, signal: ImprovedSignal) -> List[ValidationResult]:
        """Валидация актива"""
        results = []
        
        if not signal.asset:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.CRITICAL,
                message="Asset is required",
                field="asset"
            ))
            return results
        
        # Проверяем, является ли актив валидным
        asset_upper = signal.asset.upper()
        if asset_upper not in self.valid_assets:
            # Попробуем найти похожий актив
            similar_assets = self.find_similar_assets(asset_upper)
            
            if similar_assets:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.CRITICAL,
                    message=f"Invalid asset '{signal.asset}'. Did you mean: {', '.join(similar_assets[:3])}?",
                    field="asset",
                    suggested_value=similar_assets[0]
                ))
            else:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.CRITICAL,
                    message=f"Invalid asset '{signal.asset}'",
                    field="asset"
                ))
        else:
            # Нормализуем название актива
            if signal.asset != asset_upper:
                results.append(ValidationResult(
                    is_valid=True,
                    level=ValidationLevel.INFO,
                    message=f"Asset normalized: {signal.asset} → {asset_upper}",
                    field="asset",
                    suggested_value=asset_upper
                ))
        
        return results
    
    def validate_direction(self, signal: ImprovedSignal) -> List[ValidationResult]:
        """Валидация направления торговли"""
        results = []
        
        if not signal.direction:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.CRITICAL,
                message="Direction is required",
                field="direction"
            ))
            return results
        
        # Проверяем, что направление валидно
        valid_directions = [d.value for d in SignalDirection]
        if signal.direction.value not in valid_directions:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.CRITICAL,
                message=f"Invalid direction '{signal.direction.value}'. Valid: {', '.join(valid_directions)}",
                field="direction"
            ))
        
        return results
    
    def validate_prices(self, signal: ImprovedSignal) -> List[ValidationResult]:
        """Валидация цен"""
        results = []
        
        # Проверяем entry_price
        if signal.entry_price is not None:
            price_validation = self.validate_price_value(signal.entry_price, signal.asset, "entry_price")
            if price_validation:
                results.append(price_validation)
        
        # Проверяем target_price
        if signal.target_price is not None:
            price_validation = self.validate_price_value(signal.target_price, signal.asset, "target_price")
            if price_validation:
                results.append(price_validation)
        
        # Проверяем stop_loss
        if signal.stop_loss is not None:
            price_validation = self.validate_price_value(signal.stop_loss, signal.asset, "stop_loss")
            if price_validation:
                results.append(price_validation)
        
        return results
    
    def validate_price_value(self, price: float, asset: str, field: str) -> Optional[ValidationResult]:
        """Валидация конкретной цены"""
        if price <= 0:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.CRITICAL,
                message=f"{field} must be positive",
                field=field
            )
        
        # Проверяем диапазон цен в зависимости от актива
        asset_upper = asset.upper()
        
        if asset_upper == 'BTC':
            min_price, max_price = self.price_patterns['btc_range']
        elif asset_upper == 'ETH':
            min_price, max_price = self.price_patterns['eth_range']
        elif asset_upper in ['USDT', 'USDC', 'BUSD', 'DAI']:
            min_price, max_price = self.price_patterns['stablecoin_range']
        else:
            min_price, max_price = self.price_patterns['altcoin_range']
        
        if price < min_price or price > max_price:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"{field} ${price:,.2f} is outside expected range for {asset} (${min_price:,.2f} - ${max_price:,.2f})",
                field=field
            )
        
        return None
    
    def validate_price_logic(self, signal: ImprovedSignal) -> List[ValidationResult]:
        """Валидация логики цен"""
        results = []
        
        # Проверяем только если есть все три цены
        if not all([signal.entry_price, signal.target_price, signal.stop_loss]):
            return results
        
        entry = signal.entry_price
        target = signal.target_price
        stop = signal.stop_loss
        
        if signal.direction in [SignalDirection.LONG, SignalDirection.BUY]:
            # Для LONG/BUY: entry < target, stop < entry
            if target <= entry:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.CRITICAL,
                    message="For LONG/BUY: target price must be higher than entry price",
                    field="target_price"
                ))
            
            if stop >= entry:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.CRITICAL,
                    message="For LONG/BUY: stop loss must be lower than entry price",
                    field="stop_loss"
                ))
        
        elif signal.direction in [SignalDirection.SHORT, SignalDirection.SELL]:
            # Для SHORT/SELL: entry > target, stop > entry
            if target >= entry:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.CRITICAL,
                    message="For SHORT/SELL: target price must be lower than entry price",
                    field="target_price"
                ))
            
            if stop <= entry:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.CRITICAL,
                    message="For SHORT/SELL: stop loss must be higher than entry price",
                    field="stop_loss"
                ))
        
        # Проверяем риск/прибыль
        if signal.risk_reward_ratio:
            if signal.risk_reward_ratio < 1.0:
                results.append(ValidationResult(
                    is_valid=True,
                    level=ValidationLevel.WARNING,
                    message=f"Risk/Reward ratio {signal.risk_reward_ratio:.2f} is below 1.0 (high risk)",
                    field="risk_reward_ratio"
                ))
            elif signal.risk_reward_ratio > 5.0:
                results.append(ValidationResult(
                    is_valid=True,
                    level=ValidationLevel.INFO,
                    message=f"Excellent Risk/Reward ratio: {signal.risk_reward_ratio:.2f}",
                    field="risk_reward_ratio"
                ))
        
        return results
    
    def validate_leverage(self, signal: ImprovedSignal) -> List[ValidationResult]:
        """Валидация leverage"""
        results = []
        
        if signal.leverage is None:
            return results
        
        if signal.leverage < self.leverage_limits['min']:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.CRITICAL,
                message=f"Leverage {signal.leverage}x is below minimum {self.leverage_limits['min']}x",
                field="leverage"
            ))
        
        if signal.leverage > self.leverage_limits['max']:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.CRITICAL,
                message=f"Leverage {signal.leverage}x exceeds maximum {self.leverage_limits['max']}x",
                field="leverage"
            ))
        
        if signal.leverage > self.leverage_limits['recommended_max']:
            results.append(ValidationResult(
                is_valid=True,
                level=ValidationLevel.WARNING,
                message=f"High leverage {signal.leverage}x (recommended max: {self.leverage_limits['recommended_max']}x)",
                field="leverage"
            ))
        
        return results
    
    def validate_timeframe(self, signal: ImprovedSignal) -> List[ValidationResult]:
        """Валидация timeframe"""
        results = []
        
        if signal.timeframe is None:
            return results
        
        valid_timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
        
        if signal.timeframe not in valid_timeframes:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"Invalid timeframe '{signal.timeframe}'. Valid: {', '.join(valid_timeframes)}",
                field="timeframe",
                suggested_value="1h"
            ))
        
        return results
    
    def validate_bybit_availability(self, signal: ImprovedSignal) -> List[ValidationResult]:
        """Валидация доступности на Bybit"""
        results = []
        
        asset_upper = signal.asset.upper()
        is_available = asset_upper in self.bybit_assets
        
        signal.bybit_available = is_available
        
        if not is_available:
            results.append(ValidationResult(
                is_valid=True,
                level=ValidationLevel.WARNING,
                message=f"Asset {signal.asset} is not available on Bybit",
                field="bybit_available"
            ))
        
        return results
    
    def find_similar_assets(self, asset: str) -> List[str]:
        """Находит похожие активы для исправления опечаток"""
        similar = []
        
        # Простые замены
        replacements = {
            'BТС': 'BTC', 'ЕТН': 'ETH', 'АDА': 'ADA',
            'SОL': 'SOL', 'DОT': 'DOT', 'LINK': 'LINK',
            'UNI': 'UNI', 'AVAX': 'AVAX', 'MATIC': 'MATIC'
        }
        
        if asset in replacements:
            similar.append(replacements[asset])
        
        # Поиск по частичному совпадению
        for valid_asset in self.valid_assets:
            if asset in valid_asset or valid_asset in asset:
                similar.append(valid_asset)
        
        # Поиск по расстоянию Левенштейна (упрощенный)
        for valid_asset in self.valid_assets:
            if len(asset) >= 3 and len(valid_asset) >= 3:
                if asset[:3] == valid_asset[:3] or asset[-3:] == valid_asset[-3:]:
                    similar.append(valid_asset)
        
        return list(set(similar))[:5]  # Возвращаем до 5 похожих активов

def main():
    """Тестирование валидатора"""
    validator = EnhancedSignalValidator()
    
    # Тестовые сигналы
    test_signals = [
        {
            'asset': 'BTC',
            'direction': SignalDirection.LONG,
            'entry_price': 50000,
            'target_price': 55000,
            'stop_loss': 48000,
            'leverage': 10
        },
        {
            'asset': 'BТС',  # Опечатка
            'direction': SignalDirection.SHORT,
            'entry_price': 50000,
            'target_price': 45000,
            'stop_loss': 52000,
            'leverage': 50
        },
        {
            'asset': 'INVALID',
            'direction': SignalDirection.BUY,
            'entry_price': 100,
            'target_price': 90,  # Неправильная логика для BUY
            'stop_loss': 110,
            'leverage': 5
        }
    ]
    
    for i, test_data in enumerate(test_signals):
        print(f"\n=== Тест {i+1} ===")
        print(f"Сигнал: {test_data}")
        
        # Создаем тестовый сигнал
        signal = ImprovedSignal(
            id=f"test_{i}",
            asset=test_data['asset'],
            direction=test_data['direction'],
            entry_price=test_data['entry_price'],
            target_price=test_data['target_price'],
            stop_loss=test_data['stop_loss'],
            leverage=test_data['leverage']
        )
        
        # Валидируем
        results = validator.validate_signal(signal)
        
        print(f"Валидность: {signal.is_valid}")
        print("Результаты валидации:")
        for result in results:
            print(f"  [{result.level.value.upper()}] {result.field}: {result.message}")

if __name__ == "__main__":
    main()
