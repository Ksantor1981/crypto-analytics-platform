"""
Trading Service for auto-trading functionality
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, extract
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import asyncio
from cryptography.fernet import Fernet
import os

from app.models.trading import (
    TradingAccount, TradingPosition, TradingOrder, RiskManagement,
    OrderStatus, PositionSide, OrderType, OrderSide, StrategyType
)
from app.models.user import User
from app.models.signal import Signal
from app.schemas.trading import (
    TradingAccountCreate, TradingAccountUpdate, TradingPositionCreate,
    TradingOrderCreate, PlaceOrderRequest, ClosePositionRequest
)
from app.core.config import get_settings
from app.services.exchange_service import ExchangeService
from app.services.risk_service import RiskService

logger = logging.getLogger(__name__)

class TradingService:
    """Main trading service for auto-trading operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.exchange_service = ExchangeService()
        self.risk_service = RiskService(db)
        
        # Initialize encryption key for API credentials
        self.encryption_key = os.getenv("TRADING_ENCRYPTION_KEY")
        if not self.encryption_key:
            logger.warning("TRADING_ENCRYPTION_KEY not set - using default key")
            self.encryption_key = "default-encryption-key-for-development-only"
        
        self.cipher = Fernet(self.encryption_key.encode())
    
    def create_trading_account(self, user_id: int, account_data: TradingAccountCreate) -> TradingAccount:
        """Create a new trading account"""
        try:
            # Validate API credentials with exchange
            is_valid = self.exchange_service.validate_credentials(
                exchange=account_data.exchange,
                api_key=account_data.api_key,
                api_secret=account_data.api_secret,
                passphrase=account_data.passphrase
            )
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid API credentials for the exchange"
                )
            
            # Encrypt API credentials
            encrypted_api_key = self.cipher.encrypt(account_data.api_key.encode()).decode()
            encrypted_api_secret = self.cipher.encrypt(account_data.api_secret.encode()).decode()
            encrypted_passphrase = None
            if account_data.passphrase:
                encrypted_passphrase = self.cipher.encrypt(account_data.passphrase.encode()).decode()
            
            # Create trading account
            trading_account = TradingAccount(
                user_id=user_id,
                name=account_data.name,
                exchange=account_data.exchange,
                api_key_encrypted=encrypted_api_key,
                api_secret_encrypted=encrypted_api_secret,
                passphrase_encrypted=encrypted_passphrase,
                max_position_size=account_data.max_position_size,
                max_daily_loss=account_data.max_daily_loss,
                risk_per_trade=account_data.risk_per_trade,
                auto_trading_enabled=account_data.auto_trading_enabled,
                max_open_positions=account_data.max_open_positions,
                min_signal_confidence=account_data.min_signal_confidence
            )
            
            self.db.add(trading_account)
            self.db.commit()
            self.db.refresh(trading_account)
            
            logger.info(f"Trading account created for user {user_id}: {trading_account.name}")
            return trading_account
            
        except Exception as e:
            logger.error(f"Error creating trading account: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create trading account"
            )
    
    def get_user_accounts(self, user_id: int) -> List[TradingAccount]:
        """Get all trading accounts for a user"""
        return self.db.query(TradingAccount).filter(
            TradingAccount.user_id == user_id,
            TradingAccount.is_active == True
        ).all()
    
    def get_account_positions(self, account_id: int) -> List[TradingPosition]:
        """Get all positions for a trading account"""
        return self.db.query(TradingPosition).filter(
            TradingPosition.account_id == account_id
        ).order_by(TradingPosition.created_at.desc()).all()
    
    def get_open_positions(self, account_id: int) -> List[TradingPosition]:
        """Get open positions for a trading account"""
        return self.db.query(TradingPosition).filter(
            TradingPosition.account_id == account_id,
            TradingPosition.is_open == True
        ).all()
    
    async def place_order(self, order_request: PlaceOrderRequest, user_id: int) -> TradingOrder:
        """Place a trading order"""
        try:
            # Get trading account
            account = self.db.query(TradingAccount).filter(
                TradingAccount.id == order_request.account_id,
                TradingAccount.user_id == user_id,
                TradingAccount.is_active == True
            ).first()
            
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Trading account not found"
                )
            
            # Check risk management rules
            risk_check = await self.risk_service.check_order_risk(
                account_id=account.id,
                symbol=order_request.symbol,
                side=order_request.side,
                quantity=order_request.quantity,
                price=order_request.price
            )
            
            if not risk_check["allowed"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Order rejected by risk management: {risk_check['reason']}"
                )
            
            # Decrypt API credentials
            api_key = self.cipher.decrypt(account.api_key_encrypted.encode()).decode()
            api_secret = self.cipher.decrypt(account.api_secret_encrypted.encode()).decode()
            passphrase = None
            if account.passphrase_encrypted:
                passphrase = self.cipher.decrypt(account.passphrase_encrypted.encode()).decode()
            
            # Place order on exchange
            exchange_order = await self.exchange_service.place_order(
                exchange=account.exchange,
                api_key=api_key,
                api_secret=api_secret,
                passphrase=passphrase,
                symbol=order_request.symbol,
                side=order_request.side,
                order_type=order_request.order_type,
                quantity=order_request.quantity,
                price=order_request.price,
                time_in_force=order_request.time_in_force
            )
            
            # Create order record
            trading_order = TradingOrder(
                account_id=account.id,
                position_id=order_request.position_id,
                symbol=order_request.symbol,
                order_type=order_request.order_type,
                side=order_request.side,
                quantity=order_request.quantity,
                price=order_request.price,
                status=OrderStatus.PENDING,
                exchange_order_id=exchange_order.get("order_id"),
                exchange_client_order_id=exchange_order.get("client_order_id")
            )
            
            self.db.add(trading_order)
            self.db.commit()
            self.db.refresh(trading_order)
            
            logger.info(f"Order placed: {trading_order.id} for account {account.id}")
            return trading_order
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to place order"
            )
    
    async def close_position(self, close_request: ClosePositionRequest, user_id: int) -> TradingOrder:
        """Close a trading position"""
        try:
            # Get position
            position = self.db.query(TradingPosition).join(TradingAccount).filter(
                TradingPosition.id == close_request.position_id,
                TradingAccount.user_id == user_id,
                TradingPosition.is_open == True
            ).first()
            
            if not position:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Position not found or already closed"
                )
            
            # Determine close quantity
            close_quantity = close_request.quantity or position.size
            
            if close_quantity > position.size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Close quantity cannot exceed position size"
                )
            
            # Determine close side (opposite of position side)
            close_side = OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY
            
            # Place closing order
            order_request = PlaceOrderRequest(
                account_id=position.account_id,
                symbol=position.symbol,
                side=close_side,
                order_type=OrderType.MARKET,
                quantity=close_quantity
            )
            
            closing_order = await self.place_order(order_request, user_id)
            
            # Update position if fully closed
            if close_quantity == position.size:
                position.is_open = False
                position.closed_at = datetime.utcnow()
                self.db.commit()
            
            return closing_order
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to close position"
            )
    
    async def execute_signal(self, signal_id: int, account_id: int) -> TradingPosition:
        """Execute a trading signal"""
        try:
            # Get signal
            signal = self.db.query(Signal).filter(Signal.id == signal_id).first()
            if not signal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Signal not found"
                )
            
            # Get account
            account = self.db.query(TradingAccount).filter(
                TradingAccount.id == account_id,
                TradingAccount.is_active == True
            ).first()
            
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Trading account not found"
                )
            
            # Check if auto-trading is enabled
            if not account.auto_trading_enabled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Auto-trading is disabled for this account"
                )
            
            # Check signal confidence
            if signal.confidence < account.min_signal_confidence:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Signal confidence {signal.confidence} below minimum {account.min_signal_confidence}"
                )
            
            # Calculate position size based on risk management
            position_size = await self.risk_service.calculate_position_size(
                account_id=account_id,
                signal=signal
            )
            
            # Determine order side
            order_side = OrderSide.BUY if signal.direction == "LONG" else OrderSide.SELL
            
            # Place order
            order_request = PlaceOrderRequest(
                account_id=account_id,
                symbol=signal.symbol,
                side=order_side,
                order_type=OrderType.MARKET,
                quantity=position_size
            )
            
            order = await self.place_order(order_request, account.user_id)
            
            # Create position record
            position = TradingPosition(
                account_id=account_id,
                signal_id=signal_id,
                symbol=signal.symbol,
                side=PositionSide.LONG if signal.direction == "LONG" else PositionSide.SHORT,
                size=position_size,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit
            )
            
            self.db.add(position)
            self.db.commit()
            self.db.refresh(position)
            
            logger.info(f"Signal executed: {signal_id} -> Position {position.id}")
            return position
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to execute signal"
            )
    
    async def update_positions(self, account_id: int) -> Dict[str, Any]:
        """Update position prices and PnL"""
        try:
            account = self.db.query(TradingAccount).filter(
                TradingAccount.id == account_id
            ).first()
            
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Trading account not found"
                )
            
            # Decrypt API credentials
            api_key = self.cipher.decrypt(account.api_key_encrypted.encode()).decode()
            api_secret = self.cipher.decrypt(account.api_secret_encrypted.encode()).decode()
            passphrase = None
            if account.passphrase_encrypted:
                passphrase = self.cipher.decrypt(account.passphrase_encrypted.encode()).decode()
            
            # Get open positions
            open_positions = self.get_open_positions(account_id)
            
            updated_count = 0
            for position in open_positions:
                try:
                    # Get current price from exchange
                    current_price = await self.exchange_service.get_current_price(
                        exchange=account.exchange,
                        api_key=api_key,
                        api_secret=api_secret,
                        passphrase=passphrase,
                        symbol=position.symbol
                    )
                    
                    if current_price:
                        position.current_price = current_price
                        
                        # Calculate unrealized PnL
                        if position.side == PositionSide.LONG:
                            pnl = (current_price - position.entry_price) * position.size
                        else:
                            pnl = (position.entry_price - current_price) * position.size
                        
                        position.unrealized_pnl = pnl
                        position.unrealized_pnl_percent = (pnl / (position.entry_price * position.size)) * 100
                        
                        updated_count += 1
                        
                except Exception as e:
                    logger.error(f"Error updating position {position.id}: {e}")
            
            self.db.commit()
            
            return {
                "success": True,
                "positions_updated": updated_count,
                "total_positions": len(open_positions)
            }
            
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update positions"
            )
    
    def get_trading_stats(self, account_id: int) -> Dict[str, Any]:
        """Get trading statistics for an account"""
        try:
            # Get all positions for the account
            positions = self.db.query(TradingPosition).filter(
                TradingPosition.account_id == account_id
            ).all()
            
            total_positions = len(positions)
            open_positions = len([p for p in positions if p.is_open])
            closed_positions = total_positions - open_positions
            
            # Calculate PnL
            total_pnl = sum(p.realized_pnl for p in positions if not p.is_open)
            total_pnl += sum(p.unrealized_pnl for p in positions if p.is_open)
            
            # Calculate win rate
            winning_positions = [p for p in positions if not p.is_open and p.realized_pnl > 0]
            win_rate = len(winning_positions) / closed_positions if closed_positions > 0 else 0
            
            # Calculate averages
            avg_win = sum(p.realized_pnl for p in winning_positions) / len(winning_positions) if winning_positions else 0
            losing_positions = [p for p in positions if not p.is_open and p.realized_pnl < 0]
            avg_loss = sum(p.realized_pnl for p in losing_positions) / len(losing_positions) if losing_positions else 0
            
            return {
                "total_positions": total_positions,
                "open_positions": open_positions,
                "closed_positions": closed_positions,
                "total_pnl": total_pnl,
                "win_rate": win_rate,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "winning_trades": len(winning_positions),
                "losing_trades": len(losing_positions)
            }
            
        except Exception as e:
            logger.error(f"Error getting trading stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get trading statistics"
            ) 