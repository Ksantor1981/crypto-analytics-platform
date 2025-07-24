"""
Trading API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from app.core.database import get_db
from app.core.auth import get_current_user, require_premium
from app.models.user import User
from app.services.trading_service import TradingService
from app.schemas.trading import (
    TradingAccountCreate, TradingAccountUpdate, TradingAccountResponse,
    TradingPositionResponse, TradingOrderResponse, PlaceOrderRequest,
    ClosePositionRequest, TradingStatsResponse, AccountValidationRequest,
    AccountValidationResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/accounts", response_model=TradingAccountResponse)
async def create_trading_account(
    account_data: TradingAccountCreate,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db)
):
    """Create a new trading account"""
    try:
        trading_service = TradingService(db)
        account = trading_service.create_trading_account(current_user.id, account_data)
        return account
    except Exception as e:
        logger.error(f"Error creating trading account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create trading account"
        )

@router.get("/accounts", response_model=List[TradingAccountResponse])
async def get_trading_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all trading accounts for the current user"""
    try:
        trading_service = TradingService(db)
        accounts = trading_service.get_user_accounts(current_user.id)
        return accounts
    except Exception as e:
        logger.error(f"Error getting trading accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trading accounts"
        )

@router.get("/accounts/{account_id}", response_model=TradingAccountResponse)
async def get_trading_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific trading account"""
    try:
        trading_service = TradingService(db)
        accounts = trading_service.get_user_accounts(current_user.id)
        account = next((acc for acc in accounts if acc.id == account_id), None)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
        
        return account
    except Exception as e:
        logger.error(f"Error getting trading account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trading account"
        )

@router.put("/accounts/{account_id}", response_model=TradingAccountResponse)
async def update_trading_account(
    account_id: int,
    account_data: TradingAccountUpdate,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db)
):
    """Update a trading account"""
    try:
        trading_service = TradingService(db)
        accounts = trading_service.get_user_accounts(current_user.id)
        account = next((acc for acc in accounts if acc.id == account_id), None)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
        
        # Update account fields
        for field, value in account_data.dict(exclude_unset=True).items():
            setattr(account, field, value)
        
        db.commit()
        db.refresh(account)
        
        return account
    except Exception as e:
        logger.error(f"Error updating trading account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update trading account"
        )

@router.delete("/accounts/{account_id}")
async def delete_trading_account(
    account_id: int,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db)
):
    """Delete a trading account"""
    try:
        trading_service = TradingService(db)
        accounts = trading_service.get_user_accounts(current_user.id)
        account = next((acc for acc in accounts if acc.id == account_id), None)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
        
        # Soft delete - mark as inactive
        account.is_active = False
        db.commit()
        
        return {"message": "Trading account deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting trading account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete trading account"
        )

@router.get("/accounts/{account_id}/positions", response_model=List[TradingPositionResponse])
async def get_account_positions(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all positions for a trading account"""
    try:
        trading_service = TradingService(db)
        accounts = trading_service.get_user_accounts(current_user.id)
        account = next((acc for acc in accounts if acc.id == account_id), None)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
        
        positions = trading_service.get_account_positions(account_id)
        return positions
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get positions"
        )

@router.get("/accounts/{account_id}/positions/open", response_model=List[TradingPositionResponse])
async def get_open_positions(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get open positions for a trading account"""
    try:
        trading_service = TradingService(db)
        accounts = trading_service.get_user_accounts(current_user.id)
        account = next((acc for acc in accounts if acc.id == account_id), None)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
        
        positions = trading_service.get_open_positions(account_id)
        return positions
    except Exception as e:
        logger.error(f"Error getting open positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get open positions"
        )

@router.post("/orders", response_model=TradingOrderResponse)
async def place_order(
    order_request: PlaceOrderRequest,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db)
):
    """Place a trading order"""
    try:
        trading_service = TradingService(db)
        order = await trading_service.place_order(order_request, current_user.id)
        return order
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to place order"
        )

@router.post("/positions/close", response_model=TradingOrderResponse)
async def close_position(
    close_request: ClosePositionRequest,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db)
):
    """Close a trading position"""
    try:
        trading_service = TradingService(db)
        order = await trading_service.close_position(close_request, current_user.id)
        return order
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close position"
        )

@router.post("/signals/{signal_id}/execute")
async def execute_signal(
    signal_id: int,
    account_id: int,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db)
):
    """Execute a trading signal"""
    try:
        trading_service = TradingService(db)
        position = await trading_service.execute_signal(signal_id, account_id)
        return {
            "message": "Signal executed successfully",
            "position_id": position.id,
            "symbol": position.symbol,
            "side": position.side,
            "size": position.size,
            "entry_price": position.entry_price
        }
    except Exception as e:
        logger.error(f"Error executing signal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute signal"
        )

@router.post("/accounts/{account_id}/positions/update")
async def update_positions(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update position prices and PnL"""
    try:
        trading_service = TradingService(db)
        accounts = trading_service.get_user_accounts(current_user.id)
        account = next((acc for acc in accounts if acc.id == account_id), None)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
        
        result = await trading_service.update_positions(account_id)
        return result
    except Exception as e:
        logger.error(f"Error updating positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update positions"
        )

@router.get("/accounts/{account_id}/stats", response_model=TradingStatsResponse)
async def get_trading_stats(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trading statistics for an account"""
    try:
        trading_service = TradingService(db)
        accounts = trading_service.get_user_accounts(current_user.id)
        account = next((acc for acc in accounts if acc.id == account_id), None)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
        
        stats = trading_service.get_trading_stats(account_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting trading stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trading statistics"
        )

@router.post("/accounts/validate", response_model=AccountValidationResponse)
async def validate_account(
    validation_request: AccountValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate trading account credentials"""
    try:
        trading_service = TradingService(db)
        accounts = trading_service.get_user_accounts(current_user.id)
        account = next((acc for acc in accounts if acc.id == validation_request.account_id), None)
        
        if not account:
            return AccountValidationResponse(
                is_valid=False,
                error_message="Account not found"
            )
        
        # In a real implementation, you would validate with the exchange
        # For now, we'll simulate validation
        return AccountValidationResponse(
            is_valid=True,
            balance=account.available_balance,
            permissions=["READ", "TRADE", "WITHDRAW"]
        )
    except Exception as e:
        logger.error(f"Error validating account: {e}")
        return AccountValidationResponse(
            is_valid=False,
            error_message="Validation failed"
        )

@router.post("/accounts/{account_id}/sync")
async def sync_account(
    account_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync account data with exchange"""
    try:
        trading_service = TradingService(db)
        accounts = trading_service.get_user_accounts(current_user.id)
        account = next((acc for acc in accounts if acc.id == account_id), None)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
        
        # Add background task to sync account
        background_tasks.add_task(trading_service.update_positions, account_id)
        
        return {"message": "Account sync started"}
    except Exception as e:
        logger.error(f"Error syncing account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync account"
        )

@router.get("/risk/metrics/{account_id}")
async def get_risk_metrics(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get risk metrics for an account"""
    try:
        from app.services.risk_service import RiskService
        
        risk_service = RiskService(db)
        accounts = risk_service.db.query(TradingAccount).filter(
            TradingAccount.user_id == current_user.id,
            TradingAccount.id == account_id
        ).first()
        
        if not accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
        
        metrics = await risk_service.get_risk_metrics(account_id)
        return metrics
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get risk metrics"
        ) 