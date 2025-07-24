"""
Celery tasks for automated trading
"""
import asyncio
from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.services.trading_service import TradingService
from app.services.risk_service import RiskService
from app.models.trading import TradingAccount, TradingPosition
from app.models.signal import Signal

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery('crypto_analytics_trading')

@celery_app.task
def update_all_positions():
    """Update prices and PnL for all open positions"""
    try:
        db = next(get_db())
        trading_service = TradingService(db)
        
        # Get all active trading accounts
        accounts = db.query(TradingAccount).filter(
            TradingAccount.is_active == True,
            TradingAccount.auto_trading_enabled == True
        ).all()
        
        updated_count = 0
        for account in accounts:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(trading_service.update_positions(account.id))
                    updated_count += result.get("positions_updated", 0)
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"Error updating positions for account {account.id}: {e}")
        
        logger.info(f"Updated {updated_count} positions across {len(accounts)} accounts")
        return {"success": True, "positions_updated": updated_count}
        
    except Exception as e:
        logger.error(f"Error in update_all_positions task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task
def check_stop_losses():
    """Check and execute stop losses for all open positions"""
    try:
        db = next(get_db())
        risk_service = RiskService(db)
        trading_service = TradingService(db)
        
        # Get all open positions
        open_positions = db.query(TradingPosition).filter(
            TradingPosition.is_open == True
        ).all()
        
        executed_count = 0
        for position in open_positions:
            try:
                # Check stop loss
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    should_close = loop.run_until_complete(risk_service.check_stop_loss_trigger(position))
                    
                    if should_close:
                        # Close position
                        from app.schemas.trading import ClosePositionRequest
                        close_request = ClosePositionRequest(position_id=position.id)
                        
                        close_result = loop.run_until_complete(
                            trading_service.close_position(close_request, position.account.user_id)
                        )
                        
                        if close_result:
                            executed_count += 1
                            logger.info(f"Stop loss executed for position {position.id}")
                            
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"Error checking stop loss for position {position.id}: {e}")
        
        logger.info(f"Executed {executed_count} stop losses")
        return {"success": True, "stop_losses_executed": executed_count}
        
    except Exception as e:
        logger.error(f"Error in check_stop_losses task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task
def check_take_profits():
    """Check and execute take profits for all open positions"""
    try:
        db = next(get_db())
        risk_service = RiskService(db)
        trading_service = TradingService(db)
        
        # Get all open positions
        open_positions = db.query(TradingPosition).filter(
            TradingPosition.is_open == True
        ).all()
        
        executed_count = 0
        for position in open_positions:
            try:
                # Check take profit
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    should_close = loop.run_until_complete(risk_service.check_take_profit_trigger(position))
                    
                    if should_close:
                        # Close position
                        from app.schemas.trading import ClosePositionRequest
                        close_request = ClosePositionRequest(position_id=position.id)
                        
                        close_result = loop.run_until_complete(
                            trading_service.close_position(close_request, position.account.user_id)
                        )
                        
                        if close_result:
                            executed_count += 1
                            logger.info(f"Take profit executed for position {position.id}")
                            
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"Error checking take profit for position {position.id}: {e}")
        
        logger.info(f"Executed {executed_count} take profits")
        return {"success": True, "take_profits_executed": executed_count}
        
    except Exception as e:
        logger.error(f"Error in check_take_profits task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task
def update_trailing_stops():
    """Update trailing stops for all open positions"""
    try:
        db = next(get_db())
        risk_service = RiskService(db)
        
        # Get all open positions with trailing stops
        open_positions = db.query(TradingPosition).filter(
            TradingPosition.is_open == True,
            TradingPosition.trailing_stop == True
        ).all()
        
        updated_count = 0
        for position in open_positions:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    new_stop_loss = loop.run_until_complete(risk_service.update_trailing_stop(position))
                    
                    if new_stop_loss:
                        position.stop_loss = new_stop_loss
                        updated_count += 1
                        logger.info(f"Updated trailing stop for position {position.id}: {new_stop_loss}")
                        
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"Error updating trailing stop for position {position.id}: {e}")
        
        db.commit()
        logger.info(f"Updated {updated_count} trailing stops")
        return {"success": True, "trailing_stops_updated": updated_count}
        
    except Exception as e:
        logger.error(f"Error in update_trailing_stops task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task
def execute_pending_signals():
    """Execute pending signals for auto-trading accounts"""
    try:
        db = next(get_db())
        trading_service = TradingService(db)
        
        # Get all active auto-trading accounts
        auto_trading_accounts = db.query(TradingAccount).filter(
            TradingAccount.is_active == True,
            TradingAccount.auto_trading_enabled == True
        ).all()
        
        # Get recent signals with high confidence
        recent_signals = db.query(Signal).filter(
            Signal.created_at >= datetime.utcnow() - timedelta(hours=1),
            Signal.confidence >= 0.7,
            Signal.status == "active"
        ).all()
        
        executed_count = 0
        for account in auto_trading_accounts:
            for signal in recent_signals:
                try:
                    # Check if signal already executed for this account
                    existing_position = db.query(TradingPosition).filter(
                        TradingPosition.account_id == account.id,
                        TradingPosition.signal_id == signal.id
                    ).first()
                    
                    if existing_position:
                        continue
                    
                    # Execute signal
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        position = loop.run_until_complete(
                            trading_service.execute_signal(signal.id, account.id)
                        )
                        
                        if position:
                            executed_count += 1
                            logger.info(f"Signal {signal.id} executed for account {account.id}")
                            
                    finally:
                        loop.close()
                        
                except Exception as e:
                    logger.error(f"Error executing signal {signal.id} for account {account.id}: {e}")
        
        logger.info(f"Executed {executed_count} signals")
        return {"success": True, "signals_executed": executed_count}
        
    except Exception as e:
        logger.error(f"Error in execute_pending_signals task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task
def sync_account_balances():
    """Sync account balances with exchanges"""
    try:
        db = next(get_db())
        
        # Get all active trading accounts
        accounts = db.query(TradingAccount).filter(
            TradingAccount.is_active == True
        ).all()
        
        synced_count = 0
        for account in accounts:
            try:
                # This would sync with actual exchange in production
                # For now, we'll simulate balance updates
                import random
                
                # Simulate balance changes
                balance_change = random.uniform(-100, 100)
                account.total_balance += balance_change
                account.available_balance = account.total_balance * 0.95  # Keep 5% in positions
                account.last_sync_at = datetime.utcnow()
                
                synced_count += 1
                logger.info(f"Synced balance for account {account.id}")
                
            except Exception as e:
                logger.error(f"Error syncing balance for account {account.id}: {e}")
        
        db.commit()
        logger.info(f"Synced {synced_count} account balances")
        return {"success": True, "accounts_synced": synced_count}
        
    except Exception as e:
        logger.error(f"Error in sync_account_balances task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task
def generate_trading_report():
    """Generate daily trading report"""
    try:
        db = next(get_db())
        trading_service = TradingService(db)
        
        # Get all trading accounts
        accounts = db.query(TradingAccount).filter(
            TradingAccount.is_active == True
        ).all()
        
        report_data = {
            "date": datetime.utcnow().date().isoformat(),
            "total_accounts": len(accounts),
            "active_accounts": len([acc for acc in accounts if acc.auto_trading_enabled]),
            "total_positions": 0,
            "open_positions": 0,
            "total_pnl": 0.0,
            "accounts": []
        }
        
        for account in accounts:
            try:
                stats = trading_service.get_trading_stats(account.id)
                
                account_data = {
                    "account_id": account.id,
                    "name": account.name,
                    "exchange": account.exchange.value,
                    "total_pnl": float(stats.get("total_pnl", 0)),
                    "open_positions": stats.get("open_positions_count", 0),
                    "total_positions": stats.get("total_positions_count", 0),
                    "win_rate": stats.get("win_rate", 0)
                }
                
                report_data["accounts"].append(account_data)
                report_data["total_positions"] += account_data["total_positions"]
                report_data["open_positions"] += account_data["open_positions"]
                report_data["total_pnl"] += account_data["total_pnl"]
                
            except Exception as e:
                logger.error(f"Error generating report for account {account.id}: {e}")
        
        logger.info(f"Generated trading report for {len(accounts)} accounts")
        return {"success": True, "report": report_data}
        
    except Exception as e:
        logger.error(f"Error in generate_trading_report task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close() 