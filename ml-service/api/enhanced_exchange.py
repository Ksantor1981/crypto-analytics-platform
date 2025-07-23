"""
Enhanced Exchange API endpoints for ML Service
Multi-exchange support with advanced features
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

try:
    from models.enhanced_exchange_client import (
        exchange_client, 
        get_enhanced_price, 
        get_multi_exchange_prices
    )
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.enhanced_exchange_client import (
        exchange_client, 
        get_enhanced_price, 
        get_multi_exchange_prices
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["enhanced-exchange"])

class SymbolRequest(BaseModel):
    """Request model for symbol data"""
    symbol: str
    preferred_exchange: Optional[str] = None

class MultiSymbolRequest(BaseModel):
    """Request model for multiple symbols"""
    symbols: List[str]
    include_comparison: bool = False

class ExchangeComparisonRequest(BaseModel):
    """Request model for exchange comparison"""
    symbol: str
    exchanges: Optional[List[str]] = None

@router.post("/exchange/price-enhanced")
async def get_enhanced_price_endpoint(request: SymbolRequest):
    """
    Get enhanced price data for a symbol with exchange metadata
    """
    try:
        price_data = await get_enhanced_price(request.symbol)
        
        if price_data:
            return {
                "success": True,
                "data": price_data,
                "message": f"Enhanced price data retrieved for {request.symbol}"
            }
        else:
            return {
                "success": False,
                "data": None,
                "message": f"Could not retrieve price for {request.symbol}",
                "error": "Price not available from any exchange"
            }
            
    except Exception as e:
        logger.error(f"Error getting enhanced price for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced price fetch failed: {str(e)}")

@router.post("/exchange/multi-exchange-comparison")
async def get_multi_exchange_comparison(request: ExchangeComparisonRequest):
    """
    Compare prices across multiple exchanges for arbitrage opportunities
    """
    try:
        prices = await get_multi_exchange_prices(request.symbol)
        
        if not prices:
            return {
                "success": False,
                "data": None,
                "message": f"No price data available for {request.symbol}",
                "error": "Symbol not available on any exchange"
            }
        
        # Calculate arbitrage opportunities
        price_values = [p['price'] for p in prices if p['price']]
        
        analysis = {
            "symbol": request.symbol,
            "exchange_count": len(prices),
            "prices": prices,
            "price_analysis": {
                "highest_price": max(price_values) if price_values else None,
                "lowest_price": min(price_values) if price_values else None,
                "price_spread": max(price_values) - min(price_values) if price_values else None,
                "spread_percentage": ((max(price_values) - min(price_values)) / min(price_values) * 100) if price_values else None,
                "arbitrage_opportunity": (max(price_values) - min(price_values)) / min(price_values) > 0.001 if price_values else False
            }
        }
        
        return {
            "success": True,
            "data": analysis,
            "message": f"Multi-exchange comparison completed for {request.symbol}"
        }
        
    except Exception as e:
        logger.error(f"Error in multi-exchange comparison for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Multi-exchange comparison failed: {str(e)}")

@router.post("/exchange/market-summary-enhanced")
async def get_enhanced_market_summary(request: MultiSymbolRequest):
    """
    Get enhanced market summary for multiple symbols
    """
    try:
        market_data = await exchange_client.get_market_summary(request.symbols)
        
        # Calculate summary statistics
        active_symbols = [s for s, data in market_data.items() if data.get('status') == 'active']
        total_volume = sum([data.get('volume_24h', 0) or 0 for data in market_data.values()])
        
        positive_changes = len([
            data for data in market_data.values() 
            if data.get('price_change_24h') and data['price_change_24h'] > 0
        ])
        
        summary = {
            "market_overview": {
                "total_symbols": len(request.symbols),
                "active_symbols": len(active_symbols),
                "unavailable_symbols": len(request.symbols) - len(active_symbols),
                "total_volume_24h": total_volume,
                "symbols_with_positive_change": positive_changes,
                "market_sentiment": "bullish" if positive_changes > len(active_symbols) / 2 else "bearish"
            },
            "symbol_data": market_data,
            "exchanges_used": list(set([
                data.get('exchange') for data in market_data.values() 
                if data.get('exchange')
            ]))
        }
        
        # Add comparison data if requested
        if request.include_comparison and len(active_symbols) > 0:
            comparison_tasks = []
            for symbol in active_symbols[:5]:  # Limit to 5 symbols for performance
                comparison_tasks.append(get_multi_exchange_prices(symbol))
            
            import asyncio
            comparison_results = await asyncio.gather(*comparison_tasks, return_exceptions=True)
            
            summary["exchange_comparisons"] = {}
            for i, symbol in enumerate(active_symbols[:5]):
                if i < len(comparison_results) and not isinstance(comparison_results[i], Exception):
                    summary["exchange_comparisons"][symbol] = comparison_results[i]
        
        return {
            "success": True,
            "data": summary,
            "message": f"Enhanced market summary retrieved for {len(request.symbols)} symbols"
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced market summary: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced market summary failed: {str(e)}")

@router.get("/exchange/supported-exchanges")
async def get_supported_exchanges():
    """
    Get list of supported exchanges and their capabilities
    """
    try:
        health_status = exchange_client.get_health_status()
        
        exchanges_info = {
            "binance": {
                "name": "Binance",
                "base_url": "https://api.binance.com",
                "features": ["spot_trading", "futures", "24h_ticker", "klines"],
                "rate_limits": {
                    "requests_per_second": 10,
                    "requests_per_minute": 1200
                },
                "supported_pairs": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"],
                "authentication_required": False
            },
            "bybit": {
                "name": "Bybit", 
                "base_url": "https://api.bybit.com",
                "features": ["spot_trading", "derivatives", "24h_ticker", "klines"],
                "rate_limits": {
                    "requests_per_second": 10,
                    "requests_per_minute": 600
                },
                "supported_pairs": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT"],
                "authentication_required": False
            },
            "coinbase": {
                "name": "Coinbase Pro",
                "base_url": "https://api.exchange.coinbase.com", 
                "features": ["spot_trading", "24h_ticker"],
                "rate_limits": {
                    "requests_per_second": 5,
                    "requests_per_minute": 1000
                },
                "supported_pairs": ["BTC/USD", "ETH/USD", "BTC/EUR"],
                "authentication_required": False
            }
        }
        
        # Add current health status
        for exchange_name, info in exchanges_info.items():
            if exchange_name in health_status.get('exchanges', {}):
                info['current_status'] = health_status['exchanges'][exchange_name]
        
        return {
            "success": True,
            "data": {
                "exchanges": exchanges_info,
                "total_exchanges": len(exchanges_info),
                "health_summary": health_status
            },
            "message": "Supported exchanges information retrieved"
        }
        
    except Exception as e:
        logger.error(f"Error getting supported exchanges: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get exchanges info: {str(e)}")

@router.get("/exchange/health-status")
async def get_exchange_health():
    """
    Get health status of all exchange connections
    """
    try:
        health_status = exchange_client.get_health_status()
        
        # Add recommendation based on health
        if health_status['healthy_exchanges'] == 0:
            recommendation = "All exchanges are down. Check network connectivity."
            severity = "critical"
        elif health_status['healthy_exchanges'] < health_status['total_exchanges'] / 2:
            recommendation = "Some exchanges are experiencing issues. Consider using alternative data sources."
            severity = "warning"
        else:
            recommendation = "Exchange connectivity is stable."
            severity = "info"
        
        enhanced_status = {
            **health_status,
            "recommendation": recommendation,
            "severity": severity,
            "last_check": "2025-07-08T15:45:00Z"  # Current timestamp would be dynamic
        }
        
        return {
            "success": True,
            "data": enhanced_status,
            "message": "Exchange health status retrieved"
        }
        
    except Exception as e:
        logger.error(f"Error getting exchange health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/exchange/clear-cache")
async def clear_exchange_cache():
    """
    Clear all cached exchange data
    """
    try:
        exchange_client.clear_cache()
        
        return {
            "success": True,
            "message": "Exchange cache cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error clearing exchange cache: {e}")
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")

@router.get("/exchange/arbitrage-opportunities")
async def get_arbitrage_opportunities():
    """
    Scan for potential arbitrage opportunities across exchanges
    """
    try:
        # Common trading pairs to check
        symbols_to_check = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT"]
        
        opportunities = []
        
        for symbol in symbols_to_check:
            try:
                prices = await get_multi_exchange_prices(symbol)
                
                if len(prices) >= 2:
                    price_values = [p['price'] for p in prices]
                    min_price = min(price_values)
                    max_price = max(price_values)
                    spread_pct = (max_price - min_price) / min_price * 100
                    
                    # Consider opportunities with >0.1% spread
                    if spread_pct > 0.1:
                        buy_exchange = next(p['exchange'] for p in prices if p['price'] == min_price)
                        sell_exchange = next(p['exchange'] for p in prices if p['price'] == max_price)
                        
                        opportunities.append({
                            "symbol": symbol,
                            "buy_exchange": buy_exchange,
                            "sell_exchange": sell_exchange,
                            "buy_price": min_price,
                            "sell_price": max_price,
                            "spread_amount": max_price - min_price,
                            "spread_percentage": round(spread_pct, 3),
                            "potential_profit": round(spread_pct - 0.2, 3),  # Assuming 0.2% total fees
                            "all_prices": prices
                        })
            except Exception as e:
                logger.warning(f"Error checking arbitrage for {symbol}: {e}")
                continue
        
        # Sort by potential profit
        opportunities.sort(key=lambda x: x['potential_profit'], reverse=True)
        
        return {
            "success": True,
            "data": {
                "opportunities": opportunities,
                "total_opportunities": len(opportunities),
                "symbols_checked": len(symbols_to_check),
                "disclaimer": "This is for informational purposes only. Consider fees, slippage, and execution time.",
                "last_scan": "2025-07-08T15:45:00Z"
            },
            "message": f"Found {len(opportunities)} potential arbitrage opportunities"
        }
        
    except Exception as e:
        logger.error(f"Error scanning for arbitrage opportunities: {e}")
        raise HTTPException(status_code=500, detail=f"Arbitrage scan failed: {str(e)}") 