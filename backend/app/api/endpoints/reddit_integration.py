"""
Reddit Integration API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

from ...core.database import get_db
from ...models.channel import Channel
from ...models.signal import Signal
from ...services.reddit_service import RedditService
from ...schemas.reddit import (
    RedditSignalCreate, RedditSignalResponse, RedditChannelCreate,
    RedditCollectionRequest, RedditCollectionResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reddit", tags=["reddit"])

@router.post("/collect-signals", response_model=RedditCollectionResponse)
async def collect_reddit_signals(
    request: RedditCollectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Collect signals from Reddit subreddits
    """
    try:
        reddit_service = RedditService(db)
        
        # Run collection in background
        background_tasks.add_task(
            reddit_service.collect_signals_from_subreddits,
            request.subreddits,
            request.limit_per_subreddit,
            request.time_filter
        )
        
        return RedditCollectionResponse(
            success=True,
            message="Reddit signal collection started in background",
            subreddits=request.subreddits,
            status="processing"
        )
        
    except Exception as e:
        logger.error(f"Error triggering Reddit collection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start collection: {str(e)}")

@router.get("/subreddits")
async def get_monitored_subreddits(db: Session = Depends(get_db)):
    """
    Get list of monitored Reddit subreddits
    """
    try:
        reddit_service = RedditService(db)
        subreddits = reddit_service.get_monitored_subreddits()
        
        return {
            "subreddits": subreddits,
            "total": len(subreddits)
        }
        
    except Exception as e:
        logger.error(f"Error getting subreddits: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subreddits")
async def add_subreddit(
    subreddit: RedditChannelCreate,
    db: Session = Depends(get_db)
):
    """
    Add new Reddit subreddit for monitoring
    """
    try:
        reddit_service = RedditService(db)
        result = reddit_service.add_subreddit(subreddit)
        
        return {
            "success": True,
            "subreddit": result,
            "message": f"Added subreddit r/{subreddit.name}"
        }
        
    except Exception as e:
        logger.error(f"Error adding subreddit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals")
async def get_reddit_signals(
    skip: int = 0,
    limit: int = 50,
    subreddit: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get signals collected from Reddit
    """
    try:
        reddit_service = RedditService(db)
        signals = reddit_service.get_signals(skip, limit, subreddit)
        
        return {
            "signals": signals,
            "total": len(signals),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting Reddit signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_reddit_stats(db: Session = Depends(get_db)):
    """
    Get Reddit integration statistics
    """
    try:
        reddit_service = RedditService(db)
        stats = reddit_service.get_statistics()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting Reddit stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
