"""
Price Validation API endpoints for ML Service
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta

try:
    from models.price_checker import price_checker, check_signal_price, get_current_prices
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.price_checker import price_checker, check_signal_price, get_current_prices

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["price-validation"])

class SignalValidationRequest(BaseModel):
    """Request model for signal validation"""
    id: str
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    targets: List[float]
    stop_loss: float = None
    timestamp: str = None

class PriceRequest(BaseModel):
    """Request model for current prices"""
    symbols: List[str]
    preferred_exchange: str = None

class MarketSummaryRequest(BaseModel):
    """Request model for market summary"""
    symbols: List[str]

class HistoricalDataRequest(BaseModel):
    """Request model for historical price data"""
    symbol: str
    start_time: Optional[int] = None  # Unix timestamp in milliseconds
    end_time: Optional[int] = None    # Unix timestamp in milliseconds
    interval: str = "1h"  # 1m, 5m, 15m, 1h, 4h, 1d
    exchange: str = "binance"  # binance or bybit
    hours_back: Optional[int] = 24  # Alternative to start_time/end_time

@router.post("/price-validation/validate-signal")
async def validate_signal(signal: SignalValidationRequest):
    """
    Validate a single trading signal execution
    """
    try:
        signal_data = signal.dict()
        result = await check_signal_price(signal_data)
        
        return {
            "success": True,
            "data": result,
            "message": "Signal validation completed"
        }
        
    except Exception as e:
        logger.error(f"Error validating signal: {e}")
        raise HTTPException(status_code=500, detail=f"Signal validation failed: {str(e)}")

@router.post("/price-validation/validate-batch")
async def validate_batch_signals(signals: List[SignalValidationRequest]):
    """
    Validate multiple trading signals in batch
    """
    try:
        results = []
        
        for signal in signals:
            signal_data = signal.dict()
            result = await price_checker.validate_signal_execution(signal_data)
            
            results.append({
                "signal_id": result.signal_id,
                "symbol": result.symbol,
                "status": result.status,
                "current_price": float(result.current_price),
                "pnl_percentage": float(result.pnl_percentage),
                "hit_targets": result.hit_targets,
                "confidence_score": result.confidence_score,
                "execution_time": result.execution_time.isoformat() if result.execution_time else None
            })
        
        return {
            "success": True,
            "data": results,
            "total_signals": len(signals),
            "message": "Batch validation completed"
        }
        
    except Exception as e:
        logger.error(f"Error in batch validation: {e}")
        raise HTTPException(status_code=500, detail=f"Batch validation failed: {str(e)}")

@router.post("/price-validation/current-prices")
async def get_current_market_prices(request: PriceRequest):
    """
    Get current prices for multiple symbols
    """
    try:
        prices = {}
        
        for symbol in request.symbols:
            price = await price_checker.get_current_price(symbol, request.preferred_exchange)
            if price:
                prices[symbol] = float(price)
            else:
                prices[symbol] = None
        
        return {
            "success": True,
            "data": prices,
            "preferred_exchange": request.preferred_exchange,
            "message": "Current prices retrieved"
        }
        
    except Exception as e:
        logger.error(f"Error fetching current prices: {e}")
        raise HTTPException(status_code=500, detail=f"Price fetch failed: {str(e)}")

@router.post("/price-validation/market-summary")
async def get_market_summary(request: MarketSummaryRequest):
    """
    Get comprehensive market summary for symbols
    """
    try:
        summary = await price_checker.get_market_summary(request.symbols)
        
        return {
            "success": True,
            "data": summary,
            "message": "Market summary retrieved"
        }
        
    except Exception as e:
        logger.error(f"Error fetching market summary: {e}")
        raise HTTPException(status_code=500, detail=f"Market summary failed: {str(e)}")

@router.post("/price-validation/historical-data")
async def get_historical_data(request: HistoricalDataRequest):
    """
    Get historical price data for technical analysis
    New endpoint for enhanced price checking functionality
    """
    try:
        # Calculate time range if hours_back is provided
        if request.hours_back and not (request.start_time and request.end_time):
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = end_time - (request.hours_back * 60 * 60 * 1000)
        else:
            start_time = request.start_time
            end_time = request.end_time
        
        if not start_time or not end_time:
            raise HTTPException(status_code=400, detail="Either provide start_time/end_time or hours_back")
        
        # Get historical data from the specified exchange
        if request.exchange == "binance":
            klines = await price_checker.get_binance_klines(
                request.symbol, start_time, end_time, request.interval
            )
        elif request.exchange == "bybit":
            # Convert interval format for Bybit (1h -> 60)
            bybit_interval = request.interval
            if request.interval == "1h":
                bybit_interval = "60"
            elif request.interval == "4h":
                bybit_interval = "240"
            elif request.interval == "1d":
                bybit_interval = "D"
            
            klines = await price_checker.get_bybit_klines(
                request.symbol, start_time, end_time, bybit_interval
            )
        else:
            raise HTTPException(status_code=400, detail="Supported exchanges: binance, bybit")
        
        # Convert Decimal values to float for JSON serialization
        formatted_klines = []
        for kline in klines:
            formatted_klines.append({
                'timestamp': kline['timestamp'],
                'open': float(kline['open']),
                'high': float(kline['high']),
                'low': float(kline['low']),
                'close': float(kline['close']),
                'volume': float(kline['volume'])
            })
        
        return {
            "success": True,
            "data": {
                "symbol": request.symbol,
                "exchange": request.exchange,
                "interval": request.interval,
                "start_time": start_time,
                "end_time": end_time,
                "klines": formatted_klines,
                "count": len(formatted_klines)
            },
            "message": f"Historical data retrieved for {request.symbol}"
        }
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        raise HTTPException(status_code=500, detail=f"Historical data fetch failed: {str(e)}")

@router.get("/price-validation/supported-symbols")
async def get_supported_symbols():
    """
    Get list of supported trading symbols with enhanced metadata
    """
    try:
        symbols = list(price_checker.supported_symbols.keys())
        exchanges = {}
        
        for symbol, exchange_list in price_checker.supported_symbols.items():
            exchanges[symbol] = exchange_list
        
        # Add real data integration status
        try:
            from models.price_checker import REAL_DATA_AVAILABLE, CRYPTO_SYMBOLS
            enhanced_symbols = list(CRYPTO_SYMBOLS) if REAL_DATA_AVAILABLE else []
        except ImportError:
            enhanced_symbols = []
            REAL_DATA_AVAILABLE = False
        
        return {
            "success": True,
            "data": {
                "symbols": symbols,
                "exchanges": exchanges,
                "total_symbols": len(symbols),
                "real_data_integration": REAL_DATA_AVAILABLE,
                "enhanced_symbols": enhanced_symbols,
                "enhanced_symbols_count": len(enhanced_symbols)
            },
            "message": "Supported symbols retrieved"
        }
        
    except Exception as e:
        logger.error(f"Error fetching supported symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported symbols: {str(e)}")

@router.get("/price-validation/symbol-metadata/{symbol}")
async def get_symbol_metadata(symbol: str):
    """
    Get metadata for a specific symbol from real_data_config
    New endpoint for enhanced symbol information
    """
    try:
        from models.price_checker import SYMBOL_METADATA, REAL_DATA_AVAILABLE
        
        if not REAL_DATA_AVAILABLE:
            return {
                "success": False,
                "data": None,
                "message": "Real data integration not available"
            }
        
        # Convert symbol format if needed (BTC/USDT -> BTCUSDT)
        symbol_key = symbol.replace('/', '')
        if not symbol_key.endswith('USDT'):
            symbol_key += 'USDT'
        
        metadata = SYMBOL_METADATA.get(symbol_key, {})
        
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Metadata not found for symbol {symbol}")
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "symbol_key": symbol_key,
                "metadata": metadata,
                "supported_exchanges": price_checker.supported_symbols.get(symbol, []),
                "default_exchange": price_checker.exchange_mapping.get(symbol, "binance")
            },
            "message": f"Metadata retrieved for {symbol}"
        }
        
    except Exception as e:
        logger.error(f"Error fetching symbol metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Metadata fetch failed: {str(e)}")

@router.get("/price-validation/health")
async def price_validation_health():
    """
    Health check for price validation service with enhanced information
    """
    try:
        # Test with BTC/USDT
        test_price = await price_checker.get_current_price("BTC/USDT")
        
        # Check real data integration
        try:
            from models.price_checker import REAL_DATA_AVAILABLE, BYBIT_API_KEY
            bybit_configured = bool(BYBIT_API_KEY)
        except ImportError:
            REAL_DATA_AVAILABLE = False
            bybit_configured = False
        
        return {
            "success": True,
            "status": "healthy",
            "test_symbol": "BTC/USDT",
            "test_price": float(test_price) if test_price else None,
            "cache_size": len(price_checker._price_cache),
            "supported_symbols_count": len(price_checker.supported_symbols),
            "real_data_integration": REAL_DATA_AVAILABLE,
            "bybit_api_configured": bybit_configured,
            "features": {
                "current_prices": True,
                "historical_data": True,
                "signal_validation": True,
                "batch_processing": True,
                "multi_exchange": True,
                "caching": True
            },
            "message": "Price validation service is healthy"
        }
        
    except Exception as e:
        logger.error(f"Price validation health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "message": "Price validation service is experiencing issues"
        } 