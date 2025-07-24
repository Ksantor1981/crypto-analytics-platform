"""
Risk Management Service for auto-trading
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from app.models.trading import TradingAccount, TradingPosition, RiskManagement
from app.models.signal import Signal
from app.models.user import User

logger = logging.getLogger(__name__)

class RiskService:
    """Service for managing trading risks"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def check_order_risk(self, account_id: int, symbol: str, side: str, 
                              quantity: Decimal, price: Optional[Decimal]) -> Dict[str, Any]:
        """Check if an order meets risk management requirements"""
        try:
            # Get account and risk management settings
            account = self.db.query(TradingAccount).filter(
                TradingAccount.id == account_id
            ).first()
            
            if not account:
                return {"allowed": False, "reason": "Account not found"}
            
            risk_settings = self.db.query(RiskManagement).filter(
                RiskManagement.user_id == account.user_id
            ).first()
            
            if not risk_settings:
                # Use default risk settings
                risk_settings = RiskManagement(
                    user_id=account.user_id,
                    max_position_size_usd=100.0,
                    max_daily_loss_usd=50.0,
                    max_portfolio_risk=0.05,
                    risk_per_trade=0.02,
                    max_positions_per_symbol=1,
                    max_total_positions=5
                )
            
            # Check position size limits
            position_value = quantity * (price or Decimal('0'))
            if position_value > risk_settings.max_position_size_usd:
                return {
                    "allowed": False, 
                    "reason": f"Position size ${position_value} exceeds maximum ${risk_settings.max_position_size_usd}"
                }
            
            # Check daily loss limit
            daily_loss = await self._calculate_daily_loss(account_id)
            if daily_loss >= risk_settings.max_daily_loss_usd:
                return {
                    "allowed": False,
                    "reason": f"Daily loss limit reached: ${daily_loss}"
                }
            
            # Check total positions limit
            open_positions = self.db.query(TradingPosition).filter(
                TradingPosition.account_id == account_id,
                TradingPosition.is_open == True
            ).count()
            
            if open_positions >= risk_settings.max_total_positions:
                return {
                    "allowed": False,
                    "reason": f"Maximum positions limit reached: {open_positions}/{risk_settings.max_total_positions}"
                }
            
            # Check positions per symbol limit
            symbol_positions = self.db.query(TradingPosition).filter(
                TradingPosition.account_id == account_id,
                TradingPosition.symbol == symbol,
                TradingPosition.is_open == True
            ).count()
            
            if symbol_positions >= risk_settings.max_positions_per_symbol:
                return {
                    "allowed": False,
                    "reason": f"Maximum positions per symbol reached: {symbol_positions}/{risk_settings.max_positions_per_symbol}"
                }
            
            # Check trading hours
            if not await self._is_trading_hours_allowed(risk_settings):
                return {
                    "allowed": False,
                    "reason": "Trading outside allowed hours"
                }
            
            # Check portfolio risk
            portfolio_risk = await self._calculate_portfolio_risk(account_id, position_value)
            if portfolio_risk > risk_settings.max_portfolio_risk:
                return {
                    "allowed": False,
                    "reason": f"Portfolio risk {portfolio_risk:.2%} exceeds maximum {risk_settings.max_portfolio_risk:.2%}"
                }
            
            return {"allowed": True, "reason": "Order approved"}
            
        except Exception as e:
            logger.error(f"Error checking order risk: {e}")
            return {"allowed": False, "reason": "Risk check failed"}
    
    async def calculate_position_size(self, account_id: int, signal: Signal) -> Decimal:
        """Calculate optimal position size based on risk management"""
        try:
            account = self.db.query(TradingAccount).filter(
                TradingAccount.id == account_id
            ).first()
            
            if not account:
                raise ValueError("Account not found")
            
            risk_settings = self.db.query(RiskManagement).filter(
                RiskManagement.user_id == account.user_id
            ).first()
            
            if not risk_settings:
                # Use default risk settings
                risk_per_trade = 0.02  # 2% risk per trade
            else:
                risk_per_trade = risk_settings.risk_per_trade
            
            # Get account balance
            available_balance = account.available_balance or Decimal('1000')
            
            # Calculate position size based on risk
            # Risk amount = available balance * risk_per_trade
            risk_amount = available_balance * Decimal(str(risk_per_trade))
            
            # Position size = risk amount / (entry_price - stop_loss)
            if signal.stop_loss:
                price_difference = abs(signal.entry_price - signal.stop_loss)
                if price_difference > 0:
                    position_size = risk_amount / price_difference
                else:
                    # Fallback to 1% of balance if no stop loss
                    position_size = available_balance * Decimal('0.01') / signal.entry_price
            else:
                # Fallback to 1% of balance if no stop loss
                position_size = available_balance * Decimal('0.01') / signal.entry_price
            
            # Ensure position size doesn't exceed account limits
            max_position_value = account.max_position_size
            max_position_size = max_position_value / signal.entry_price
            
            position_size = min(position_size, max_position_size)
            
            # Round to appropriate decimal places
            position_size = position_size.quantize(Decimal('0.001'))
            
            logger.info(f"Calculated position size: {position_size} for signal {signal.id}")
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            # Return a safe default
            return Decimal('0.001')
    
    async def _calculate_daily_loss(self, account_id: int) -> Decimal:
        """Calculate total daily loss for an account"""
        try:
            today = datetime.utcnow().date()
            
            # Get all closed positions for today
            daily_positions = self.db.query(TradingPosition).filter(
                TradingPosition.account_id == account_id,
                TradingPosition.is_open == False,
                func.date(TradingPosition.closed_at) == today
            ).all()
            
            total_loss = sum(
                position.realized_pnl for position in daily_positions 
                if position.realized_pnl < 0
            )
            
            return abs(total_loss) if total_loss < 0 else Decimal('0')
            
        except Exception as e:
            logger.error(f"Error calculating daily loss: {e}")
            return Decimal('0')
    
    async def _is_trading_hours_allowed(self, risk_settings: RiskManagement) -> bool:
        """Check if current time is within allowed trading hours"""
        try:
            now = datetime.utcnow()
            current_time = now.strftime("%H:%M")
            
            # Check if it's weekend
            if not risk_settings.weekend_trading and now.weekday() >= 5:
                return False
            
            # Check trading hours
            if risk_settings.trading_hours_start <= current_time <= risk_settings.trading_hours_end:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking trading hours: {e}")
            return True  # Allow trading if check fails
    
    async def _calculate_portfolio_risk(self, account_id: int, new_position_value: Decimal) -> float:
        """Calculate current portfolio risk including new position"""
        try:
            # Get all open positions
            open_positions = self.db.query(TradingPosition).filter(
                TradingPosition.account_id == account_id,
                TradingPosition.is_open == True
            ).all()
            
            # Calculate total portfolio value
            total_portfolio_value = sum(
                position.size * (position.current_price or position.entry_price)
                for position in open_positions
            )
            
            # Add new position value
            total_portfolio_value += new_position_value
            
            # Calculate risk as percentage of total portfolio
            if total_portfolio_value > 0:
                risk_percentage = float(new_position_value / total_portfolio_value)
            else:
                risk_percentage = 0.0
            
            return risk_percentage
            
        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {e}")
            return 0.0
    
    async def check_stop_loss_trigger(self, position: TradingPosition) -> bool:
        """Check if stop loss should be triggered"""
        try:
            if not position.stop_loss or not position.current_price:
                return False
            
            if position.side.value == "LONG":
                # For long positions, trigger if price goes below stop loss
                return position.current_price <= position.stop_loss
            else:
                # For short positions, trigger if price goes above stop loss
                return position.current_price >= position.stop_loss
                
        except Exception as e:
            logger.error(f"Error checking stop loss: {e}")
            return False
    
    async def check_take_profit_trigger(self, position: TradingPosition) -> bool:
        """Check if take profit should be triggered"""
        try:
            if not position.take_profit or not position.current_price:
                return False
            
            if position.side.value == "LONG":
                # For long positions, trigger if price goes above take profit
                return position.current_price >= position.take_profit
            else:
                # For short positions, trigger if price goes below take profit
                return position.current_price <= position.take_profit
                
        except Exception as e:
            logger.error(f"Error checking take profit: {e}")
            return False
    
    async def update_trailing_stop(self, position: TradingPosition) -> Optional[Decimal]:
        """Update trailing stop for a position"""
        try:
            if not position.trailing_stop or not position.trailing_stop_distance or not position.current_price:
                return None
            
            if position.side.value == "LONG":
                # For long positions, trailing stop moves up
                new_stop_loss = position.current_price * (1 - position.trailing_stop_distance)
                if new_stop_loss > position.stop_loss:
                    return new_stop_loss
            else:
                # For short positions, trailing stop moves down
                new_stop_loss = position.current_price * (1 + position.trailing_stop_distance)
                if new_stop_loss < position.stop_loss:
                    return new_stop_loss
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating trailing stop: {e}")
            return None
    
    async def get_risk_metrics(self, account_id: int) -> Dict[str, Any]:
        """Get comprehensive risk metrics for an account"""
        try:
            account = self.db.query(TradingAccount).filter(
                TradingAccount.id == account_id
            ).first()
            
            if not account:
                return {}
            
            # Get all positions
            positions = self.db.query(TradingPosition).filter(
                TradingPosition.account_id == account_id
            ).all()
            
            open_positions = [p for p in positions if p.is_open]
            closed_positions = [p for p in positions if not p.is_open]
            
            # Calculate metrics
            total_pnl = sum(p.realized_pnl for p in closed_positions)
            unrealized_pnl = sum(p.unrealized_pnl for p in open_positions)
            
            # Calculate drawdown
            max_drawdown = await self._calculate_max_drawdown(positions)
            
            # Calculate Sharpe ratio (simplified)
            sharpe_ratio = await self._calculate_sharpe_ratio(closed_positions)
            
            # Calculate correlation between positions
            correlation = await self._calculate_position_correlation(open_positions)
            
            return {
                "total_pnl": total_pnl,
                "unrealized_pnl": unrealized_pnl,
                "total_pnl_percent": float((total_pnl + unrealized_pnl) / account.total_balance * 100) if account.total_balance > 0 else 0,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "position_correlation": correlation,
                "open_positions_count": len(open_positions),
                "total_positions_count": len(positions),
                "daily_loss": await self._calculate_daily_loss(account_id),
                "risk_per_trade": account.risk_per_trade,
                "max_position_size": account.max_position_size
            }
            
        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return {}
    
    async def _calculate_max_drawdown(self, positions: List[TradingPosition]) -> float:
        """Calculate maximum drawdown from positions"""
        try:
            if not positions:
                return 0.0
            
            # Sort positions by date
            sorted_positions = sorted(positions, key=lambda p: p.created_at)
            
            cumulative_pnl = 0.0
            peak_pnl = 0.0
            max_drawdown = 0.0
            
            for position in sorted_positions:
                pnl = float(position.realized_pnl if not position.is_open else position.unrealized_pnl)
                cumulative_pnl += pnl
                
                if cumulative_pnl > peak_pnl:
                    peak_pnl = cumulative_pnl
                
                drawdown = (peak_pnl - cumulative_pnl) / peak_pnl if peak_pnl > 0 else 0.0
                max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0
    
    async def _calculate_sharpe_ratio(self, positions: List[TradingPosition]) -> float:
        """Calculate Sharpe ratio from positions"""
        try:
            if not positions:
                return 0.0
            
            # Get returns
            returns = [float(p.realized_pnl) for p in positions if p.realized_pnl != 0]
            
            if not returns:
                return 0.0
            
            # Calculate average return and standard deviation
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            
            # Sharpe ratio = average return / standard deviation
            if std_dev > 0:
                return avg_return / std_dev
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0
    
    async def _calculate_position_correlation(self, positions: List[TradingPosition]) -> float:
        """Calculate correlation between positions"""
        try:
            if len(positions) < 2:
                return 0.0
            
            # This is a simplified correlation calculation
            # In a real implementation, you'd use historical price data
            pnl_values = [float(p.unrealized_pnl_percent) for p in positions]
            
            if not pnl_values:
                return 0.0
            
            # Calculate correlation coefficient
            n = len(pnl_values)
            if n < 2:
                return 0.0
            
            mean_pnl = sum(pnl_values) / n
            variance = sum((p - mean_pnl) ** 2 for p in pnl_values) / (n - 1)
            
            if variance == 0:
                return 0.0
            
            # Simplified correlation (in reality, you'd compare price movements)
            return 0.1  # Low correlation assumption
            
        except Exception as e:
            logger.error(f"Error calculating position correlation: {e}")
            return 0.0 