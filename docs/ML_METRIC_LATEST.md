# ML: последняя зафиксированная метрика (честная)

**Дата:** 2026-03-26  
**Источник:** `real_signals` (backtested стратегии на свечах Binance)  
**Таймфрейм индикаторов:** `1d` (`technical_indicators.timeframe`)  
**Символы:** BTCUSDT, ETHUSDT  

## Данные

- **Свечи:** 365 дней на каждый символ (Binance), записаны в `market_candles`
- **Индикаторы:** рассчитаны из `market_candles` и записаны в `technical_indicators` (RSI/MACD/BB/ATR/Stoch)
- **Сигналы для обучения:** 145 строк в `real_signals` с исходом `TP_HIT` / `SL_HIT` / `EXPIRED`

## Метрика

Метрика зафиксирована из `ml-service/models/evaluation_report_v2.json` (модель `xgboost_real_signals`):

- **CV accuracy (TimeSeriesSplit):** **66.7%** (std 15.9%, диапазон 52.8–88.9)
- **Train accuracy:** 70.3%

## Важно

- Это **не** «точность продукта в проде», а метрика на backtest‑генерации, даже если свечи/индикаторы реальные.
- Для публичных claims нужна отдельная процедура: hold‑out по времени + реальные сигналы из Telegram/Reddit с фактическими исходами.

